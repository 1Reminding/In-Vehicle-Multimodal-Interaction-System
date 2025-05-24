import cv2
import mediapipe as mp
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance as dist
from gaze_tracking import GazeTracking
import time

# 初始化 MediaPipe Hands
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75)

# 初始化头部姿态检测
det = dlib.get_frontal_face_detector()
pre = dlib.shape_predictor("head/shape_predictor_68_face_landmarks.dat")
(lS, lE) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rS, rE) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mS, mE) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

# 工具函数
def get_y(hand_landmarks, landmark_enum):
    return hand_landmarks.landmark[landmark_enum].y

def get_x(hand_landmarks, landmark_enum):
    return hand_landmarks.landmark[landmark_enum].x

def head_pose(shape, size):
    """计算头部姿态"""
    model_pts = np.float32([
        (0.0,   0.0,   0.0),      # 鼻尖 30
        (0.0,  -330.0, -65.0),    # 下巴 8
        (-225.0, 170.0, -135.0),  # 左眼角 36
        (225.0, 170.0, -135.0),   # 右眼角 45
        (-150.0, -150.0, -125.0), # 左嘴角 48
        (150.0, -150.0, -125.0)   # 右嘴角 54
    ])

    image_pts = np.float32([
        shape[30],  # 鼻尖
        shape[8],   # 下巴
        shape[36],  # 左眼角
        shape[45],  # 右眼角
        shape[48],  # 左嘴角
        shape[54]   # 右嘴角
    ])

    h, w = size
    focal = w
    center = (w / 2, h / 2)
    camera_mtx = np.array([[focal, 0, center[0]],
                           [0, focal, center[1]],
                           [0, 0, 1]], dtype=np.float32)
    dist_coef = np.zeros((4, 1))

    ok, rvec, tvec = cv2.solvePnP(model_pts, image_pts, camera_mtx,
                                  dist_coef, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return None

    rot_mat, _ = cv2.Rodrigues(rvec)
    pose_mat = cv2.hconcat((rot_mat, tvec))
    _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)
    pitch, yaw, roll = [x[0] for x in euler]  # degree
    return yaw, pitch, roll

def recognize_gesture(hand_landmarks):
    """识别手势"""
    # 关键点枚举
    lm_thumb_tip = mp_hands.HandLandmark.THUMB_TIP
    lm_thumb_ip = mp_hands.HandLandmark.THUMB_IP
    lm_thumb_mcp = mp_hands.HandLandmark.THUMB_MCP
    
    lm_index_tip = mp_hands.HandLandmark.INDEX_FINGER_TIP
    lm_index_pip = mp_hands.HandLandmark.INDEX_FINGER_PIP
    lm_index_mcp = mp_hands.HandLandmark.INDEX_FINGER_MCP
    
    lm_middle_tip = mp_hands.HandLandmark.MIDDLE_FINGER_TIP
    lm_middle_pip = mp_hands.HandLandmark.MIDDLE_FINGER_PIP
    lm_middle_mcp = mp_hands.HandLandmark.MIDDLE_FINGER_MCP
    
    lm_ring_tip = mp_hands.HandLandmark.RING_FINGER_TIP
    lm_ring_pip = mp_hands.HandLandmark.RING_FINGER_PIP
    lm_ring_mcp = mp_hands.HandLandmark.RING_FINGER_MCP
    
    lm_pinky_tip = mp_hands.HandLandmark.PINKY_TIP
    lm_pinky_pip = mp_hands.HandLandmark.PINKY_PIP
    lm_pinky_mcp = mp_hands.HandLandmark.PINKY_MCP

    # 获取各关键点坐标
    thumb_tip_y, thumb_ip_y, thumb_mcp_y = get_y(hand_landmarks, lm_thumb_tip), get_y(hand_landmarks, lm_thumb_ip), get_y(hand_landmarks, lm_thumb_mcp)
    index_tip_y, index_pip_y, index_mcp_y = get_y(hand_landmarks, lm_index_tip), get_y(hand_landmarks, lm_index_pip), get_y(hand_landmarks, lm_index_mcp)
    middle_tip_y, middle_pip_y, middle_mcp_y = get_y(hand_landmarks, lm_middle_tip), get_y(hand_landmarks, lm_middle_pip), get_y(hand_landmarks, lm_middle_mcp)
    ring_tip_y, ring_pip_y, ring_mcp_y = get_y(hand_landmarks, lm_ring_tip), get_y(hand_landmarks, lm_ring_pip), get_y(hand_landmarks, lm_ring_mcp)
    pinky_tip_y, pinky_pip_y, pinky_mcp_y = get_y(hand_landmarks, lm_pinky_tip), get_y(hand_landmarks, lm_pinky_pip), get_y(hand_landmarks, lm_pinky_mcp)

    # 1. 识别"竖起大拇指"
    thumb_points_up = (thumb_tip_y < thumb_ip_y and thumb_ip_y < thumb_mcp_y)
    other_fingers_curled = (index_tip_y > index_pip_y and
                            middle_tip_y > middle_pip_y and
                            ring_tip_y > ring_pip_y and
                            pinky_tip_y > pinky_pip_y)
    thumb_dominant = thumb_tip_y < index_mcp_y 

    if thumb_points_up and other_fingers_curled and thumb_dominant:
        return "竖起大拇指"

    # 2. 识别"摇手"（张开手掌）
    thumb_extended = (thumb_tip_y < thumb_ip_y and thumb_tip_y < thumb_mcp_y)
    index_extended = (index_tip_y < index_pip_y and index_tip_y < index_mcp_y)
    middle_extended = (middle_tip_y < middle_pip_y and middle_tip_y < middle_mcp_y)
    ring_extended = (ring_tip_y < ring_pip_y and ring_tip_y < ring_mcp_y)
    pinky_extended = (pinky_tip_y < pinky_pip_y and pinky_tip_y < pinky_mcp_y)

    if thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended:
        return "摇手"

    # 3. 识别"握拳"
    index_fist_curled = (index_tip_y > index_pip_y and index_tip_y > index_mcp_y)
    middle_fist_curled = (middle_tip_y > middle_pip_y and middle_tip_y > middle_mcp_y)
    ring_fist_curled = (ring_tip_y > ring_pip_y and ring_tip_y > ring_mcp_y)
    pinky_fist_curled = (pinky_tip_y > pinky_pip_y and pinky_tip_y > pinky_mcp_y)
    thumb_fist_curled = (thumb_tip_y > thumb_ip_y and thumb_tip_y > thumb_mcp_y)

    if index_fist_curled and middle_fist_curled and ring_fist_curled and pinky_fist_curled and thumb_fist_curled:
        return "握拳"