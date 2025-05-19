# 创建新的 Conda 环境
conda create -n gaze python=3.8 -y

# 激活环境
conda activate gaze

# 安装依赖
pip install opencv-python dlib imutils gaze_tracking

dlib需要cmake和MSVC