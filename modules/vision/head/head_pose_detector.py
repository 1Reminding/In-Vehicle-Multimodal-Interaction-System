import time
import cv2
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance as dist
import os


class HeadPoseDetector:
    """
    头部姿态检测器（接口不变）：
        - 调用 process_frame(frame)：
            • 校准阶段 → None 或 {'type':'head_pose_calibrated', ...}
            • 检测到动作 → {'type':'head_pose', 'action':'点头'/'摇头', 'ts':...}
            • 其余帧 → None
        - reset() 依旧可重置
    """
    def __init__(self,
                 calib_secs=2,
                 yaw_thresh=10,
                 pitch_delta=6,
                 pitch_frames=1,
                 fps_guess=30):

        # ----------- 配置 -----------
        self.CALIB_SECS = calib_secs
        self.FPS_GUESS = fps_guess
        self.YAW_THRESH = yaw_thresh
        self.PITCH_DELTA = pitch_delta
        self.PITCH_FRAMES = pitch_frames

        # ----------- 校准相关 -----------
        self.pitch_sum = 0.0
        self.sample_cnt = 0
        self.calibrated = False
        self.pitch0 = None            # 基准俯仰角

        # ----------- 状态缓存（一次性动作检测）-----------
        self.yaw_dir = None           # 'L' / 'R', 上一次超过阈值的方向
        self.pitch_down_frames = 0    # 连续低头帧计数

        # ----------- dlib 初始化 -----------
        current_dir = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(current_dir, "models", "shape_predictor_68_face_landmarks.dat")
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"找不到面部特征点预测器: {predictor_path}")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)

        # 眼部特征点索引（眨眼用，虽然目前未使用）
        (self.lS, self.lE) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rS, self.rE) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    # ------------------------------------------------------------------ #
    #                              工具函数                               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def eye_aspect_ratio(eye):
        """计算眨眼比例 EAR"""
        from scipy.spatial import distance as dist
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    @staticmethod
    def _solve_pnp(shape, size):
        """使用 solvePnP 得到 (yaw, pitch, roll)，单位：度"""
        model_pts = np.float32([
            (0.0,   0.0,   0.0),      # 30: nose tip
            (0.0,  -330.0, -65.0),    # 8: chin
            (-225.0, 170.0, -135.0),  # 36: left eye corner
            (225.0, 170.0, -135.0),   # 45: right eye corner
            (-150.0, -150.0, -125.0), # 48: left mouth corner
            (150.0, -150.0, -125.0)   # 54: right mouth corner
        ])
        image_pts = np.float32([shape[i] for i in (30, 8, 36, 45, 48, 54)])

        h, w = size
        focal = w
        center = (w / 2, h / 2)
        camera_mtx = np.array([[focal, 0, center[0]],
                               [0, focal, center[1]],
                               [0, 0, 1]], dtype=np.float32)
        dist_coef = np.zeros((4, 1))

        ok, rvec, tvec = cv2.solvePnP(model_pts, image_pts,
                                      camera_mtx, dist_coef,
                                      flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return None
        rot_mat, _ = cv2.Rodrigues(rvec)
        pose_mat = cv2.hconcat((rot_mat, tvec))
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)
        pitch, yaw, roll = [x[0] for x in euler]
        return yaw, pitch, roll

    # ------------------------------------------------------------------ #
    #                         核心接口：process_frame                      #
    # ------------------------------------------------------------------ #
    def process_frame(self, frame):
        """
        兼容旧接口——一次性动作判定，不做累计计数。

        Returns
        -------
        dict | None
            - 校准完成时：{'type':'head_pose_calibrated', 'pitch0':..., 'ts':...}
            - 检测到动作时：{'type':'head_pose', 'action':'点头'/'摇头', 'ts':...}
            - 其余情况：None
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if not rects:
            return None

        shape = face_utils.shape_to_np(self.predictor(gray, rects[0]))
        pose = self._solve_pnp(shape, frame.shape[:2])
        if pose is None:
            return None
        yaw, pitch, _ = pose

        # ---------------- ① 基线校准 ----------------
        if not self.calibrated:
            self.pitch_sum += pitch
            self.sample_cnt += 1
            if self.sample_cnt >= self.CALIB_SECS * self.FPS_GUESS:
                self.pitch0 = self.pitch_sum / self.sample_cnt
                self.calibrated = True
                return {
                    "type": "head_pose_calibrated",
                    "pitch0": self.pitch0,
                    "ts": time.time()
                }
            # 校准进行中
            return None

        detected_action = None

        # ---------------- ② 摇头检测 ----------------
        if abs(yaw) > self.YAW_THRESH:
            cur_dir = 'L' if yaw > 0 else 'R'
            if self.yaw_dir and cur_dir != self.yaw_dir:
                detected_action = "摇头"
                self.yaw_dir = None  # 复位
            else:
                self.yaw_dir = cur_dir
        else:
            self.yaw_dir = None  # 回到阈值内即清空方向

        # ---------------- ③ 点头检测 ----------------
        if not detected_action:  # 若本帧已判定摇头则优先输出摇头
            if pitch < self.pitch0 - self.PITCH_DELTA:
                self.pitch_down_frames += 1
            else:
                if self.pitch_down_frames >= self.PITCH_FRAMES:
                    detected_action = "点头"
                self.pitch_down_frames = 0  # 无论是否触发都要归零

        # ---------------- ④ 输出 ----------------
        if detected_action:
            return {
                "type": "head_pose",
                "action": detected_action,
                "ts": time.time()
            }
        return None

    # ------------------------------------------------------------------ #
    #                               reset                                 #
    # ------------------------------------------------------------------ #
    def reset(self):
        """重置校准与状态（对外接口不变）"""
        self.pitch_sum = 0.0
        self.sample_cnt = 0
        self.calibrated = False
        self.pitch0 = None
        self.yaw_dir = None
        self.pitch_down_frames = 0
