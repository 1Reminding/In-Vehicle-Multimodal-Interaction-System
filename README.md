下面给出一个**可扩展的项目目录模板**（兼顾已完成的语音 + 手势代码），并解释各目录/文件的职责、典型输入输出，以及接下来需要补全的关键逻辑。可以直接把已有 `hand.py`、`main.py`、`action_handler.py` 迁移/拆分到对应位置，再按需要填充空白模块。

```
yaml复制编辑car_multimodal/
│
├─ app.py                     # 运行入口：加载配置→启动各服务→进入事件循环
│
├─ configs/
│   ├─ settings.yaml          # 系统级参数：模型路径、摄像头ID、阈值、端口等
│   └─ logging.yaml           # 日志等级/格式/滚动策略
│
├─ data/
│   ├─ user_profiles.json     # 驾驶员/乘客个性化指令、权限
│   └─ logs/                  # 多模态事件与系统动作的时间戳化日志
│
├─ modules/                   # **核心业务层**
│   ├─ audio/                 # -------- 语音子系统 --------
│   │   ├─ __init__.py
│   │   ├─ recorder.py        # 麦克风流→帧 (包裹 webrtcvad)
│   │   ├─ speech_recognizer.py
│   │   │   • in : WAV/PCM bytes
│   │   │   • out: 文本串
│   │   └─ intent_classifier.py
│   │       • in : 文本串
│   │       • out: {"intent": str, "slots": dict, "conf": float}
│   │       # 对应现有 whisper+SentenceTransformer 逻辑，可直接搬过来 :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
│   │
│   ├─ vision/                # -------- 视觉子系统 --------
│   │   ├─ __init__.py
│   │   ├─ gesture_recognizer.py   # 封装 hand.py 手势判别并加上置信度 :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
│   │   ├─ gaze_tracker.py         # 眼动/分心检测 (待实现，可用 GazeCapture + openface)
│   │   └─ head_pose.py            # 点头/摇头 (OpenCV solvePnP 简单版即可)
│   │
│   ├─ fusion/                # -------- 多模态决策层 --------
│   │   ├─ __init__.py
│   │   ├─ events.py          # dataclass Event{type, payload, ts, conf, src}
│   │   ├─ rule_fusion.py     # v1: 时序+优先级+多数票融合
│   │   │   • in : 来自 audio/vision 的 Event 流
│   │   │   • out: 高层 Intent / SystemAction
│   │   ├─ ml_fusion.py       # v2: Late‑fusion ML (可选 — 期末前若有余力)
│   │   └─ state_manager.py   # 保存/回溯交互上下文、超时逻辑
│   │
│   ├─ actions/               # -------- 执行动作层 --------
│   │   ├─ __init__.py
│   │   └─ action_handler.py  # 现有的 TTS 反馈等 :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}
│   │
│   └─ utils/
│       ├─ time_sync.py       # 统一时间戳、计算跨线程延迟
│       └─ bus.py             # 简易发布/订阅或 asyncio.Queue 事件总线
│
├─ ui/                        # 可选：仪表盘/调试面板
│   ├─ dashboard.py           # Tkinter/Streamlit/Qt 绘制实时状态
│   └─ assets/
│
├─ tests/
│   ├─ test_audio.py          # 离线语音样例 → intent 断言
│   ├─ test_gesture.py        # 视频帧 → 手势标签
│   ├─ test_fusion.py         # 模拟三模态事件序列 → 最终动作
│   └─ test_end2end.py        # 场景脚本回放 → 符合预期日志
│
├─ docs/                      # 课程要求的文档
│   ├─ requirements.md        # 需求分析
│   ├─ architecture.md        # 系统架构 & 数据流图
│   ├─ modules.md             # 每个子模块说明 (可引用此目录结构)
│   ├─ test_report.md
│   └─ user_manual.md
│
├─ requirements.txt           # 依赖列表
└─ README.md                  # 构建/运行/演示指南
```

------

## 各文件核心要点

| 模块        | 关键文件                | 需补全/关注点                                                | 输入 → 输出                             |
| ----------- | ----------------------- | ------------------------------------------------------------ | --------------------------------------- |
| **audio**   | `recorder.py`           | webrtcvad 阈值、缓冲策略                                     | 麦克风帧 → PCM                          |
|             | `speech_recognizer.py`  | whisper/turbo 的线程池；GPU⇆CPU 切换                         | PCM → 字符串                            |
|             | `intent_classifier.py`  | Prototype 扩充、阈值调优；返回 `conf`                        | 文本 → {intent, slots, conf}            |
| **vision**  | `gesture_recognizer.py` | 把 `hand.py` 封成类；输出置信度                              | BGR frame → {gesture, conf}             |
|             | `gaze_tracker.py`       | 直接使用 dlib/MediaPipe 或简版掩码判断                       | frame → {is_distracted, conf, gaze_dir} |
|             | `head_pose.py`          | 6Dof 头姿态→ nod/shake 分类                                  | frame → {nod, shake, conf}              |
| **fusion**  | `rule_fusion.py`        | **最先实现**： 1. 时间窗对齐（如 1 s） 2. 优先级（安全 > 娱乐） 3. 多数票/置信度加权 | Event[] → FinalIntent                   |
|             | `state_manager.py`      | 保存最近 N 秒事件；处理“等待确认/超时”                       | 交互上下文 → 状态                       |
| **actions** | `action_handler.py`     | 1. 扩充 `FEEDBACK_TEXT` 2. 接入硬件模拟（串口/Socket）       | intent → TTS/模拟动作                   |
| **utils**   | `bus.py`                | 发布订阅、异步队列，降低耦合                                 | Event → Event                           |
| **app.py**  |                         | 解析 YAML 配置→启动线程/协程→注册回调→捕获 Ctrl‑C 优雅退出   | ——                                      |



------

## 建议的多模态融合流程（Rule‑based V1）

1. **事件统一格式**

   ```
   python复制编辑Event(type="gesture", name="ThumbUp",  ts=..., conf=0.92, src="vision")
   Event(type="speech",  name="TurnOnAC", ts=..., conf=0.87, src="audio")
   ```

2. **时间窗对齐**：以 `ts` 为基准，在 Δt=1 s 窗口内收集不同模态事件。

3. **安全优先**：视觉分心告警 > 驾驶相关手势/语音 > 娱乐相关命令。

4. **冲突解决**：

   - 若同一窗内存在“确认”和“拒绝”，取置信度高者。
   - 若语音与手势均为有效指令且不冲突，可并行执行。

5. **输出**：`FinalIntent` 交给 `action_handler`；并写入 `data/logs/yyyymmdd.log`。

**这样即可满足作业的“三模态完整交互流程”要求**；后续若想拿更高分，可在 `ml_fusion.py` 中把多模态特征 (+ 时间信息) 喂给轻量级模型（如 XGBoost）学习决策。

------

## 系统管理功能对接

- **用户个性化配置**：
   `data/user_profiles.json` + 简易 CRUD API；
   `state_manager` 读取当前驾驶员 profile，影响 `rule_fusion`（例如不同阈值、常用指令别名）。
- **权限管理**：
   在 `rule_fusion` 输出前加一层 `permission_checker(role, intent)`，拦截乘客危险操作。
- **交互日志分析**：
   每条 `Event` 和 `FinalIntent` 写入 CSV/JSON；测试工程师可用 notebook 统计误检率。

------

## 下一步怎么做？

1. **已补充的代码**
   -  `modules/vision/gesture_recognizer.py`
   -  `audio/recorder.py` + `speech_recognizer.py` + `intent_classifier.py`。
   - `app.py`简单测试手势和语音**（手势识别准确率较低，语音识别太慢）**
2. **快速打通 Rule Fusion**
   - 在 `app.py` 启动三个线程：语音、手势、视觉分心检测；事件经 `utils.bus.EventBus` 汇聚到 `rule_fusion`.
3. **完成第三模态（视觉分心 + 头姿）**
   - 采用 MediaPipe FaceMesh → 简单阈值即可满足“点头/摇头”识别。
4. **补文档与测试**
   - 先在 `docs/architecture.md` 画出上面模块图；
   - `tests/` 写最小场景用例（CI 可用 pytest）。
