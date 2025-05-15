# ASR.py
import whisper
import torch

# 全局加载模型（只加载一次）
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = whisper.load_model("turbo").to(DEVICE)

def transcribe_file(file_path: str) -> str:
    """
    识别指定音频文件，返回转写后的纯文本。
    支持 wav/mp3/flac 等格式，自动使用 GPU（若可用）或 CPU。
    """
    # Whisper 的 transcribe 方法内部会调用 ffmpeg 转码
    result = MODEL.transcribe(file_path, fp16=(DEVICE == "cuda"))
    return result["text"].strip()
