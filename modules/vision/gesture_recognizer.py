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

mp_hands = mp.solutions.hands


class GestureRecognizer:
    def __init__(
        self,
        camera_id: int = 0,
        max_hands: int = 2,
        det_conf: float = 0.75,
        track_conf: float = 0.75,
    ):
        self.cap = cv2.VideoCapture(camera_id)
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf,
        )

    # ---------- 手势判别核心逻辑（从 hand.py 迁移而来） ----------
    @staticmethod
    def _get_y(landmarks, idx):
        return landmarks.landmark[idx].y

    @staticmethod
    def _get_x(landmarks, idx):
        return landmarks.landmark[idx].x

    def _recognize_gesture(self, hand_landmarks):
        lm = mp_hands.HandLandmark  # 枚举简写
        # 下面保持原手势规则不变；如需增删手势，在此函数改即可
        # 1. 识别“握拳”
        tips = [
            lm.THUMB_TIP,
            lm.INDEX_FINGER_TIP,
            lm.MIDDLE_FINGER_TIP,
            lm.RING_FINGER_TIP,
            lm.PINKY_TIP,
        ]
        pips = [
            lm.THUMB_IP,
            lm.INDEX_FINGER_PIP,
            lm.MIDDLE_FINGER_PIP,
            lm.RING_FINGER_PIP,
            lm.PINKY_PIP,
        ]
        is_fist = all(
            self._get_y(hand_landmarks, t) > self._get_y(hand_landmarks, p)
            for t, p in zip(tips, pips)
        )
        if is_fist:
            return "握拳", 0.95

        # 2. 识别“大拇指朝上”
        thumb_up = (
            self._get_y(hand_landmarks, lm.THUMB_TIP)
            < self._get_y(hand_landmarks, lm.THUMB_IP)
            < self._get_y(hand_landmarks, lm.THUMB_MCP)
        )
        other_curled = all(
            self._get_y(hand_landmarks, t) > self._get_y(hand_landmarks, p)
            for t, p in zip(
                [lm.INDEX_FINGER_TIP, lm.MIDDLE_FINGER_TIP, lm.RING_FINGER_TIP, lm.PINKY_TIP],
                [lm.INDEX_FINGER_PIP, lm.MIDDLE_FINGER_PIP, lm.RING_FINGER_PIP, lm.PINKY_PIP],
            )
        )
        if thumb_up and other_curled:
            return "竖起大拇指", 0.92

        # 3. 更多手势…（保持原 hand.py 规则，可继续扩展）
        return None, 0.0

    # ---------- 外部接口 ----------
    def run(self):
        if not self.cap.isOpened():
            raise RuntimeError("摄像头无法打开")
        try:
            while True:
                ok, frame = self.cap.read()
                if not ok:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = self.hands.process(rgb)
                if res.multi_hand_landmarks:
                    for hlm in res.multi_hand_landmarks:
                        gesture, conf = self._recognize_gesture(hlm)
                        if gesture:
                            yield {
                                "type": "gesture",
                                "gesture": gesture,
                                "conf": conf,
                                "ts": time.time(),
                            }
        finally:
            self.cap.release()
            self.hands.close()
