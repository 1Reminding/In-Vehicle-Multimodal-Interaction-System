#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态数据收集器模块

负责收集和整合来自不同模态的数据
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque

from modules.ai.deepseek_client import MultimodalInput


@dataclass
class GazeState:
    """眼动状态"""
    state: str  # "left", "right", "center"
    start_time: float
    duration: float = 0.0
    deviation_level: str = "normal"  # "normal", "mild", "severe"


@dataclass
class GestureState:
    """手势状态"""
    gesture: str
    confidence: float
    intent: str = "unknown"
    timestamp: float = field(default_factory=time.time)


@dataclass
class SpeechState:
    """语音状态"""
    text: str
    intent: str = "unknown"  # 将通过 _infer_speech_intent 填充
    emotion: str = "neutral"
    timestamp: float = field(default_factory=time.time)


class MultimodalCollector:
    """多模态数据收集器"""
    
    def __init__(self, gaze_threshold: float = 3.0):
        self.gaze_threshold = gaze_threshold  # 眼动偏离阈值（秒）
        
        # 数据状态
        self.current_gaze_state: Optional[GazeState] = None
        self.current_gesture_state: Optional[GestureState] = None
        self.current_speech_state: Optional[SpeechState] = None
        
        # 数据历史 (可选保留，当前逻辑不强依赖)
        self.gaze_history = deque(maxlen=100)
        self.gesture_history = deque(maxlen=50)
        self.speech_history = deque(maxlen=20)
        
        # 回调函数
        self.on_multimodal_ready: Optional[Callable[[MultimodalInput], None]] = None
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 分心状态管理
        self.distraction_detected = False
        self.distraction_start_time: Optional[float] = None
        
        print("✅ 多模态数据收集器初始化完成 (新版逻辑)")
    
    def update_gaze_data(self, gaze_data: Dict[str, Any]):
        """更新眼动数据"""
        with self._lock:
            current_time = time.time()
            state = gaze_data.get("state", "center")
            
            if (self.current_gaze_state is None or 
                self.current_gaze_state.state != state):
                if self.current_gaze_state:
                    self.current_gaze_state.duration = current_time - self.current_gaze_state.start_time
                    self.gaze_history.append(self.current_gaze_state)
                
                self.current_gaze_state = GazeState(
                    state=state,
                    start_time=current_time
                )
                print(f"👁 眼动状态变化: {state}")

            if self.current_gaze_state:
                self.current_gaze_state.duration = current_time - self.current_gaze_state.start_time
                
                if state != "center":
                    if self.current_gaze_state.duration > self.gaze_threshold:
                        self.current_gaze_state.deviation_level = "severe"
                        if not self.distraction_detected:
                            self.distraction_detected = True
                            self.distraction_start_time = current_time
                            print(f"🚨 分心驾驶检测！偏离时间: {self.current_gaze_state.duration:.1f}秒")
                            context = {
                                "type": "distraction_detected",
                                "gaze_duration": self.current_gaze_state.duration,
                                "reason": "gaze_deviation"
                            }
                            self._prepare_and_send_multimodal_data(context, triggered_by="gaze")
                    elif self.current_gaze_state.duration > self.gaze_threshold / 2:
                        self.current_gaze_state.deviation_level = "mild"
                    else:
                        self.current_gaze_state.deviation_level = "normal"
                else: # state == "center"
                    self.current_gaze_state.deviation_level = "normal"
                    # 视线回到中心，如果之前是分心状态，分心状态依然保持，等待用户语音/手势确认恢复
                    if self.distraction_detected:
                        print("👀 视线已回到中心，但仍处于分心状态。等待用户语音或手势确认恢复注意力。")
    
    def update_gesture_data(self, gesture_data: Dict[str, Any]):
        """更新手势数据"""
        with self._lock:
            gesture = gesture_data.get("gesture")
            confidence = float(gesture_data.get("conf", 0.0))
            
            if gesture and confidence > 0.7:
                intent = self._infer_gesture_intent(gesture)
                self.current_gesture_state = GestureState(
                    gesture=gesture,
                    confidence=confidence,
                    intent=intent,
                    timestamp=time.time()
                )
                self.gesture_history.append(self.current_gesture_state)
                print(f"🖐 手势更新: {gesture} (置信度: {confidence:.2f}, 意图: {intent})")
                
                context_type = "user_input"
                context_info = {"trigger": "gesture", "gesture": gesture, "intent": intent}

                if self.distraction_detected:
                    if self._is_confirmation_gesture(intent):
                        print(f"✅ 通过手势 '{gesture}' 确认，驾驶员已恢复注意力")
                        self.distraction_detected = False
                        self.distraction_start_time = None
                        context_type = "attention_restored"
                        context_info["confirmed_by"] = "gesture"
                    else:
                        print(f"👉 用户在分心状态下输入手势: {gesture}")
                        context_type = "user_input_while_distracted"
                        # context_info["distraction_active"] = True # Already implied by context_type
                
                context_info["type"] = context_type
                self._prepare_and_send_multimodal_data(context_info, triggered_by="gesture")

    def update_speech_data(self, speech_data: Dict[str, Any]):
        """更新语音数据"""
        with self._lock:
            text = speech_data.get("text", "").strip()
            
            if text:
                emotion = self._infer_emotion(text)
                # 简单推断语音意图 (可以根据需要扩展)
                speech_intent = "command" if not self._is_confirmation_speech(text) else "confirmation"

                self.current_speech_state = SpeechState(
                    text=text,
                    emotion=emotion,
                    intent=speech_intent, # 新增意图
                    timestamp=time.time()
                )
                self.speech_history.append(self.current_speech_state)
                print(f"🎤 语音更新: '{text}' (情感: {emotion}, 意图: {speech_intent})")

                context_type = "user_input"
                context_info = {"trigger": "speech", "text": text, "emotion": emotion, "intent": speech_intent}

                if self.distraction_detected:
                    if self._is_confirmation_speech(text):
                        print(f"✅ 通过语音 '{text}' 确认，驾驶员已恢复注意力")
                        self.distraction_detected = False
                        self.distraction_start_time = None
                        context_type = "attention_restored"
                        context_info["confirmed_by"] = "speech"
                    else:
                        print(f"🗣️ 用户在分心状态下输入语音: {text}")
                        context_type = "user_input_while_distracted"
                        # context_info["distraction_active"] = True
                
                context_info["type"] = context_type
                self._prepare_and_send_multimodal_data(context_info, triggered_by="speech")

    def _infer_gesture_intent(self, gesture: str) -> str:
        """推断手势意图"""
        gesture_intent_map = {
            "Thumbs Up": "确认已回到专注状态",
            "Thumbs Down": "仍为分心状态",
            "OK": "确认已回到专注状态", # Considered as confirmation
            "Close": "仍为分心状态", # Example action
            "Open": "播放音乐", # Example action
            "Point": "打开空调" # Example action
        }
        return gesture_intent_map.get(gesture, "unknown")

    def _is_confirmation_gesture(self, intent: str) -> bool:
        """判断是否为确认手势意图"""
        return intent in ["confirm", "ok"]

    def _infer_emotion(self, text: str) -> str:
        """推断情感倾向（简单规则）"""
        text_lower = text.lower()
        positive_keywords = ["好", "是", "确定", "同意", "可以", "谢谢", "棒", "不错"]
        negative_keywords = ["不", "没有", "拒绝", "不要", "取消", "糟糕"]
        question_keywords = ["吗", "呢", "什么", "怎么", "为什么", "?", "？"]
        
        if any(keyword in text_lower for keyword in positive_keywords):
            return "positive"
        elif any(keyword in text_lower for keyword in negative_keywords):
            return "negative"
        elif any(keyword in text_lower for keyword in question_keywords):
            return "questioning"
        else:
            return "neutral"
    
    def _is_confirmation_speech(self, text: str) -> bool:
        """判断是否为确认语音"""
        confirmation_keywords = [
            "已注意", "注意道路", "看路", "专心", "集中", "明白", "知道了", 
            "好的", "收到", "确定", "是的", "没问题", "我已恢复注意力",
            "注意前方", "我在看路", "恢复注意", "明白了", "我会注意",
            "行", "嗯", "ok"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in confirmation_keywords)

    def _prepare_and_send_multimodal_data(self, context_info: Dict[str, Any], triggered_by: Optional[str] = None):
        """准备并发送多模态数据"""
        current_time = time.time()
        
        gaze_d = self._get_gaze_data() # 总是包含眼动数据
        speech_d = {"text": "", "intent": "unknown", "emotion": "neutral"}
        gesture_d = {"gesture": "none", "confidence": 0.0, "intent": "unknown"}

        # 标记数据是否是"新的"或"触发事件的"
        # triggered_by 用来指明是什么直接导致了这个发送事件
        
        if triggered_by == "speech" and self.current_speech_state:
            speech_d = self._get_speech_data(consume=True) # 触发的语音数据，消耗掉
        elif self.current_speech_state and (current_time - self.current_speech_state.timestamp < 1.5): # 最近1.5秒内的语音
            speech_d = self._get_speech_data(consume=False) # 非触发但伴随的语音，不消耗

        if triggered_by == "gesture" and self.current_gesture_state:
            gesture_d = self._get_gesture_data(consume=True) # 触发的手势数据，消耗掉
        elif self.current_gesture_state and (current_time - self.current_gesture_state.timestamp < 2.0): # 最近2秒内的手势
            gesture_d = self._get_gesture_data(consume=False) # 非触发但伴随的手势，不消耗
        
        # 如果是因分心检测触发，且当时有较新的语音/手势，也一并带上
        if triggered_by == "gaze":
            if self.current_speech_state and (current_time - self.current_speech_state.timestamp < 1.5):
                speech_d = self._get_speech_data(consume=False) # 不消耗，因为不是语音主动触发
            if self.current_gesture_state and (current_time - self.current_gesture_state.timestamp < 2.0):
                gesture_d = self._get_gesture_data(consume=False) # 不消耗

        multimodal_input = MultimodalInput(
            gaze_data=gaze_d,
            gesture_data=gesture_d,
            speech_data=speech_d,
            timestamp=current_time,
            duration=0.1,  # 表示瞬时事件
            context=context_info
        )
        
        log_message = (
            f"📋 准备发送多模态数据 (上下文: {context_info.get('type', 'N/A')}):\n"
            f"   - 眼动: {multimodal_input.gaze_data['state']} (持续 {multimodal_input.gaze_data['duration']:.1f}s, "
            f"分心: {'是' if multimodal_input.gaze_data['distraction_detected'] else '否'})\n"
            f"   - 手势: {multimodal_input.gesture_data['gesture']} (意图: {multimodal_input.gesture_data['intent']})\n"
            f"   - 语音: '{multimodal_input.speech_data['text']}' (意图: {multimodal_input.speech_data['intent']})"
        )
        print(log_message)
        
        if self.on_multimodal_ready:
            print(f"🚀 调用多模态数据就绪回调: {self.on_multimodal_ready.__qualname__ if hasattr(self.on_multimodal_ready, '__qualname__') else str(self.on_multimodal_ready)}")
            self.on_multimodal_ready(multimodal_input)
        else:
            print("❌ 错误: 多模态数据就绪回调 (on_multimodal_ready) 未设置!")

    def _get_gaze_data(self) -> Dict[str, Any]:
        """获取当前眼动数据"""
        if self.current_gaze_state:
            return {
                "state": self.current_gaze_state.state,
                "duration": float(self.current_gaze_state.duration),
                "deviation_level": self.current_gaze_state.deviation_level,
                "distraction_detected": self.distraction_detected,
            }
        return {
            "state": "center", 
            "duration": 0.0, 
            "deviation_level": "normal",
            "distraction_detected": self.distraction_detected, # 即使没有当前眼动状态，也要反映整体分心状态
        }
    
    def _get_gesture_data(self, consume: bool = False) -> Dict[str, Any]:
        """获取当前手势数据"""
        data_to_return = {"gesture": "none", "confidence": 0.0, "intent": "unknown"}
        if self.current_gesture_state:
            data_to_return = {
                "gesture": self.current_gesture_state.gesture,
                "confidence": float(self.current_gesture_state.confidence),
                "intent": self.current_gesture_state.intent
            }
            if consume:
                print(f"💨 消耗已发送手势: {self.current_gesture_state.gesture}")
                self.current_gesture_state = None
        return data_to_return
    
    def _get_speech_data(self, consume: bool = False) -> Dict[str, Any]:
        """获取当前语音数据"""
        data_to_return = {"text": "", "intent": "unknown", "emotion": "neutral"}
        if self.current_speech_state:
            data_to_return = {
                "text": self.current_speech_state.text,
                "intent": self.current_speech_state.intent,
                "emotion": self.current_speech_state.emotion
            }
            if consume:
                print(f"💨 消耗已发送语音: '{self.current_speech_state.text}'")
                self.current_speech_state = None
        return data_to_return
    
    def set_callback(self, callback: Callable[[MultimodalInput], None]):
        """设置多模态数据就绪回调"""
        self.on_multimodal_ready = callback
        print(f"✅ 多模态数据回调已设置: {callback.__qualname__ if hasattr(callback, '__qualname__') else str(callback)}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取收集器状态"""
        with self._lock: # 确保线程安全地读取状态
            return {
                "gaze_threshold": self.gaze_threshold,
                "distraction_detected": self.distraction_detected,
                "distraction_start_time": self.distraction_start_time,
                "current_gaze": self._get_gaze_data(), # Use internal getters without consume flag
                "current_gesture": self._get_gesture_data(consume=False),
                "current_speech": self._get_speech_data(consume=False),
                "history_sizes": { # 历史记录大小可能对调试有用
                    "gaze": len(self.gaze_history),
                    "gesture": len(self.gesture_history),
                    "speech": len(self.speech_history)
                }
            }
    
    def reset(self):
        """重置收集器状态"""
        with self._lock:
            self.current_gaze_state = None
            self.current_gesture_state = None
            self.current_speech_state = None
            self.distraction_detected = False
            self.distraction_start_time = None
            # 清空历史记录是可选的，但通常重置意味着从头开始
            self.gaze_history.clear()
            self.gesture_history.clear()
            self.speech_history.clear()
            print("🔄 多模态收集器已重置")


# 全局多模态收集器实例
multimodal_collector = MultimodalCollector() 