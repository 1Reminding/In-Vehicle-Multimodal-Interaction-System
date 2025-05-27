def handle_action(action: str) -> None:
    """
    接收来自 AI 的操作指令文本，并根据指令类型输出对应的提示。
    支持的指令：
      - "TurnOnAC": 打开空调
      - "PlayMusic": 播放音乐
      - "distract": 司机分心警示
      - "NoticeRoad": 司机注意道路提示
    其他指令会输出未知提示。
    """
    cmd = action.strip()
    if cmd == "TurnOnAC":
        print("🧊 操作：正在打开空调...")
    elif cmd == "PlayMusic":
        print("🎵 操作：正在播放音乐...")
    elif cmd.lower() == "distract":
        print("⚠️ 警示：司机分心，请集中注意力！")
    elif cmd == "NoticeRoad":
        print("✅ 提示：司机已注意道路，继续安全驾驶。")
    else:
        print(f"❓ 未知指令：{action}")
