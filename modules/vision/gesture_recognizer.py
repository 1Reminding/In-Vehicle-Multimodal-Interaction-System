# File: modules/vision/gesture_recognizer.py
"""
基于 MediaPipe‑Hands 的手势识别，将识别结果包装为字典并通过 yield 向外部流式输出。

Usage:
    from modules.vision.gesture_recognizer import GestureRecognizer
    for event in GestureRecognizer(camera_id=0).run():
        print(event)   # {'gesture': '握拳', 'conf': 0.90, 'ts': 1715854812.123}
"""
import time
import cv2
import mediapipe as mp
import numpy as np
import csv
import os
import itertools
import copy

from .keypoint_classifier import KeyPointClassifier

mp_hands = mp.solutions.hands


# Helper functions from hand-keypoint-classification-model-zoo/main.py
# (calc_bounding_rect is not used in the new _recognize_gesture, so omitted)
def calc_landmark_list(image_width, image_height, landmarks):
    landmark_point = []
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point.append([landmark_x, landmark_y])
    return landmark_point

def pre_process_landmark(landmark_list):
    temp_landmark_list = copy.deepcopy(landmark_list)
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]
        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y
    temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))
    max_value = max(list(map(abs, temp_landmark_list)))
    def normalize_(n):
        return n / max_value if max_value != 0 else 0
    temp_landmark_list = list(map(normalize_, temp_landmark_list))
    return temp_landmark_list


class GestureRecognizer:
    def __init__(
        self,
        camera_id: int = 0,
        max_hands: int = 1,
        det_conf: float = 0.7,
        track_conf: float = 0.5,
        model_name: str = 'avazahedi',
    ):
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                 raise RuntimeError(f"摄像头 {camera_id} 无法打开")

        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf,
        )

        # Load KeyPointClassifier
        script_dir = os.path.dirname(__file__)
        model_path = os.path.join(script_dir, 'models', model_name, 'keypoint_classifier.tflite')
        label_path = os.path.join(script_dir, 'models', model_name, 'keypoint_classifier_label.csv')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(label_path):
            raise FileNotFoundError(f"Label file not found: {label_path}")

        self.keypoint_classifier = KeyPointClassifier(model_path=model_path)
        with open(label_path, encoding='utf-8-sig') as f:
            self.keypoint_classifier_labels = [row[0] for row in csv.reader(f)]
        
        self.image_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.image_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


    def _recognize_gesture(self, hand_landmarks):
        landmark_list = calc_landmark_list(self.image_width, self.image_height, hand_landmarks)

        pre_processed_landmark_list = pre_process_landmark(landmark_list)

        gesture_id, confidence = self.keypoint_classifier(pre_processed_landmark_list)
        
        if 0 <= gesture_id < len(self.keypoint_classifier_labels):
            gesture_name = self.keypoint_classifier_labels[gesture_id]
            return gesture_name, confidence
        
        return None, 0.0

    # ---------- 外部接口 ----------
    def run(self):
        if not self.cap.isOpened():
            raise RuntimeError("摄像头无法打开")
        try:
            while True:
                ok, frame = self.cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue
                
                current_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                current_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if self.image_width != current_width or self.image_height != current_height:
                    self.image_width = current_width
                    self.image_height = current_height

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = self.hands.process(rgb)
                rgb.flags.writeable = True

                if res.multi_hand_landmarks:
                    for hlm in res.multi_hand_landmarks: 
                        gesture, conf = self._recognize_gesture(hlm)
                        if gesture:
                            yield {
                                "type": "gesture",
                                "gesture": gesture,
                                "conf": float(conf),
                                "ts": time.time(),
                            }
        finally:
            self.cap.release()
            self.hands.close()
