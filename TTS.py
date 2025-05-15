import threading
import pyttsx3


def speak(text: str):
    """
    每次说话启动独立线程，初始化新引擎进行播报，播报完成后停止引擎。
    """
    print(f"[speak] start speak thread for: {text!r}")
    threading.Thread(target=_speak_once, args=(text,), daemon=True).start()


def _speak_once(text: str):
    """
    在新线程中创建 pyttsx3 引擎，执行播报并停止。
    """
    try:
        engine = pyttsx3.init()
        print(f"[TTS thread] engine.say: {text!r}")
        engine.say(text)
        print(f"[TTS thread] engine.runAndWait")
        engine.runAndWait()
        print(f"[TTS thread] engine.stop")
        engine.stop()
    except Exception as e:
        print(f"[TTS thread] ERROR: {e!r}")