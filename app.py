# 仅演示：语音线程 + 手势线程 → 打印输出
import threading
from modules.audio.recorder import Recorder
from modules.audio.speech_recognizer import transcribe
from modules.audio.intent_classifier import classify
from modules.vision.gesture_recognizer import GestureRecognizer

def audio_worker():
    rec = Recorder()
    for seg in rec.record_stream():
        text = transcribe(seg["wav"])
        res = classify(text)
        if res:
            print("🎤", res)

def gesture_worker():
    for ev in GestureRecognizer().run():
        print("🖐", ev)

if __name__ == "__main__":
    threading.Thread(target=audio_worker, daemon=True).start()
    gesture_worker()   # 主线程跑摄像头，Ctrl‑C 退出
