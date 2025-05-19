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
        
        # 修改角度计算方法
        dx = right_eye.x - left_eye.x
        dy = nose_tip.y - chin.y
        
        # 调整计算方式和缩放因子
        yaw = math.degrees(math.atan2(dx, 0.3)) * 1.5  # 水平方向
        pitch = math.degrees(math.atan2(dy, 0.5)) * 2.0  # 垂直方向
        
        # 限制角度范围
        pitch = max(min(pitch, 45), -45)
        yaw = max(min(yaw, 45), -45)
        
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

                # 在屏幕上显示更详细的调试信息
                cv2.putText(frame, f"Pitch (垂直): {pitch:.1f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Yaw (水平): {yaw:.1f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"垂直阈值: ±30, 水平阈值: ±35", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # 设置更严格的阈值判断
                head_pose = "正常"
                status_color = (0, 255, 0)  # 默认绿色

                # 分别判断垂直和水平方向的动作
                if abs(pitch) > 30:
                    if pitch < -30:
                        head_pose = "点头"
                        status_color = (0, 165, 255)
                    elif pitch > 30:
                        head_pose = "抬头"
                        status_color = (0, 165, 255)
                elif abs(yaw) > 35:
                    head_pose = "摇头"
                    status_color = (0, 0, 255)

                cv2.putText(frame, f"当前状态: {head_pose}", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

                # 打印调试信息到控制台
                print(f" 当前角度 - 垂直: {pitch:.1f}, 水平: {yaw:.1f}, 状态: {head_pose}")

                # 添加状态持续判断
                if 'last_pose' not in locals():
                    last_pose = head_pose
                    last_time = time.time()
                elif head_pose != "正常" and head_pose != last_pose:
                    # 只有在动作持续超过0.5秒才更新状态
                    current_time = time.time()
                    if current_time - last_time > 0.5:
                        print(f" 检测到头部动作: {head_pose}")
                        last_pose = head_pose
                        last_time = current_time
                elif head_pose == "正常" and head_pose != last_pose:
                    # 回到正常状态时立即更新
                    print(f" 恢复正常状态")
                    last_pose = head_pose
                    last_time = time.time()

        else:
            # 当没有检测到人脸时显示提示
            cv2.putText(frame, "未检测到人脸", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 移除频繁的打印输出
        cv2.imshow('Face Pose', frame)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            print(" 收到退出指令")
            break

print(" 释放资源中...")
cap.release()
cv2.destroyAllWindows()
