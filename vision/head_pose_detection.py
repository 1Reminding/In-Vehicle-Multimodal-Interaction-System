import cv2
import numpy as np
import paddlehub as hub
from paddlehub.common.logger import logger
import time
import math
import os

class HeadPoseDetector:
    def __init__(self):
        self.module = hub.Module(name="face_landmark_localization")
        self.cap = cv2.VideoCapture(0)
        
        # 检查摄像头是否成功打开
        if not self.cap.isOpened():
            raise ValueError("无法打开摄像头，请检查摄像头连接")
            
        # 设置摄像头参数
        ret = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        ret &= self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ret &= self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not ret:
            print("警告：摄像头参数设置可能不成功")
        
        # 创建窗口
        cv2.namedWindow('Head Pose Detection', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Head Pose Detection', 640, 480)

    def get_face_landmark(self, image):
        try:
            # 确保图像格式正确
            if image is None:
                print("错误：接收到空图像")
                return False, None
                
            # 转换为uint8类型
            image = np.array(image, dtype=np.uint8)
            
            # 转换图像格式
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
            # 规范化图像尺寸
            image = cv2.resize(image, (640, 480))
            
            res = self.module.keypoint_detection(images=[image], use_gpu=False)
            if not res or not res[0]['data']:
                return False, None
                
            return True, res[0]['data'][0]
            
        except Exception as e:
            print(f"人脸关键点检测失败: {e}")
            return False, None

    def run(self):
        print("开始头部姿态检测，按'q'退出")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("无法获取摄像头画面")
                break

            try:
                # 图像预处理
                frame = cv2.flip(frame, 1)  # 水平翻转，使画面更直观
                
                # 获取人脸关键点
                success, landmarks = self.get_face_landmark(frame)
                
                if success:
                    # 计算欧拉角
                    pitch, yaw = self.calculate_euler_angles(landmarks)
                    
                    # 判断头部动作
                    head_pose = "正常"
                    color = (0, 255, 0)  # 绿色
                    
                    if abs(pitch) > 20:
                        if pitch < -20:
                            head_pose = "点头"
                            color = (0, 165, 255)  # 橙色
                        elif pitch > 20:
                            head_pose = "抬头"
                            color = (0, 165, 255)
                    elif abs(yaw) > 25:
                        head_pose = "摇头"
                        color = (0, 0, 255)  # 红色

                    # 显示信息
                    cv2.putText(frame, f"Pitch (垂直): {pitch:.1f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, f"Yaw (水平): {yaw:.1f}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, f"动作: {head_pose}", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # 绘制人脸关键点
                    for point in landmarks:
                        cv2.circle(frame, (int(point[0]), int(point[1])), 2, (0, 255, 0), -1)

                # 显示画面
                cv2.imshow('Head Pose Detection', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception as e:
                print(f"处理过程出错: {e}")
                continue

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = HeadPoseDetector()
    detector.run()