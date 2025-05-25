import time
import math
import cv2
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance as dist
import os


class HeadPoseDetector:
    def __init__(self, 
                 calib_secs=2, 
                 yaw_thresh=10, 
                 pitch_delta=6, 
                 pitch_frames=1,
                 fps_guess=30):
        """
        初始化头部姿态检测器
        
        Args:
            calib_secs: 基线校准时长（秒）
            yaw_thresh: 摇头阈值（度）
            pitch_delta: 点头相对下降角度（度）
            pitch_frames: 点头检测帧数
            fps_guess: 估计FPS
        """
        self.CALIB_SECS = calib_secs
        self.FPS_GUESS = fps_guess
        self.YAW_THRESH = yaw_thresh
        self.PITCH_DELTA = pitch_delta
        self.PITCH_FRAMES = pitch_frames
        
        # 计数器
        self.pitch_sum = 0
        self.sample_cnt = 0
        self.calibrated = False
        self.pitch0 = None
        
        self.yaw_dir = None
        self.yaw_flag = 0
        self.tot_shake = 0
        self.pitch_down_frames = 0
        self.tot_nod = 0
        self.prev_state = (-1, -1)
        
        # 初始化dlib模型
        script_dir = os.path.dirname(__file__)
        predictor_path = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")
        
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"找不到面部特征点预测器: {predictor_path}")
            
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # 眼部特征点索引
        (self.lS, self.lE) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rS, self.rE) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        
    def eye_aspect_ratio(self, eye):
        """计算眨眼比例 EAR"""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)
    
    def head_pose(self, shape, size):
        """
        使用solvePnP计算头部姿态
        返回 (yaw, pitch, roll) 角度（度）
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
    
    def process_frame(self, frame):
        """
        处理单帧图像，返回检测结果
        
        Args:
            frame: 输入图像帧
            
        Returns:
            dict: 包含头部姿态信息的字典，如果有状态变化则返回，否则返回None
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        
        if not rects:
            return None
            
        shape = face_utils.shape_to_np(self.predictor(gray, rects[0]))
        
        # 计算眼部纵横比（可用于眨眼检测）
        ear_val = (self.eye_aspect_ratio(shape[self.lS:self.lE]) +
                   self.eye_aspect_ratio(shape[self.rS:self.rE])) / 2.0
        
        pose = self.head_pose(shape, frame.shape[:2])
        if not pose:
            return None
            
        # 基线校准
        if not self.calibrated:
            self.pitch_sum += pose[1]
            self.sample_cnt += 1
            if self.sample_cnt >= self.CALIB_SECS * self.FPS_GUESS:
                self.pitch0 = self.pitch_sum / self.sample_cnt
                self.calibrated = True
                return {
                    "type": "head_pose_calibrated",
                    "pitch0": self.pitch0,
                    "ts": time.time()
                }
            return None
            
        # 摇头检测
        yaw, pitch, roll = pose
        detected_action = None
        
        if abs(yaw) > self.YAW_THRESH:
            cur = 'L' if yaw > 0 else 'R'
            if self.yaw_dir != cur:
                self.yaw_flag += 1
                self.yaw_dir = cur
            if self.yaw_flag >= 2:
                self.tot_shake += 1
                self.yaw_flag = 0
                detected_action = "摇头"
                
        # 点头检测
        if pitch < self.pitch0 - self.PITCH_DELTA:
            self.pitch_down_frames += 1
        else:
            if self.pitch_down_frames >= self.PITCH_FRAMES:
                self.tot_nod += 1
                self.pitch_down_frames = 0
                detected_action = "点头"
            
        # 只在检测到动作时返回结果
        if detected_action:
            return {
                "type": "head_pose",
                "action": detected_action,
                "ts": time.time()
            }
            
        return None
    
    def reset(self):
        """重置检测器状态"""
        self.pitch_sum = 0
        self.sample_cnt = 0
        self.calibrated = False
        self.pitch0 = None
        self.yaw_dir = None
        self.yaw_flag = 0
        self.tot_shake = 0
        self.pitch_down_frames = 0
        self.tot_nod = 0
        self.prev_state = (-1, -1) 