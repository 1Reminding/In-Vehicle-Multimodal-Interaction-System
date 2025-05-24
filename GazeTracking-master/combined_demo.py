import cv2
import mediapipe as mp
from gaze_tracking import GazeTracking
import time
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance as dist

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
pre = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
(lS, lE) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rS, rE) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mS, mE) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

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
        
    return None

def main():
    # 初始化眼神追踪器
    gaze = GazeTracking()
    
    # 打开摄像头
    webcam = cv2.VideoCapture(0)
    
    # 初始化状态跟踪变量
    current_state = "center"
    state_start_time = time.time()
    previous_distracted = False
    last_gesture = None
    waiting_for_thumbs_up = False
    is_distracted = False
    mouth_open = False  # 添加嘴部状态跟踪
    
    # 设置分心阈值（秒）
    DISTRACTION_THRESHOLD = {
        "blink": 1.0,
        "left": 3.0,
        "right": 3.0,
    }
    
    # 头部姿态检测相关变量
    CALIB_SECS = 2               # 基线采样时长
    FPS_GUESS = 30
    YAW_THRESH = 10              # °  |Yaw|>阈值 → 左/右
    PITCH_DELTA = 6              # ° 低头相对下降角
    PITCH_FRAMES = 1
    
    # 基线校准相关变量
    ear_sum = pitch_sum = 0
    sample_cnt = 0
    calibrated = False
    ear0 = pitch0 = None
    
    # 头部姿态相关变量
    yaw_dir = None
    yaw_flag = 0
    pitch_down_frames = 0
    last_head_time = time.time()
    
    # 添加计数器
    tot_mouth = 0
    tot_shake = 0
    tot_nod = 0
    prev_state = (-1, -1, -1)  # 用于跟踪状态变化
    last_head_time = time.time()

    while True:
        # 读取摄像头帧
        ret, frame = webcam.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        # 先进行镜面翻转，再处理所有功能
        frame = cv2.flip(frame, 1)

        # 处理眼神追踪
        gaze.refresh(frame)
        frame = gaze.annotated_frame()

        # 处理头部姿态检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = det(gray, 0)
        head_pose_text = "未检测到人脸"
        head_pose_color = (0, 0, 255)
        
        if rects:
            shape = face_utils.shape_to_np(pre(gray, rects[0]))
            pose = head_pose(shape, frame.shape[:2])
            
            if pose:
                yaw, pitch, roll = pose
                
                # 基线校准
                if not calibrated:
                    pitch_sum += pitch
                    sample_cnt += 1
                    if sample_cnt >= CALIB_SECS * FPS_GUESS:
                        pitch0 = pitch_sum / sample_cnt
                        calibrated = True
                        print(f"📏 基线完成：pitch0={pitch0:.1f}°")
                    continue
                
                # 头部姿态检测
                head_pose_status = "正常"
                head_pose_color = (0, 255, 0)
                
                # 摇头检测
                if abs(yaw) > YAW_THRESH:
                    cur = 'L' if yaw > 0 else 'R'
                    if yaw_dir != cur:
                        yaw_flag += 1
                        yaw_dir = cur
                    if yaw_flag >= 2:
                        tot_shake += 1
                        yaw_flag = 0
                        head_pose_status = "摇头"
                        head_pose_color = (0, 0, 255)
                
                # 点头检测
                if pitch < pitch0 - PITCH_DELTA:
                    pitch_down_frames += 1
                else:
                    if pitch_down_frames >= PITCH_FRAMES:
                        tot_nod += 1
                        head_pose_status = "点头"
                        head_pose_color = (0, 165, 255)
                    pitch_down_frames = 0
                
                # 更新状态并打印
                state = (tot_mouth, tot_shake, tot_nod)
                if state != prev_state:
                    print(f"Mouth={tot_mouth}  Shake={tot_shake}  Nod={tot_nod}")
                    prev_state = state
                
                head_pose_text = f"头部姿态: {head_pose_status} (Pitch: {pitch:.1f}, Yaw: {yaw:.1f})"

        # 检测嘴部动作
        if rects:
            shape = face_utils.shape_to_np(pre(gray, rects[0]))
            mouth = shape[mS:mE]
            mar = dist.euclidean(mouth[2], mouth[9]) + dist.euclidean(mouth[4], mouth[7])
            mar = mar / (2.0 * dist.euclidean(mouth[0], mouth[6]))
            
            if mar > 0.5:  # 张嘴阈值
                if not mouth_open:
                    mouth_open = True
                    tot_mouth += 1
                    # 更新状态并打印
                    state = (tot_mouth, tot_shake, tot_nod)
                    if state != prev_state:
                        print(f"Mouth={tot_mouth}  Shake={tot_shake}  Nod={tot_nod}")
                        prev_state = state
            else:
                mouth_open = False

        # 处理手势识别
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        # 眼部追踪状态处理
        new_state = ""
        if gaze.is_blinking():
            new_state = "blink"
        elif gaze.is_right():
            new_state = "right"
        elif gaze.is_left():
            new_state = "left"
        elif gaze.is_center():
            new_state = "center"
            
        if new_state != current_state:
            current_state = new_state
            state_start_time = time.time()
        
        duration = time.time() - state_start_time
        
        # 修改分心状态处理逻辑
        if not is_distracted and current_state in DISTRACTION_THRESHOLD and duration > DISTRACTION_THRESHOLD[current_state]:
            is_distracted = True
            waiting_for_thumbs_up = True
            print(f"警告：检测到分心！当前状态: {current_state}")
            print("请竖起大拇指以确认您已恢复注意力")
        
        # 手势识别处理
        current_gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                current_gesture = recognize_gesture(hand_landmarks)
                # 检查是否是竖起大拇指来解除分心状态
                if waiting_for_thumbs_up and current_gesture == "竖起大拇指":
                    is_distracted = False
                    waiting_for_thumbs_up = False
                    print("已确认注意力恢复，解除分心状态")
                    last_gesture = current_gesture  # 更新上一次的手势状态
                    
        # 只在手势状态发生变化时输出
        if current_gesture != last_gesture:
            if current_gesture:
                print(f"识别到的手势: {current_gesture}")
            elif last_gesture:  # 只有在之前有手势的情况下才提示手势结束
                print("手势结束")
            last_gesture = current_gesture

        # 在画面上显示信息
        gaze_text = f"{current_state} ({duration:.1f}秒)"
        if is_distracted:
            gaze_text += " (分心 - 请竖起大拇指确认恢复注意力)"
        cv2.putText(frame, gaze_text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

        if current_gesture:
            cv2.putText(frame, f"手势: {current_gesture}", (90, 120), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 0), 2)

        # 显示瞳孔位置
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil is not None:
            cv2.putText(frame, f"左瞳孔: {left_pupil}", (90, 180), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
        if right_pupil is not None:
            cv2.putText(frame, f"右瞳孔: {right_pupil}", (90, 220), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
            
        # 显示头部姿态信息
        cv2.putText(frame, head_pose_text, (90, 260), cv2.FONT_HERSHEY_DUPLEX, 0.9, head_pose_color, 1)

        # 在画面下方显示计数
        count_text = f"Mouth={tot_mouth}  Shake={tot_shake}  Nod={tot_nod}"
        cv2.putText(frame, count_text, (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 显示处理后的帧
        cv2.imshow("组合演示", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # 按ESC退出
            break

    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()