# action_handler.py
import threading
import pyttsx3

# 意图／动作 对应 的语音反馈
FEEDBACK_TEXT = {
    "TurnOnAC":        "好的，我将为您打开空调",
    "PlayMusic":       "好的，我将为您播放音乐",
    "AcknowledgeRoad": "好的，已注意道路",
    # 假设手势动作也映射到意图名
    "SwipeUp":         "好的，我将为您调高温度",
    "SwipeDown":       "好的，我将为您调低温度",
    # …以后再加
}

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


def handle_action(intent: str, **kwargs):
    """
    统一的动作反馈入口。
    intent: 动作/意图 名
    kwargs: 可以是 slot, value 等附加信息，若反馈语需要拼接可用到这里
    """
    text = FEEDBACK_TEXT.get(intent)
    if text:
        speak(text)
    # 如果没有配置反馈，就什么也不做
