import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 抑制 TensorFlow 警告
import cv2
import mediapipe as mp
import logging
logging.getLogger('mediapipe').setLevel(logging.ERROR)  # 抑制 MediaPipe 警告

# 初始化 Mediapipe 模块
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# 打开默认摄像头
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ 无法打开摄像头")
    exit()

# 初始化 FaceMesh（动态模式，持续跟踪）
with mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,  # 启用眼睛/嘴唇/虹膜等细节追踪
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    print("✅ 开始面部检测，按 'q' 键退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ 无法读取帧，尝试重试")
            break

        # 翻转 + 转 RGB
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 获取面部关键点
        results = face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # 绘制面部网格
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=drawing_spec
                )

        # 显示图像
        cv2.imshow("Face Mesh Detection", frame)

        # 按 q 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# 释放资源
cap.release()
cv2.destroyAllWindows()
