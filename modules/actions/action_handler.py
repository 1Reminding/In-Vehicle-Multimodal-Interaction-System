import pyttsx3

tts_engine = pyttsx3.init()
# 可以根据需要调整语速、音量、声音等参数，例如：
# tts_engine.setProperty('rate', 150)   # 语速，默认大约 200
# tts_engine.setProperty('volume', 0.8) # 音量，范围 0.0 ~ 1.0

FEEDBACK_TEXT = {
    "TurnOnAC": "好的，我将为您打开空调",
    "TurnOffAC": "好的，我将为您关闭空调",
    "StopMusic": "好的，我将为您停止音乐",
    "PlayMusic": "好的，我将为您播放音乐",
    "NoticeRoad": "驾驶员已专注，请保持",
    "distract": "请注意安全驾驶，避免分心"
}

def speak_text(text: str) -> None:
    """通过 pyttsx3 播报文字"""
    tts_engine.say(text)
    tts_engine.runAndWait()

def handle_action(action: str) -> None:
    """统一的动作反馈入口：打印并播报"""
    cmd = action.strip()
    text = FEEDBACK_TEXT.get(cmd)
    if text:
        # 打印到控制台
        print(f"[Action] {text}")
        # 语音播报
        speak_text(text)
    else:
        # 如果找不到对应指令，也可以选择提示或者不作处理
        print(f"[Action] 未知指令：{cmd}")
        speak_text("抱歉，未识别您的指令。")

# 示例调用
if __name__ == "__main__":
    handle_action("TurnOnAC")
    handle_action("StopMusic")
    handle_action("distract")
