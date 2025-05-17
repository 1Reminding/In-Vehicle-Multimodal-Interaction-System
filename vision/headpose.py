import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import cv2
import mediapipe as mp
import math
import logging
import time

# 日志控制
logging.getLogger('mediapipe').setLevel(logging.ERROR)
print(" Mediapipe 正常导入")

# 姿态角度估计函数
def calculate_head_pose(landmarks):
    try:
        nose_tip = landmarks[1]
        chin = landmarks[152]
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        
        dx = right_eye.x - left_eye.x
        dy = nose_tip.y - chin.y
        
        yaw = math.degrees(math.atan2(dx, 0.1))
        pitch = math.degrees(math.atan2(dy, 0.1))
        return pitch, yaw
    except Exception as e:
        print(f"❌ 计算姿态时出错: {e}")
        return 0.0, 0.0

# 初始化 mediapipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# 创建窗口
cv2.namedWindow('Face Pose', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Face Pose', 640, 480)

# 打开摄像头
cap = cv2.VideoCapture(0)
time.sleep(1)

if not cap.isOpened():
    print(" 无法打开摄像头")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print(" 摄像头已打开，按 'q' 键退出")

# 初始化 mediapipe 模型
with mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print(" 图像帧读取失败，跳过...")
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        try:
            results = face_mesh.process(rgb_frame)
        except Exception as e:
            print(f" Mediapipe 推理异常：{e}")
            continue

        if results and results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1),
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(80,256,121), thickness=1)
                )

                pitch, yaw = calculate_head_pose(face_landmarks.landmark)

                head_pose = "正常"
                if pitch < -15:
                    head_pose = "点头"
                elif pitch > 15:
                    head_pose = "抬头"
                elif abs(yaw) > 15:
                    head_pose = "摇头"

                # 显示角度和判断
                cv2.putText(frame, f"Pitch: {pitch:.1f}, Yaw: {yaw:.1f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"姿态: {head_pose}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        #  明确输出“准备显示图像”
        print(" 正在显示图像窗口")
        cv2.imshow('Face Pose', frame)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            print(" 收到退出指令")
            break

print(" 释放资源中...")
cap.release()
cv2.destroyAllWindows()
