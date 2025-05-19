import sys
import cv2
import numpy as np
import os

# 检查PaddleHub是否已安装
try:
    import paddlehub as hub
except ImportError:
    print("错误：PaddleHub未安装，请先安装PaddleHub")
    print("安装命令：pip install paddlehub")
    sys.exit(1)

def run_normal_version():
    """运行普通版本的头部姿态识别"""
    print("正在启动普通版本的头部姿态识别...")
    print("按'q'键退出程序")
    
    # 导入必要的模块
    from init import HeadPostEstimation
    
    # 设置视频捕获
    capture = cv2.VideoCapture(0)
    fps = capture.get(cv2.CAP_PROP_FPS)
    size = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    
    # 创建视频写入器
    video_writer = cv2.VideoWriter('result.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    
    def generate_image():
        while True:
            ret, frame_rgb = capture.read()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if frame_rgb is None:
                break
                
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            yield frame_bgr
            
            # 显示实时画面
            cv2.imshow('Head Pose Estimation', frame_rgb)
            
        capture.release()
        video_writer.release()
        cv2.destroyAllWindows()
    
    # 创建头部姿态估计对象并运行
    head_post = HeadPostEstimation()
    for res in head_post.classify_pose_in_euler_angles(video=generate_image, 
                                                      poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION):
        print(list(res.keys()))

def run_enhanced_version():
    """运行优化版本的头部姿态识别"""
    print("正在启动优化版本的头部姿态识别...")
    print("按'q'键退出程序")
    
    # 导入必要的模块
    from init import HeadPostEstimation
    
    # 定义人脸检测器
    class MyFaceDetector(object):
        """自定义人脸检测器
        基于PaddleHub人脸检测模型ultra_light_fast_generic_face_detector_1mb_640，加强稳定人脸检测框
        """
        def __init__(self):
            self.module = hub.Module(name="ultra_light_fast_generic_face_detector_1mb_640")
            self.alpha = 0.75
            self.start_flag = 1

        def face_detection(self, images, use_gpu=False, visualization=False):
            # 使用GPU运行，use_gpu=True，并且在运行整个教程代码之前设置CUDA_VISIBLE_DEVICES环境变量
            result = self.module.face_detection(images=images, use_gpu=use_gpu, visualization=visualization)
            if not result[0]['data']:
                return result

            face = result[0]['data'][0]
            if self.start_flag == 1:
                self.left_s = result[0]['data'][0]['left']
                self.right_s = result[0]['data'][0]['right']
                self.top_s = result[0]['data'][0]['top']
                self.bottom_s = result[0]['data'][0]['bottom']
                self.start_flag = 0
            else:
                # 加权平均上一帧和当前帧人脸检测框位置，以稳定人脸检测框
                self.left_s = self.alpha * self.left_s + (1-self.alpha) * face['left'] 
                self.right_s = self.alpha * self.right_s + (1-self.alpha) * face['right'] 
                self.top_s = self.alpha * self.top_s + (1-self.alpha) * face['top']
                self.bottom_s = self.alpha * self.bottom_s + (1-self.alpha) * face['bottom'] 

            result[0]['data'][0]['left'] = self.left_s
            result[0]['data'][0]['right'] = self.right_s
            result[0]['data'][0]['top'] = self.top_s
            result[0]['data'][0]['bottom'] = self.bottom_s

            return result
    
    # 创建人脸检测器实例
    face_detector = MyFaceDetector()
    
    # 设置视频捕获
    capture = cv2.VideoCapture(0)
    fps = capture.get(cv2.CAP_PROP_FPS)
    size = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    
    # 创建视频写入器
    video_writer = cv2.VideoWriter('result_enhancement.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    
    def generate_image():
        while True:
            ret, frame_rgb = capture.read()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if frame_rgb is None:
                break
                
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            yield frame_bgr
            
            # 显示实时画面
            cv2.imshow('Head Pose Estimation (Enhanced)', frame_rgb)
            
        capture.release()
        video_writer.release()
        cv2.destroyAllWindows()
    
    # 创建头部姿态估计对象并运行
    head_post = HeadPostEstimation(face_detector)
    for res in head_post.classify_pose_in_euler_angles(video=generate_image, 
                                                      poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION):
        print(list(res.keys()))

def main():
    print("=== 头部姿态识别系统 ===")
    print("1. 运行普通版本")
    print("2. 运行优化版本")
    
    choice = input("请选择要运行的版本 (1/2): ")
    
    if choice == '1':
        run_normal_version()
    elif choice == '2':
        run_enhanced_version()
    else:
        print("无效的选择，请输入1或2")

if __name__ == "__main__":
    main()