# 仅演示：语音线程 + 手势线程 + 头部姿态线程 → 打印输出
import time
import cv2
import threading
from modules.audio.recorder import Recorder
from modules.audio.speech_recognizer import transcribe
from modules.audio.intent_classifier import classify
from modules.vision.gesture_recognizer import GestureRecognizer
from modules.vision.head_pose_detector import HeadPoseDetector
from modules.vision.gaze_tracking import GazeTracking


def audio_worker():
    rec = Recorder()
    for seg in rec.record_stream():
        text = transcribe(seg["wav"])
        res = classify(text)
        if res:
            print("🎤", res)


def vision_worker():
    gr = GestureRecognizer()
    hp = HeadPoseDetector()  # 初始化头部姿态检测器
    gaze = GazeTracking()    # 初始化眼神追踪
    
    if not gr.cap.isOpened():
        raise RuntimeError("摄像头无法打开")

    last_gesture = None
    last_conf = 0.0
    # 添加稳定性检测变量
    stable_gesture = None
    stable_start_time = None
    stability_threshold = 0.5  # 半秒稳定时间
    
    # 眼神追踪状态变量
    last_gaze_state = None

    try:
        while True:
            ok, frame = gr.cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # 检查分辨率是否变动
            current_width = int(gr.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            current_height = int(gr.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if gr.image_width != current_width or gr.image_height != current_height:
                gr.image_width = current_width
                gr.image_height = current_height

            frame = cv2.flip(frame, 1)
            
            # 眼神追踪检测
            gaze.refresh(frame)
            current_gaze_state = "center"
            if gaze.is_right():
                current_gaze_state = "right"
            elif gaze.is_left():
                current_gaze_state = "left"
            elif gaze.is_center():
                current_gaze_state = "center"
                
            # 只在状态变化时输出
            if current_gaze_state != last_gaze_state:
                last_gaze_state = current_gaze_state
                print("👁", {
                    "type": "gaze",
                    "state": current_gaze_state,
                    "ts": time.time()
                })
            
            # 头部姿态检测
            head_pose_result = hp.process_frame(frame)
            if head_pose_result:
                if head_pose_result["type"] == "head_pose_calibrated":
                    print("🎯", f"头部姿态基线校准完成: pitch0={head_pose_result['pitch0']:.1f}°")
                elif head_pose_result["type"] == "head_pose":
                    print("🗣", head_pose_result)
            
            # 手势检测
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            res = gr.hands.process(rgb)
            rgb.flags.writeable = True

            current_time = time.time()
            current_gesture = None

            if res.multi_hand_landmarks:
                for hlm in res.multi_hand_landmarks:
                    gesture, conf = gr._recognize_gesture(hlm)
                    if gesture:
                        current_gesture = gesture
                        break  # 只处理第一个检测到的手势

            # 稳定性检测逻辑
            if current_gesture == stable_gesture:
                # 手势保持不变
                if stable_start_time is not None:
                    stable_duration = current_time - stable_start_time
                    if stable_duration >= stability_threshold and current_gesture != last_gesture:
                        # 手势稳定超过阈值且与上次输出不同
                        last_gesture = current_gesture
                        print("🖐", {
                            "type": "gesture",
                            "gesture": current_gesture,
                            "conf": float(conf) if current_gesture else 0.0,
                            "ts": current_time,
                            "stable_duration": stable_duration
                        })
            else:
                # 手势发生变化，重置稳定性计时
                stable_gesture = current_gesture
                stable_start_time = current_time if current_gesture else None

    finally:
        gr.cap.release()
        gr.hands.close()


if __name__ == "__main__":
    threading.Thread(target=audio_worker, daemon=True).start()
    vision_worker()  # 主线程跑摄像头，Ctrl‑C 退出
