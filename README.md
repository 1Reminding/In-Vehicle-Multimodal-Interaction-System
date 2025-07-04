# 车载多模态智能交互系统 (In-Vehicle Multimodal Interaction System)

基于人工智能的车载多模态交互系统，集成了语音识别、手势识别、眼动追踪等多种交互方式，通过 DeepSeek API 实现智能化的多模态融合分析和反馈。

## 🌟 主要特性

- 👁 **眼动追踪**：实时监测驾驶员视线方向，分析注意力分散情况
- 🖐 **手势识别**：支持多种手势命令的识别和响应
- 🎤 **语音交互**：实时语音识别和自然语言处理
- 🗣 **语音播报**：将系统提示内容转换为语音输出
- 🤖 **AI 增强**：基于 DeepSeek API 的多模态数据智能分析
- 📊 **实时反馈**：提供及时的视觉和语音反馈
- 🎯 **智能推荐**：根据多模态输入提供个性化建议
- 👤 **系统管理**：用户配置管理、交互日志记录和权限控制
- 🌤️ **天气集成**：支持实时天气信息查询和显示
- 📈 **数据统计**：提供系统使用统计和性能分析

## 🛠 系统架构

```
├── app.py                     # 主应用程序入口
├── modules/                   # 功能模块
│   ├── audio/                 # 音频处理模块（语音识别、录音等）
│   ├── vision/                # 视觉处理模块（眼动追踪、手势识别等）
│   │   ├── gaze/              # 眼动追踪
│   │   ├── gesture/           # 手势识别
│   │   ├── head/              # 头部姿态检测
│   │   └── camera_manager.py  # 摄像头管理
│   ├── actions/               # 动作处理模块（命令执行、语音反馈等）
│   ├── ai/                    # AI 相关模块（DeepSeek API 集成等）
│   └── system/                # 系统管理模块（用户管理、日志等）
├── ui/                        # 用户界面
│   ├── Main.qml               # 主界面 QML 文件
│   ├── dashboard.py           # 仪表盘组件
│   └── assets/                # UI 资源文件
├── data/                      # 数据文件（运行后生成）
│   ├── logs/                  # 交互日志
│   └── user_configs/          # 用户配置
└── environment.yml            # Conda 环境配置文件
```

## 🎥 系统演示

[https://github.com/user-attachments/assets/5e0ff218-06b5-432e-9c43-fe877d6d1164](https://private-user-images.githubusercontent.com/133238375/452571098-abdc2947-1f28-49f0-a2ad-2d9a82aadf7b.mp4?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDk0NTAwMzksIm5iZiI6MTc0OTQ0OTczOSwicGF0aCI6Ii8xMzMyMzgzNzUvNDUyNTcxMDk4LWFiZGMyOTQ3LTFmMjgtNDlmMC1hMmFkLTJkOWE4MmFhZGY3Yi5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjA5JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYwOVQwNjE1MzlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1kZmIyZDUzNzU4YzQwMDc2OGQ3MGMyNzg3MTE2YjFhM2JiNzc3OWU5NTFiZWExYWU2ZWRiNzE5NGZiNzRiY2MwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.1oEhzXnZPgM9OLxOyLiWLPEStIsbrubrCn_-dzLCgBU)

本演示展示了系统的多模态交互能力：

- 语音控制：通过语音命令"打开空调"来控制车内温度和"关闭音乐"来调节车载音响
- 手势识别：（本演示展示了"open"手势）
  - "open"手势：打开音乐
  - 握拳手势：暂停音乐播放
  - 竖起大拇指：确认当前操作
  - 摇手手势：拒绝/取消当前操作
- 注意力监测：实时监测驾驶员视线，当向左或右连续偏移超过3秒时发出警告
- 手势确认：通过竖起大拇指的手势确认恢复正常状态

## 📋 环境要求

- Python 3.10
- Conda 环境管理工具
- CUDA 支持（推荐，用于深度学习加速）
- 摄像头（用于眼动追踪和手势识别）
- 麦克风（用于语音交互）
- 其他依赖项（见 environment.yml）

## 🚀 快速开始

1. 克隆项目
```bash
git clone https://github.com/1Reminding/In-Vehicle-Multimodal-Interaction-System.git
cd In-Vehicle-Multimodal-Interaction-System
```

2. 创建并激活 Conda 环境
```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate multimodal
```

3. 配置系统
- 确保摄像头和麦克风正常工作
- 系统会自动创建默认用户配置
- 用户配置和日志将保存在 `data` 目录下

4. 运行系统
```bash
python app.py
```

## 💡 使用说明

系统启动后会自动开启以下功能：
- 眼动偏离超过 3 秒自动触发 AI 分析
- 语音输入实时识别并触发分析
- 手势识别自动触发相应操作
- 界面实时显示系统状态和建议
- 自动记录所有交互日志
- 支持多用户切换和管理
- 提供实时天气信息查询

## 🔑 关键功能

1. **多模态数据采集**
   - 实时眼动追踪（基于 OpenCV 和 dlib）
   - 连续语音识别（支持实时转写）
   - 动态手势检测（支持多种手势命令）

2. **AI 智能分析**
   - 多模态数据融合分析
   - 基于上下文的行为理解
   - 智能决策推荐
   - DeepSeek API 集成

3. **交互反馈**
   - 实时视觉反馈（QML 界面）
   - 智能语音提示
   - 个性化建议
   - 系统状态仪表盘

4. **系统管理**
   - **用户配置管理**：支持多用户配置，区分驾驶员和乘客角色
   - **交互日志记录**：自动记录并分析用户交互行为
   - **权限控制**：基于用户角色的功能权限管理
   - **行为分析**：分析用户常用指令和交互习惯
   - **性能监控**：实时监控系统性能和资源使用

## 📝 注意事项

- 首次使用需要进行摄像头校准
- 确保麦克风正常工作
- 保持良好的光照条件以提高识别准确率
- 建议使用支持 CUDA 的显卡以获得更好的性能
- 系统会自动创建默认用户，可以通过界面切换用户
- 所有交互日志都会自动保存在 `data/logs` 目录下
- 用户配置文件保存在 `data/user_configs` 目录下

## 🔐 系统管理功能

### 用户配置管理

系统支持多用户配置，主要特性包括：

- 多用户支持：可创建和管理不同用户的个性化配置
- 角色区分：支持驾驶员、乘客和管理员角色
- 个性化设置：包括交互偏好、常用命令、辅助功能等
- 自动适应：系统会学习用户的交互习惯并进行优化
- 用户切换：支持运行时切换用户，保持会话连续性

### 交互日志记录

系统自动记录所有交互行为，便于分析和优化：

- 详细日志：记录多模态输入、AI响应和系统行为
- 性能统计：追踪系统性能指标和资源使用
- 错误分析：识别和分类系统错误
- 数据导出：支持导出日志用于深度分析
- 实时监控：提供系统状态仪表盘

### 权限管理

基于安全考虑，系统实现了权限控制机制：

- 基于角色：不同角色（驾驶员/乘客）有不同权限
- 驾驶状态感知：根据行驶状态动态调整可用功能
- 安全限制：确保驾驶时只允许安全操作
- 管理员功能：支持系统配置和高级功能
- 会话管理：支持多用户会话的创建和管理
