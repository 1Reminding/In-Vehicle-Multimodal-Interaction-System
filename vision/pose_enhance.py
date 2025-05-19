class MyFaceDetector(object):
    """
    自定义人脸检测器
    基于PaddleHub人脸检测模型ultra_light_fast_generic_face_detector_1mb_640，加强稳定人脸检测框
    """
    def __init__(self):
        self.module = hub.Module(name="ultra_light_fast_generic_face_detector_1mb_640")
        self.alpha = 0.75
        self.start_flag =1

    def face_detection(self,images, use_gpu=False, visualization=False):
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

            self.start_flag=0
        else:
            # 加权平均上一帧和当前帧人脸检测框位置，以稳定人脸检测框
            self.left_s = self.alpha * self.left_s +  (1-self.alpha) * face['left'] 
            self.right_s = self.alpha * self.right_s +  (1-self.alpha) * face['right'] 
            self.top_s = self.alpha * self.top_s +  (1-self.alpha) * face['top']
            self.bottom_s = self.alpha * self.bottom_s + (1-self.alpha) * face['bottom'] 

        result[0]['data'][0]['left'] = self.left_s
        result[0]['data'][0]['right'] = self.right_s
        result[0]['data'][0]['top'] = self.top_s
        result[0]['data'][0]['bottom'] = self.bottom_s

        return result

# 定义人脸检测器
face_detector = MyFaceDetector()

# 打开摄像头
capture  = cv2.VideoCapture(0) 
# capture  = cv2.VideoCapture('test_sample.mov')  # 注释掉原来的视频文件输入
fps = capture.get(cv2.CAP_PROP_FPS)
size = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
# 将预测结果写成视频
video_writer = cv2.VideoWriter('result_enhancement.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

def generate_image():
    while True:
        # frame_rgb即视频的一帧数据
        ret, frame_rgb = capture.read() 
        # 按q键即可退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if frame_rgb is None:
            break
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        yield frame_bgr
    capture.release()
    video_writer.release()
    cv2.destroyAllWindows()

head_post = HeadPostEstimation(face_detector)
for res in head_post.classify_pose_in_euler_angles(video=generate_image, poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION):
    print(list(res.keys()))