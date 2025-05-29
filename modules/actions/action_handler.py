# 意图／动作 对应 的反馈文本
FEEDBACK_TEXT = {
    "TurnOnAC":        "好的，我将为您打开空调",
    "TurnOffAC":       "好的，我将为您关闭空调",
    "StopMusic":       "好的，我将为您停止音乐",
    "PlayMusic":       "好的，我将为您播放音乐",
    "NoticeRoad":      "驾驶员已专注，请保持",
    "distract":        "请注意安全驾驶，避免分心"  
}

def handle_action(action: str) -> None:
    """
    统一的动作反馈入口。
    action: 动作/意图名称
    """
    cmd = action.strip()
    text = FEEDBACK_TEXT.get(cmd)
    if text:
        print(f"[Action] {text}")
