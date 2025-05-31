from __future__ import division
import os
import cv2
import dlib
from .eye import Eye
from .calibration import Calibration


class GazeTracking(object):
    """
    This class tracks the user's gaze.
    It provides useful information like the position of the eyes
    and pupils and allows to know if the eyes are open or closed
    """

    def __init__(self):
        self.frame = None
        self.eye_left = None
        self.eye_right = None
        self.calibration = Calibration()
        
        # 添加状态维持变量
        self.last_gaze_direction = "center"  # 可能的值: "left", "right", "center"
        
        # 为每个方向维护独立的历史记录
        self.right_gaze_history = []  # 用于存储右视线历史
        self.left_gaze_history = []   # 用于存储左视线历史
        self.center_gaze_history = [] # 用于存储中央视线历史
        self.history_size = 10  # 增加历史记录大小，提高稳定性
        
        # _face_detector is used to detect faces
        self._face_detector = dlib.get_frontal_face_detector()

        # _predictor is used to get facial landmarks of a given face
        cwd = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.abspath(os.path.join(cwd, "trained_models/shape_predictor_68_face_landmarks.dat"))
        self._predictor = dlib.shape_predictor(model_path)

    @property
    def pupils_located(self):
        """Check that the pupils have been located"""
        try:
            int(self.eye_left.pupil.x)
            int(self.eye_left.pupil.y)
            int(self.eye_right.pupil.x)
            int(self.eye_right.pupil.y)
            return True
        except Exception:
            return False

    def _analyze(self):
        """Detects the face and initialize Eye objects"""
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector(frame)

        try:
            landmarks = self._predictor(frame, faces[0])
            self.eye_left = Eye(frame, landmarks, 0, self.calibration)
            self.eye_right = Eye(frame, landmarks, 1, self.calibration)

        except IndexError:
            self.eye_left = None
            self.eye_right = None

    def refresh(self, frame):
        """Refreshes the frame and analyzes it.

        Arguments:
            frame (numpy.ndarray): The frame to analyze
        """
        self.frame = frame
        self._analyze()

    def pupil_left_coords(self):
        """Returns the coordinates of the left pupil"""
        if self.pupils_located:
            x = self.eye_left.origin[0] + self.eye_left.pupil.x
            y = self.eye_left.origin[1] + self.eye_left.pupil.y
            return (x, y)

    def pupil_right_coords(self):
        """Returns the coordinates of the right pupil"""
        if self.pupils_located:
            x = self.eye_right.origin[0] + self.eye_right.pupil.x
            y = self.eye_right.origin[1] + self.eye_right.pupil.y
            return (x, y)

    def horizontal_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        horizontal direction of the gaze. The extreme right is 0.0,
        the center is 0.5 and the extreme left is 1.0
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.x / (self.eye_left.center[0] * 2 - 10)
            pupil_right = self.eye_right.pupil.x / (self.eye_right.center[0] * 2 - 10)
            return (pupil_left + pupil_right) / 2

    def vertical_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        vertical direction of the gaze. The extreme top is 0.0,
        the center is 0.5 and the extreme bottom is 1.0
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.y / (self.eye_left.center[1] * 2 - 10)
            pupil_right = self.eye_right.pupil.y / (self.eye_right.center[1] * 2 - 10)
            return (pupil_left + pupil_right) / 2

    def is_right(self):
        """Returns true if the user is looking to the right"""
        if self.pupils_located:
            # 调整阈值，使其更容易检测到右视线
            is_right_now = self.horizontal_ratio() <= 0.3  # 原来是0.35，放宽一些
            
            # 更新历史记录
            self.right_gaze_history.append(1 if is_right_now else 0)
            if len(self.right_gaze_history) > self.history_size:
                self.right_gaze_history.pop(0)
            
            # 只有当历史记录中大部分都是右视线时，才认为是右视线
            right_ratio = sum(self.right_gaze_history) / len(self.right_gaze_history)
            return right_ratio >= 0.8  # 70%以上帧检测到右视线，提高阈值增加稳定性
    
    def is_left(self):
        """Returns true if the user is looking to the left"""
        if self.pupils_located:
            # 调整阈值，使其更容易检测到左视线
            is_left_now = self.horizontal_ratio() >= 0.7  # 原来是0.65，放宽一些
            
            # 更新历史记录
            self.left_gaze_history.append(1 if is_left_now else 0)
            if len(self.left_gaze_history) > self.history_size:
                self.left_gaze_history.pop(0)
            
            # 只有当历史记录中大部分都是左视线时，才认为是左视线
            left_ratio = sum(self.left_gaze_history) / len(self.left_gaze_history)
            return left_ratio >= 0.8  # 70%以上帧检测到左视线，提高阈值增加稳定性
    
    def is_center(self):
        """Returns true if the user is looking to the center"""
        if self.pupils_located:
            # 直接判断是否在中心区域
            ratio = self.horizontal_ratio()
            is_center_now = (ratio > 0.30 and ratio < 0.70)  # 在左右阈值之间认为是中心
            
            # 更新历史记录
            self.center_gaze_history.append(1 if is_center_now else 0)
            if len(self.center_gaze_history) > self.history_size:
                self.center_gaze_history.pop(0)
            
            # 计算中心视线的比例
            center_ratio = sum(self.center_gaze_history) / len(self.center_gaze_history)
            
            # 如果左右视线都不明显，且中心视线比例足够高，则认为是中心视线
            is_right = self.is_right()
            is_left = self.is_left()
            
            if not is_right and not is_left:
                return center_ratio >= 0.8  # 50%以上帧检测到中心视线
            else:
                return False

    def is_blinking(self):
        """Returns true if the user closes his eyes"""
        if not self.pupils_located:
            # 如果无法定位瞳孔，直接认为是眨眼
            return True
        else:
            # 如果能够定位瞳孔，则根据眨眼比率判断
            blinking_ratio = (self.eye_left.blinking + self.eye_right.blinking) / 2
            return blinking_ratio > 5.2  # 保持原有阈值

    def annotated_frame(self):
        """Returns the main frame with pupils highlighted"""
        frame = self.frame.copy()

        if self.pupils_located:
            color = (0, 255, 0)
            x_left, y_left = self.pupil_left_coords()
            x_right, y_right = self.pupil_right_coords()
            cv2.line(frame, (x_left - 5, y_left), (x_left + 5, y_left), color)
            cv2.line(frame, (x_left, y_left - 5), (x_left, y_left + 5), color)
            cv2.line(frame, (x_right - 5, y_right), (x_right + 5, y_right), color)
            cv2.line(frame, (x_right, y_right - 5), (x_right, y_right + 5), color)

        return frame
