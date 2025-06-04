# 意图／动作 对应 的反馈文本
FEEDBACK_TEXT = {
    "TurnOnAC":        "好的，我将为您打开空调",
    "TurnOffAC":       "好的，我将为您关闭空调",
    "StopMusic":       "好的，我将为您停止音乐",
    "PlayMusic":       "好的，我将为您播放音乐",
    "NoticeRoad":      "驾驶员已专注，请保持",
    "distract":        "请注意安全驾驶，避免分心"  
}

import pyttsx3

_tts_engine = None


def _speak(text: str) -> None:
    """使用离线 TTS 播报文本"""
    if not text:
        return
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 170)
    _tts_engine.say(text)
    _tts_engine.runAndWait()


def handle_action(action: str) -> None:
    """统一的动作反馈入口"""
    cmd = action.strip()
    text = FEEDBACK_TEXT.get(cmd)
    if text:
        print(f"[Action] {text}")
        try:
            _speak(text)
        except Exception as e:
            print(f"语音播报失败: {e}")
