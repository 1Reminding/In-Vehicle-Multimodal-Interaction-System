# File: modules/audio/intent_classifier.py
"""
Sentence‑Transformer 原型匹配版意图分类。
可直接增删 PROTOTYPES 来支持更多指令。
"""
from sentence_transformers import SentenceTransformer
import numpy as np

# -------- 1. 定义意图原型语句 --------
PROTOTYPES = {
    "TurnOnAC": [
        "打开空调",
        "开空调",
        "帮我开下空调",
        "把空调打开",
    ],
    "PlayMusic": [
        "播放音乐",
        "放首歌",
        "来点音乐",
        "放歌",
    ],
    "AcknowledgeRoad": [
        "已注意道路",
        "知道道路情况",
        "注意道路",
    ],
}

# -------- 2. 预计算嵌入 --------
_EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
_PROTOTYPE_VECS = {
    intent: _EMBED_MODEL.encode(sentences, normalize_embeddings=True)
    for intent, sentences in PROTOTYPES.items()
}


def encode_text(text: str) -> np.ndarray:
    """把用户文本编码成向量并归一化"""
    vec = _EMBED_MODEL.encode([text], normalize_embeddings=True)
    return vec[0]

def classify(
    text: str,
    single_threshold: float = 0.75,
    avg_threshold: float = 0.65
) -> dict | None:
    """
    返回 {"intent": str, "conf": float, "slots": {}} 或 None。
    1) single_threshold: 单条 prototype 匹配阈值
    2) avg_threshold:   平均相似度阈值（回退用）
    """
    if not text:
        return None

    # 先把用户文本编码成向量
    user_vec = encode_text(text)

    # 1. 单条优先：只要有一个 proto vec 的相似度 ≥ single_threshold，立即返回
    for intent, proto_vecs in _PROTOTYPE_VECS.items():
        sims = proto_vecs @ user_vec           # 形状 (K,)
        max_sim = float(np.max(sims))          # 取最高
        if max_sim >= single_threshold:
            return {"intent": intent, "conf": max_sim, "slots": {}}

    # 2. 回退到平均相似度：取最高平均值
    best_intent, best_avg = "Unknown", 0.0
    for intent, proto_vecs in _PROTOTYPE_VECS.items():
        sims = proto_vecs @ user_vec
        avg_sim = float(sims.mean())
        if avg_sim > best_avg:
            best_intent, best_avg = intent, avg_sim

    if best_avg >= avg_threshold:
        return {"intent": best_intent, "conf": best_avg, "slots": {}}

    # 都不满足，则返回 None
    return None
