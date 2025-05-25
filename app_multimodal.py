#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态融合交互系统主程序

实现了完整的多模态交互流程：
1. 视觉模态：眼动追踪、手势识别、头部姿态
2. 语音模态：语音识别、意图分类
3. 融合决策：多模态数据融合和冲突解决
4. 系统响应：文本、语音、视觉反馈

典型场景：分心提醒
- 触发：视觉检测到视线偏离
- 融合：等待语音确认("已注意道路")或手势确认(竖拇指)
- 响应：多模态反馈确认用户注意力恢复
"""

import time
import cv2
import threading
import signal
import sys
from typing import Optional

# 导入现有模块
from modules.audio.recorder import Recorder
from modules.audio.speech_recognizer import transcribe
from modules.audio.intent_classifier import classify
from modules.vision.gesture_recognizer import GestureRecognizer
from modules.vision.head_pose_detector import HeadPoseDetector
from modules.vision.gaze_tracking import GazeTracking
from modules.vision.camera_manager import get_camera_manager, release_camera_manager

# 导入融合系统
from modules.fusion import (
    initialize_fusion_system, get_system_status,
    event_bus, state_manager, fusion_engine, scenario_handler,
    ModalityEvent, EventType, ModalityType,
    AudioEvent, VisionEvent, GestureEvent
)


class MultimodalFusionApp:
    """多模态融合应用程序"""
    
    def __init__(self):
        self.running = False
        self.audio_thread = None
        self.vision_thread = None
        
        # 初始化融合系统
        initialize_fusion_system()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("🚀 多模态融合系统启动")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n📡 收到信号 {signum}，正在关闭系统...")
        self.stop()
    
    def start(self):
        """启动系统"""
        self.running = True
        
        # 启动音频处理线程
        self.audio_thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.audio_thread.start()
        
        # 启动视觉处理线程（主线程）
        self._vision_worker()
    
    def stop(self):
        """停止系统"""
        self.running = False
        
        # 释放资源
        release_camera_manager()
        
        # 打印系统统计
        self._print_system_stats()
        
        print("👋 系统已关闭")
        sys.exit(0)
    
    def _audio_worker(self):
        """音频处理工作线程"""
        print("🎤 音频处理线程启动")
        
        try:
            rec = Recorder()
            for seg in rec.record_stream():
                if not self.running:
                    break
                
                # 语音识别
                text = transcribe(seg["wav"])
                if text:
                    # 创建语音识别事件
                    speech_event = AudioEvent(
                        event_type=EventType.SPEECH_RECOGNIZED,
                        data={"text": text, "audio_segment": seg},
                        confidence=0.8  # 可以从识别器获取实际置信度
                    )
                    event_bus.publish(speech_event)
                    
                    # 意图分类
                    intent_result = classify(text)
                    if intent_result:
                        # 创建意图分类事件
                        intent_event = AudioEvent(
                            event_type=EventType.INTENT_CLASSIFIED,
                            data={
                                "text": text,
                                "intent": intent_result.get("intent"),
                                "confidence": intent_result.get("confidence", 0.5)
                            },
                            confidence=intent_result.get("confidence", 0.5)
                        )
                        event_bus.publish(intent_event)
                        
                        print(f"🎤 语音: '{text}' -> {intent_result}")
                
        except Exception as e:
            print(f"❌ 音频处理错误: {e}")
        
        print("🎤 音频处理线程结束")
    
    def _vision_worker(self):
        """视觉处理工作线程"""
        print("👁 视觉处理线程启动")
        
        # 获取摄像头管理器
        camera_manager = get_camera_manager()
        
        # 初始化视觉模块
        gr = GestureRecognizer()
        hp = HeadPoseDetector()
        gaze = GazeTracking()
        
        if not camera_manager.is_opened:
            print("❌ 摄像头无法打开")
            return
        
        # 视觉处理状态
        last_gesture = None
        last_gaze_state = None
        stable_gesture = None
        stable_start_time = None
        stability_threshold = 0.5
        
        try:
            while self.running:
                ok, frame = camera_manager.read_frame()
                if not ok:
                    time.sleep(0.01)
                    continue
                
                # 检查分辨率变化
                current_width = camera_manager.width
                current_height = camera_manager.height
                if gr.image_width != current_width or gr.image_height != current_height:
                    gr.image_width = current_width
                    gr.image_height = current_height
                
                frame = cv2.flip(frame, 1)
                
                # 眼神追踪
                gaze.refresh(frame)
                current_gaze_state = "center"
                if gaze.is_right():
                    current_gaze_state = "right"
                elif gaze.is_left():
                    current_gaze_state = "left"
                elif gaze.is_center():
                    current_gaze_state = "center"
                
                # 只在状态变化时发布事件
                if current_gaze_state != last_gaze_state:
                    last_gaze_state = current_gaze_state
                    
                    gaze_event = VisionEvent(
                        event_type=EventType.GAZE_CHANGED,
                        data={
                            "state": current_gaze_state,
                            "timestamp": time.time()
                        },
                        confidence=0.9
                    )
                    event_bus.publish(gaze_event)
                
                # 头部姿态检测
                head_pose_result = hp.process_frame(frame)
                if head_pose_result:
                    if head_pose_result["type"] == "head_pose":
                        head_pose_event = VisionEvent(
                            event_type=EventType.HEAD_POSE_CHANGED,
                            data=head_pose_result,
                            confidence=0.8
                        )
                        event_bus.publish(head_pose_event)
                
                # 手势识别
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = gr.hands.process(rgb)
                rgb.flags.writeable = True
                
                current_time = time.time()
                current_gesture = None
                gesture_confidence = 0.0
                
                if res.multi_hand_landmarks:
                    for hlm in res.multi_hand_landmarks:
                        gesture, conf = gr._recognize_gesture(hlm)
                        if gesture:
                            current_gesture = gesture
                            gesture_confidence = conf
                            break
                
                # 手势稳定性检测
                if current_gesture == stable_gesture:
                    if stable_start_time is not None:
                        stable_duration = current_time - stable_start_time
                        if stable_duration >= stability_threshold and current_gesture != last_gesture:
                            last_gesture = current_gesture
                            
                            # 发布手势事件
                            gesture_event = GestureEvent(
                                event_type=EventType.GESTURE_DETECTED,
                                data={
                                    "gesture": current_gesture,
                                    "confidence": gesture_confidence,
                                    "stable_duration": stable_duration,
                                    "timestamp": current_time
                                },
                                confidence=gesture_confidence
                            )
                            event_bus.publish(gesture_event)
                else:
                    stable_gesture = current_gesture
                    stable_start_time = current_time if current_gesture else None
                
                # 显示当前状态（可选）
                self._display_status_overlay(frame)
                
                # 显示视频（可选，用于调试）
                if False:  # 设置为True以显示视频窗口
                    cv2.imshow('Multimodal Fusion System', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                time.sleep(0.01)  # 控制帧率
                
        except Exception as e:
            print(f"❌ 视觉处理错误: {e}")
        finally:
            gr.hands.close()
            cv2.destroyAllWindows()
        
        print("👁 视觉处理线程结束")
    
    def _display_status_overlay(self, frame):
        """在视频帧上显示状态信息"""
        # 获取系统状态
        status = get_system_status()
        current_state = status["current_state"]
        active_session = status["active_session"]
        
        # 在帧上绘制状态信息
        y_offset = 30
        cv2.putText(frame, f"State: {current_state}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if active_session:
            y_offset += 30
            scenario = active_session["scenario"]
            duration = active_session["duration"]
            cv2.putText(frame, f"Session: {scenario} ({duration:.1f}s)", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            y_offset += 25
            expected = ", ".join(active_session["expected_modalities"])
            cv2.putText(frame, f"Expected: {expected}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _print_system_stats(self):
        """打印系统统计信息"""
        print("\n📊 系统统计信息:")
        status = get_system_status()
        
        print(f"   当前状态: {status['current_state']}")
        
        session_stats = status['session_stats']
        if session_stats['total_sessions'] > 0:
            print(f"   会话统计: {session_stats['total_sessions']} 总数, "
                  f"{session_stats['completed_sessions']} 完成, "
                  f"成功率 {session_stats['completion_rate']:.1%}")
        
        fusion_stats = status['fusion_stats']
        if fusion_stats['total_fusions'] > 0:
            print(f"   融合统计: {fusion_stats['total_fusions']} 总数, "
                  f"成功率 {fusion_stats['success_rate']:.1%}")
        
        response_stats = status['response_stats']
        if response_stats['total_responses'] > 0:
            print(f"   响应统计: {response_stats['total_responses']} 总数")
        
        print(f"   事件历史: {status['event_history_size']} 条记录")
    
    def demo_distraction_scenario(self):
        """演示分心提醒场景"""
        print("\n🎭 演示分心提醒场景")
        
        # 模拟视线偏离事件
        gaze_event = VisionEvent(
            event_type=EventType.GAZE_CHANGED,
            data={"state": "left", "timestamp": time.time()},
            confidence=0.9
        )
        event_bus.publish(gaze_event)
        
        print("   1. 模拟视线偏离 -> 触发分心检测")
        time.sleep(2)
        
        # 模拟语音确认
        speech_event = AudioEvent(
            event_type=EventType.SPEECH_RECOGNIZED,
            data={"text": "已注意道路"},
            confidence=0.8
        )
        event_bus.publish(speech_event)
        
        intent_event = AudioEvent(
            event_type=EventType.INTENT_CLASSIFIED,
            data={"text": "已注意道路", "intent": "attention_confirm"},
            confidence=0.9
        )
        event_bus.publish(intent_event)
        
        print("   2. 模拟语音确认 -> 融合决策")
        time.sleep(1)
        
        # 模拟手势确认
        gesture_event = GestureEvent(
            event_type=EventType.GESTURE_DETECTED,
            data={"gesture": "thumbs_up", "confidence": 0.8},
            confidence=0.8
        )
        event_bus.publish(gesture_event)
        
        print("   3. 模拟手势确认 -> 完成交互")
        time.sleep(2)
        
        print("✅ 演示完成")


def main():
    """主函数"""
    app = MultimodalFusionApp()
    
    # 可选：运行演示
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("🎭 运行演示模式")
        threading.Timer(3.0, app.demo_distraction_scenario).start()
    
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n⌨️ 用户中断")
    except Exception as e:
        print(f"❌ 系统错误: {e}")
    finally:
        app.stop()


if __name__ == "__main__":
    main() 