import whisper
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
import sounddevice as sd
import webrtcvad
import collections
import wave
import tempfile
from action_handler import handle_action

# ASR
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


# intent_prototypes
# 每个 intent 下是一组典型表达
PROTOTYPE_PHRASES = {
    "TurnOnAC": [
        "开空调", "打开空调", "请帮我打开空调", "开启空调", "开一下空调"
    ],
    "PlayMusic": [
        "播放音乐", "来点音乐", "放首歌", "请播放音乐", "放歌"
    ],
    "AcknowledgeRoad": [
        "已注意道路", "注意道路", "我知道路况"
    ]
}

# 选择一个轻量级模型
EMBED_MODEL = SentenceTransformer("models/all-MiniLM-L6-v2")

# 预计算每个 prototype 的向量，normalize=True 用于余弦相似度
PROTOTYPE_VECS = {
    intent: EMBED_MODEL.encode(phrases, normalize_embeddings=True)
    for intent, phrases in PROTOTYPE_PHRASES.items()
}

def encode_text(text: str) -> np.ndarray:
    """把用户文本编码成向量并归一化"""
    vec = EMBED_MODEL.encode([text], normalize_embeddings=True)
    return vec[0]


def match_intent(text: str,
                 single_threshold: float = 0.75,
                 avg_threshold:    float = 0.65) -> str:
    """
    1) single_threshold: 单条 prototype 匹配阈值
    2) avg_threshold:   平均相似度阈值（回退用）
    """
    user_vec = encode_text(text)

    # 1. 单条优先：只要有一个 proto vec 的相似度 ≥ single_threshold，
    #    就立即返回该 intent
    for intent, proto_vecs in PROTOTYPE_VECS.items():
        # proto_vecs.shape = (K, D)
        sims = np.dot(proto_vecs, user_vec)  # K * 1
        if np.max(sims) >= single_threshold:
            return intent

    # 2. 回退到平均相似度：如果最高平均相似度也够，则返回
    best_intent, best_avg = "Unknown", 0.0
    for intent, proto_vecs in PROTOTYPE_VECS.items():
        sims = proto_vecs @ user_vec
        avg_sim = sims.mean()
        if avg_sim > best_avg:
            best_intent, best_avg = intent, avg_sim

    return best_intent if best_avg >= avg_threshold else "Unknown"


# NLU
def process_audio(file_path: str) -> dict:
    text = transcribe_file(file_path)
    intent = match_intent(text)
    return {
        "text":   text,
        "intent": intent,
        "slots":  {}
    }


# main
RATE = 16000
FRAME_DURATION = 30
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000)
CHANNELS = 1

vad = webrtcvad.Vad(2)

def listen_loop(silence_limit=0.8):
    buffer = collections.deque(maxlen=int(silence_limit * 1000 / FRAME_DURATION))
    voiced_frames = []
    is_recording = False

    with sd.RawInputStream(samplerate=RATE,
                           blocksize=FRAME_SIZE,
                           dtype='int16',
                           channels=CHANNELS) as stream:
        print("→ 已进入同步监听模式，等待指令…")
        while True:
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = bytes(frame)
            is_speech = vad.is_speech(frame_bytes, RATE)

            if is_speech:
                if not is_recording:
                    print("[录音开始]")
                    is_recording = True
                voiced_frames.append(frame_bytes)
                buffer.append(True)
            else:
                buffer.append(False)
                # 只有当已经开始录制，且检测到连续静音时，才触发处理
                if is_recording and not any(buffer):
                    print("[录音结束，开始同步处理]")
                    # 写临时 wav
                    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    with wave.open(tmp.name, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(voiced_frames))

                    # 同步调用 ASR+NLU
                    result = process_audio(tmp.name)
                    text = result["text"]
                    intent = result["intent"]
                    slots = result.get("slots", {})
                    print(f"识别文本：{text}")
                    print(f"意图：{intent}    槽位：{slots}")
                    if intent != "Unknown":
                        handle_action(intent)
                    tmp.close()

                    # 重置状态，回到监听
                    voiced_frames.clear()
                    buffer.clear()
                    is_recording = False
                    print("→ 回到监听状态…")

def main():
    try:
        listen_loop(silence_limit=0.8)
    except KeyboardInterrupt:
        print("退出监听。")

if __name__ == "__main__":
    main()
