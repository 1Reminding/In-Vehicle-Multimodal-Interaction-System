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


def classify(text: str, threshold: float = 0.55) -> dict | None:
    """
    返回 {"intent": str, "conf": float, "slots": {}} 或 None
    conf 是与最相似原型的余弦相似度
    """
    if not text:
        return None
    vec = _EMBED_MODEL.encode([text], normalize_embeddings=True)[0]
    best_intent, best_conf = None, 0.0
    for intent, mat in _PROTOTYPE_VECS.items():
        sims = (mat @ vec).tolist()  # 余弦相似度
        score = max(sims)
        if score > best_conf:
            best_intent, best_conf = intent, score
    if best_conf >= threshold:
        return {"intent": best_intent, "conf": float(best_conf), "slots": {}}
    return None
