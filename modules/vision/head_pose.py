import time
import math
import cv2
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance as dist

# ---------------- 工具函数 ----------------
def eye_aspect_ratio(eye):
    """眨眼比例 EAR"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def head_pose(shape, size):
    """
    solvePnP → 返回 (yaw, pitch, roll) in degree.
    yaw>0: 左转，pitch>0: 抬头
    """

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


# ---------------- 主检测 ----------------
def live_detect():
    # ------------- 常量 -------------
    CALIB_SECS   = 2               # 基线采样时长
    FPS_GUESS    = 30
    YAW_THRESH   = 10              # °  |Yaw|>阈值 → 左/右
    PITCH_DELTA  = 6              # ° 低头相对下降角
    PITCH_FRAMES = 1

    # ------------- 计数器 -------------
    pitch_sum = 0
    sample_cnt = 0
    calibrated = False
    pitch0 = None

    yaw_dir = None
    yaw_flag = 0
    tot_shake = 0
    pitch_down_frames = 0
    tot_nod = 0
    prev_state = (-1, -1)  # 只保留摇头和点头状态
    done = False

    # ------------- 模型 -------------
    det = dlib.get_frontal_face_detector()
    pre = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    (lS, lE) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rS, rE) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    # ------------- 摄像头 -------------
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    print("摄像头已打开，按 Q 退出...")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = det(gray, 0)
        if not rects:
            cv2.imshow("Live", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        shape = face_utils.shape_to_np(pre(gray, rects[0]))

        ear_val = (eye_aspect_ratio(shape[lS:lE]) +
                   eye_aspect_ratio(shape[rS:rE])) / 2.0
        pose = head_pose(shape, frame.shape[:2])

        # ---------- 基线校准 ----------
        if not calibrated and pose:
            pitch_sum += pose[1]
            sample_cnt += 1
            if sample_cnt >= CALIB_SECS * FPS_GUESS:
                pitch0 = pitch_sum / sample_cnt
                calibrated = True
                print(f"📏 基线完成：pitch0={pitch0:.1f}°")
            cv2.imshow("Live", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        # ---------------- 摇头 ----------------
        yaw, pitch, _ = pose
        if abs(yaw) > YAW_THRESH:
            cur = 'L' if yaw > 0 else 'R'
            if yaw_dir != cur:
                yaw_flag += 1
                yaw_dir = cur
            if yaw_flag >= 2:
                tot_shake += 1
                yaw_flag = 0

        # ---------------- 点头 ----------------
        if pitch < pitch0 - PITCH_DELTA:
            pitch_down_frames += 1
        else:
            if pitch_down_frames >= PITCH_FRAMES:
                tot_nod += 1
            pitch_down_frames = 0

        # ---------------- 终端输出 ----------------
        state = (tot_shake, tot_nod)  # 只保留摇头和点头计数
        if state != prev_state:
            print(f"Shake={tot_shake}  Nod={tot_nod}", flush=True)
            prev_state = state

        # 在画面下方显示计数
        text = f"Shake={tot_shake}  Nod={tot_nod}"
        cv2.putText(frame, text, (10, 460), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

        cv2.imshow("Live", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    live_detect()
