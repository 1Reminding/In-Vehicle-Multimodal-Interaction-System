# 头部姿态识别系统

这个系统可以通过电脑摄像头实时检测用户的头部姿态，识别点头和摇头动作。系统提供了两个版本：普通版本和优化版本。

## 环境要求

- Python 3.6+
- OpenCV
- NumPy
- PaddleHub
- PaddlePaddle

## 安装步骤

1. 安装PaddlePaddle（如果尚未安装）
   ```
   pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
   ```

2. 安装PaddleHub
   ```
   pip install paddlehub -i https://mirror.baidu.com/pypi/simple
   ```

3. 安装其他依赖
   ```
   pip install opencv-python numpy
   ```

## 文件说明

- `init.py`: 头部姿态识别的核心类实现
- `load.py`: 视频加载模块
- `results.py`: 结果处理模块
- `pose_enhance.py`: 优化版本实现
- `run_head_pose.py`: 运行脚本，可选择普通版本或优化版本

## 使用方法

运行以下命令启动系统：

```
python run_head_pose.py
```

然后根据提示选择要运行的版本：
1. 普通版本 - 使用基本的人脸关键点检测
2. 优化版本 - 使用增强的人脸检测器，提高稳定性

运行后，系统会打开摄像头并开始检测头部姿态。在窗口中可以看到实时的头部姿态信息，包括pitch（俯仰角）、yaw（偏航角）和roll（翻滚角）。

按下'q'键可以退出程序。

## 版本区别

- 普通版本：使用PaddleHub的face_landmark_localization模型直接检测人脸关键点
- 优化版本：使用自定义的人脸检测器（基于ultra_light_fast_generic_face_detector_1mb_640模型），通过加权平均稳定人脸检测框，提高检测稳定性

## 输出说明

系统会在控制台输出检测到的头部动作（点头/摇头），并将处理后的视频保存为MP4文件：
- 普通版本：result.mp4
- 优化版本：result_enhancement.mp4