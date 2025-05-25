# 🚗 车载多模态智能交互系统 - AI增强版

## 📋 系统概述

本系统集成了DeepSeek API，实现了真正的多模态数据融合和智能决策。系统能够：

- 🎤 **语音识别与意图分类**：实时语音输入处理
- 👁 **眼动追踪**：检测视线偏离，超过3秒触发AI分析
- 🖐 **手势识别**：识别手势并推断意图
- 🤖 **AI智能融合**：使用DeepSeek API进行多模态数据分析
- 🔊 **语音反馈**：AI分析结果通过TTS语音播报

## 🛠 安装依赖

```bash
# 安装OpenAI SDK (用于DeepSeek API)
pip install openai

# 安装语音合成库
pip install pyttsx3

# 其他依赖（如果尚未安装）
pip install opencv-python mediapipe numpy scipy librosa torch transformers
```

## 🚀 快速开始

### 1. 测试DeepSeek API功能

```bash
python test_deepseek_api.py
```

这将运行三个测试场景：
- 🚨 分心驾驶检测
- 🎤 语音命令处理
- 🖐 手势控制确认

### 2. 运行完整的AI多模态系统

```bash
python app_ai_multimodal.py
```

## 📊 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   音频模块      │    │   视觉模块      │    │   AI模块        │
│                 │    │                 │    │                 │
│ • 语音识别      │    │ • 眼动追踪      │    │ • DeepSeek API  │
│ • 意图分类      │    │ • 手势识别      │    │ • 多模态融合    │
│ • 实时录音      │    │ • 头部姿态      │    │ • 智能决策      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ 多模态数据收集器 │
                    │                 │
                    │ • 数据整合      │
                    │ • 触发条件判断  │
                    │ • 状态管理      │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   TTS语音引擎   │
                    │                 │
                    │ • 语音合成      │
                    │ • 优先级队列    │
                    │ • 实时播报      │
                    └─────────────────┘
```

## 🎯 核心功能

### 多模态数据收集

系统会自动收集和整合来自不同模态的数据：

1. **眼动数据**：
   - 状态：left, right, center
   - 持续时间：偏离中心的时长
   - 偏离程度：normal, mild, severe

2. **手势数据**：
   - 手势类型：thumbs_up, peace, fist等
   - 置信度：0.0-1.0
   - 推断意图：confirm, reject, ok等

3. **语音数据**：
   - 识别文本：语音转文字结果
   - 意图分类：navigation, control等
   - 情感倾向：positive, negative, neutral

### AI智能分析

使用DeepSeek API进行多模态数据融合：

```python
# 示例：分心驾驶场景
multimodal_input = MultimodalInput(
    gaze_data={"state": "right", "duration": 4.5, "deviation": "severe"},
    gesture_data={"gesture": "none", "confidence": 0.0, "intent": "unknown"},
    speech_data={"text": "", "intent": "unknown", "emotion": "neutral"},
    timestamp=time.time(),
    duration=4.5
)

# AI分析
ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
```

### 语音反馈

AI分析结果通过TTS引擎进行语音播报：

```python
# 语音播报
tts_engine.speak_normal(ai_response.recommendation_text)
```

## 🔧 配置说明

### DeepSeek API配置

在 `modules/ai/deepseek_client.py` 中配置API密钥：

```python
def __init__(self, api_key: str = "your-api-key-here"):
    self.client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
```

### 触发条件配置

在 `modules/ai/multimodal_collector.py` 中调整触发阈值：

```python
def __init__(self, gaze_threshold: float = 3.0):  # 眼动偏离阈值（秒）
    self.gaze_threshold = gaze_threshold
```

### TTS配置

在 `modules/ai/tts_engine.py` 中调整语音参数：

```python
self.default_config = {
    "rate": 180,        # 语速 (words per minute)
    "volume": 0.8,      # 音量 (0.0-1.0)
    "voice_id": None    # 语音ID (None为默认)
}
```

## 📈 使用场景

### 1. 分心驾驶提醒

**触发条件**：眼动偏离中心超过3秒

**系统响应**：
- 检测到视线偏离
- AI分析驾驶状态
- 语音提醒："请注意道路安全，将视线转回前方"

### 2. 语音命令处理

**触发条件**：检测到语音输入

**示例交互**：
- 用户："导航到家"
- 手势：竖拇指确认
- AI响应："好的，正在为您规划回家路线"

### 3. 手势控制确认

**触发条件**：检测到明确手势意图

**示例交互**：
- 手势：比V手势
- 语音："确定"
- AI响应："收到确认，正在执行操作"

## 🔍 调试与监控

### 系统状态监控

运行时会显示实时统计信息：

```
📊 系统状态 (运行时间: 120.5秒)
   🤖 AI请求次数: 5
   ✅ 成功响应: 5
   🎤 语音输入: 3
   🖐 手势检测: 2
   👁 眼动变化: 15
   📋 收集器状态: 待机
   🔊 TTS状态: 空闲 (队列: 0)
```

### 日志输出

系统会输出详细的处理日志：

```
👁 眼动状态变化: right
🚨 触发条件: 眼动偏离 3.2秒
📊 开始多模态数据收集...
📋 多模态数据收集完成 (耗时: 1.0秒)
🤖 AI分析开始...
🧠 AI分析结果:
   📋 推荐操作: 请注意道路安全，将视线转回前方
   🎯 置信度: 0.95
🔊 语音反馈: 请注意道路安全，将视线转回前方
```

## ⚠️ 注意事项

1. **网络连接**：需要稳定的网络连接访问DeepSeek API
2. **摄像头权限**：确保应用有摄像头访问权限
3. **麦克风权限**：确保应用有麦克风访问权限
4. **API配额**：注意DeepSeek API的使用配额限制
5. **隐私保护**：语音和视频数据仅用于本地处理，不会上传

## 🛡️ 安全特性

- **驾驶安全优先**：AI决策始终以驾驶安全为第一优先级
- **本地数据处理**：敏感数据在本地处理，仅发送分析结果到API
- **容错机制**：API调用失败时提供默认响应
- **优雅关闭**：支持Ctrl+C安全退出

## 🔄 扩展性

系统设计具有良好的扩展性：

1. **新增模态**：可轻松添加新的输入模态（如生理信号）
2. **自定义AI模型**：可替换DeepSeek API为其他AI服务
3. **个性化配置**：支持用户偏好和习惯学习
4. **多语言支持**：可扩展支持多种语言的语音识别和合成

## 📞 技术支持

如有问题或建议，请查看：
- 系统日志输出
- API调用错误信息
- 网络连接状态
- 硬件设备状态

---

**🎉 享受智能的多模态交互体验！** 