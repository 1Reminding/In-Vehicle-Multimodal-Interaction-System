# action_handler.py

from TTS import speak

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
