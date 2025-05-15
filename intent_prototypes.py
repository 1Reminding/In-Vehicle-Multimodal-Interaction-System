from sentence_transformers import SentenceTransformer
import numpy as np

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
