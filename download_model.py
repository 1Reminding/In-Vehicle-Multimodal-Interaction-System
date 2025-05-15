# download_model.py
from huggingface_hub import snapshot_download

# 把模型快照下载到本地目录 models/all-MiniLM-L6-v2
snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    local_dir="models/all-MiniLM-L6-v2",
    repo_type="model",
    resume_download=True,   # 如果之前中断，可从中断处继续
    max_workers=4          # 并行下载线程数，可调
)
print("模型下载完成！")
