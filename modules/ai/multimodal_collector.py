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
    intent: str = "unknown"
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
        
        # 数据历史
        self.gaze_history = deque(maxlen=100)
        self.gesture_history = deque(maxlen=50)
        self.speech_history = deque(maxlen=20)
        
        # 回调函数
        self.on_multimodal_ready: Optional[Callable[[MultimodalInput], None]] = None
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 收集状态
        self.collection_start_time = None
        self.is_collecting = False
        
        # 分心状态管理
        self.distraction_detected = False
        self.distraction_start_time = None
        self.waiting_for_confirmation = False
        self.confirmation_timeout = 10.0  # 等待确认的超时时间（秒）
        
        print("✅ 多模态数据收集器初始化完成")
    
    def update_gaze_data(self, gaze_data: Dict[str, Any]):
        """更新眼动数据"""
        with self._lock:
            current_time = time.time()
            state = gaze_data.get("state", "center")
            
            # 检查状态变化
            if (self.current_gaze_state is None or 
                self.current_gaze_state.state != state):
                
                # 结束前一个状态
                if self.current_gaze_state:
                    self.current_gaze_state.duration = current_time - self.current_gaze_state.start_time
                    self.gaze_history.append(self.current_gaze_state)
                
                # 开始新状态
                self.current_gaze_state = GazeState(
                    state=state,
                    start_time=current_time
                )
                
                print(f"👁 眼动状态变化: {state}")
                
                # 检查是否从分心状态恢复
                if state == "center" and self.waiting_for_confirmation:
                    print("✅ 检测到视线回到中心，等待进一步确认...")
            
            # 更新当前状态持续时间
            if self.current_gaze_state:
                self.current_gaze_state.duration = current_time - self.current_gaze_state.start_time
                
                # 判断偏离程度
                if state != "center":
                    if self.current_gaze_state.duration > self.gaze_threshold:
                        self.current_gaze_state.deviation_level = "severe"
                        if not self.distraction_detected:
                            self.distraction_detected = True
                            self.distraction_start_time = current_time
                            print(f"🚨 分心驾驶检测！偏离时间: {self.current_gaze_state.duration:.1f}秒")
                        self._trigger_collection_if_needed()
                    elif self.current_gaze_state.duration > self.gaze_threshold / 2:
                        self.current_gaze_state.deviation_level = "mild"
                else:
                    # 视线回到中心
                    if self.distraction_detected and not self.waiting_for_confirmation:
                        self.waiting_for_confirmation = True
                        print("👁 视线已回到中心，等待用户确认...")
    
    def update_gesture_data(self, gesture_data: Dict[str, Any]):
        """更新手势数据"""
        with self._lock:
            gesture = gesture_data.get("gesture")
            confidence = gesture_data.get("conf", 0.0)
            
            if gesture and confidence > 0.7:  # 置信度阈值
                # 推断手势意图
                intent = self._infer_gesture_intent(gesture)
                
                self.current_gesture_state = GestureState(
                    gesture=gesture,
                    confidence=confidence,
                    intent=intent
                )
                
                self.gesture_history.append(self.current_gesture_state)
                print(f"🖐 手势更新: {gesture} (置信度: {confidence:.2f}, 意图: {intent})")
                
                # 检查是否为确认手势
                if self.waiting_for_confirmation and intent in ["confirm", "ok"]:
                    print("✅ 检测到确认手势，准备恢复正常状态")
                    self._handle_confirmation("gesture")
                
                self._trigger_collection_if_needed()
    
    def update_speech_data(self, speech_data: Dict[str, Any]):
        """更新语音数据"""
        with self._lock:
            text = speech_data.get("text", "").strip()
            
            if text:
                # 推断情感倾向
                emotion = self._infer_emotion(text)
                
                self.current_speech_state = SpeechState(
                    text=text,
                    emotion=emotion
                )
                
                self.speech_history.append(self.current_speech_state)
                print(f"🎤 语音更新: '{text}' , 情感: {emotion})")
                
                # 检查是否为确认语音
                if self.waiting_for_confirmation:
                    if self._is_confirmation_speech(text):
                        print("✅ 检测到确认语音，准备恢复正常状态")
                        self._handle_confirmation("speech")
                
                self._trigger_collection_if_needed()
    
    def _infer_gesture_intent(self, gesture: str) -> str:
        """推断手势意图"""
        gesture_intent_map = {
            "thumbs_up": "confirm",
            "thumbs_down": "reject", 
            "peace": "ok",
            "fist": "stop",
            "open_palm": "attention",
            "pointing": "select"
        }
        return gesture_intent_map.get(gesture, "unknown")
    
    def _infer_emotion(self, text: str) -> str:
        """推断情感倾向（简单规则）"""
        text_lower = text.lower()
        
        # 积极情感关键词
        positive_keywords = ["好", "是", "确定", "同意", "可以", "谢谢"]
        # 消极情感关键词
        negative_keywords = ["不", "没有", "拒绝", "不要", "取消"]
        # 疑问关键词
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
            "好的", "收到", "确定", "是的", "没问题"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in confirmation_keywords)
    
    def _handle_confirmation(self, confirmation_type: str):
        """处理确认事件"""
        print(f"🎉 收到{confirmation_type}确认，分心状态已恢复")
        self.distraction_detected = False
        self.waiting_for_confirmation = False
        self.distraction_start_time = None
        
        # 触发恢复确认的数据收集
        self._trigger_collection_if_needed()
    
    def _trigger_collection_if_needed(self):
        """根据条件触发数据收集"""
        current_time = time.time()
        
        # 检查是否满足收集条件
        should_collect = False
        
        # 条件1: 眼动偏离超过阈值
        if (self.current_gaze_state and 
            self.current_gaze_state.state != "center" and
            self.current_gaze_state.duration >= self.gaze_threshold):
            should_collect = True
            print(f"🚨 触发条件: 眼动偏离 {self.current_gaze_state.duration:.1f}秒")
        
        # 条件2: 有语音输入
        if (self.current_speech_state and 
            current_time - self.current_speech_state.timestamp < 2.0):
            should_collect = True
            print("🚨 触发条件: 语音输入")
        
        # 条件3: 有明确手势意图
        if (self.current_gesture_state and 
            self.current_gesture_state.intent != "unknown" and
            current_time - self.current_gesture_state.timestamp < 3.0):
            should_collect = True
            print("🚨 触发条件: 手势意图")
        
        # 条件4: 等待确认状态下的任何交互
        if self.waiting_for_confirmation:
            should_collect = True
            print("🚨 触发条件: 等待确认状态")
        
        # 条件5: 确认超时
        if (self.waiting_for_confirmation and self.distraction_start_time and
            current_time - self.distraction_start_time > self.confirmation_timeout):
            should_collect = True
            print("🚨 触发条件: 确认超时")
        
        if should_collect and not self.is_collecting:
            self._start_collection()
    
    def _start_collection(self):
        """开始数据收集"""
        self.is_collecting = True
        self.collection_start_time = time.time()
        print("📊 开始多模态数据收集...")
        
        # 延迟收集，给其他模态一些时间
        threading.Timer(1.0, self._complete_collection).start()
    
    def _complete_collection(self):
        """完成数据收集并生成多模态输入"""
        with self._lock:
            if not self.is_collecting:
                return
            
            current_time = time.time()
            collection_duration = current_time - self.collection_start_time
            
            # 构建多模态输入数据
            multimodal_input = MultimodalInput(
                gaze_data=self._get_gaze_data(),
                gesture_data=self._get_gesture_data(),
                speech_data=self._get_speech_data(),
                timestamp=current_time,
                duration=collection_duration
            )
            
            print(f"📋 多模态数据收集完成 (耗时: {collection_duration:.1f}秒)")
            print(f"   - 眼动: {multimodal_input.gaze_data['state']}")
            print(f"   - 手势: {multimodal_input.gesture_data['gesture']}")
            print(f"   - 语音: '{multimodal_input.speech_data['text']}'")
            
            # 重置收集状态
            self.is_collecting = False
            self.collection_start_time = None
            
            # 触发回调
            if self.on_multimodal_ready:
                self.on_multimodal_ready(multimodal_input)
    
    def _get_gaze_data(self) -> Dict[str, Any]:
        """获取眼动数据"""
        if self.current_gaze_state:
            return {
                "state": self.current_gaze_state.state,
                "duration": self.current_gaze_state.duration,
                "deviation": self.current_gaze_state.deviation_level,
                "distraction_detected": self.distraction_detected,
                "waiting_for_confirmation": self.waiting_for_confirmation
            }
        return {
            "state": "center", 
            "duration": 0.0, 
            "deviation": "normal",
            "distraction_detected": self.distraction_detected,
            "waiting_for_confirmation": self.waiting_for_confirmation
        }
    
    def _get_gesture_data(self) -> Dict[str, Any]:
        """获取手势数据"""
        if self.current_gesture_state:
            return {
                "gesture": self.current_gesture_state.gesture,
                "confidence": self.current_gesture_state.confidence,
                "intent": self.current_gesture_state.intent
            }
        return {"gesture": "none", "confidence": 0.0, "intent": "unknown"}
    
    def _get_speech_data(self) -> Dict[str, Any]:
        """获取语音数据"""
        if self.current_speech_state:
            return {
                "text": self.current_speech_state.text,
                "intent": self.current_speech_state.intent,
                "emotion": self.current_speech_state.emotion
            }
        return {"text": "", "intent": "unknown", "emotion": "neutral"}
    
    def set_callback(self, callback: Callable[[MultimodalInput], None]):
        """设置多模态数据就绪回调"""
        self.on_multimodal_ready = callback
        print("✅ 多模态数据回调已设置")
    
    def get_status(self) -> Dict[str, Any]:
        """获取收集器状态"""
        with self._lock:
            return {
                "is_collecting": self.is_collecting,
                "gaze_threshold": self.gaze_threshold,
                "distraction_detected": self.distraction_detected,
                "waiting_for_confirmation": self.waiting_for_confirmation,
                "current_gaze": self._get_gaze_data(),
                "current_gesture": self._get_gesture_data(),
                "current_speech": self._get_speech_data(),
                "history_sizes": {
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
            self.is_collecting = False
            self.collection_start_time = None
            self.distraction_detected = False
            self.waiting_for_confirmation = False
            self.distraction_start_time = None
            print("🔄 多模态收集器已重置")


# 全局多模态收集器实例
multimodal_collector = MultimodalCollector() 