import pyttsx3
from typing import Optional, Any, Union

tts_engine = pyttsx3.init()
# tts_engine.setProperty('rate', 150)   # 语速示例
# tts_engine.setProperty('volume', 0.8) # 音量示例

FEEDBACK_TEXT = {
    "TurnOnAC": "好的，我将为您打开空调",
    "TurnOffAC": "好的，我将为您关闭空调",
    "StopMusic": "好的，我将为您停止音乐",
    "PlayMusic": "好的，我将为您播放音乐",
    "NoticeRoad": "驾驶员已专注，请保持",
    "distract": "请注意安全驾驶，避免分心"
}


def speak_text(text: str, app: Optional[Any] = None) -> None:
    """通过 pyttsx3 播报文字；播报期间暂停录音"""
    if app is not None:
        app.pause_recording()  # 暂停 Recorder
    tts_engine.say(text)
    tts_engine.runAndWait()
    if app is not None:
        app.resume_recording()  # 恢复 Recorder


def handle_action(action: Union[str, dict], app: Optional[Any] = None) -> None:
    """
    统一动作反馈入口：
      - 字符串：直接视为指令，如 "TurnOnAC"
      - 字典：尝试取常见字段或第一个键
    """
    # -------- 把 action 转成字符串 cmd --------
    if isinstance(action, dict):
        # ① DeepSeek 常用格式 {"command":"TurnOnAC"} → 取 value
        if "command" in action:
            cmd = str(action["command"])
        # ② 也可能直接是 {"TurnOnAC":1} → 取第一个键
        else:
            cmd = str(next(iter(action.keys())))
    else:
        cmd = str(action).strip()

    # -------- 原有逻辑保持不变 --------
    text = FEEDBACK_TEXT.get(cmd)
    if text:
        print(f"[Action] {text}")
        speak_text(text, app)
    else:
        print(f"[Action] 未知指令：{cmd}")
        speak_text("抱歉，未识别您的指令。", app)
