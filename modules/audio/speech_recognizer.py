# File: modules/audio/speech_recognizer.py
"""
Whisper‑turbo 封装；输入 WAV bytes → 输出文本字符串
"""
import os

import whisper
import torch
import tempfile
import io

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = whisper.load_model("turbo").to(_DEVICE)


def transcribe(wav_bytes: bytes, language: str = "zh") -> str:
    """
    修改后：在 Windows 上写入临时文件并关闭，避免 ffmpeg 无法打开的 PermissionError。
    """
    # 1. 创建一个可被外部进程读取的临时文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        fp.write(wav_bytes)
        fp.flush()
        temp_path = fp.name

    try:
        # 2. 调用 Whisper，ffmpeg 这时可以打开 temp_path
        res = _MODEL.transcribe(
            temp_path,
            language=language,
            fp16=_DEVICE.startswith("cuda"),
            word_timestamps=False,
            verbose=False,
        )
        return res["text"].strip()
    finally:
        # 3. 清理临时文件
        try:
            os.remove(temp_path)
        except OSError:
            pass
