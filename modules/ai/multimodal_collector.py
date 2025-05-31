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
        self.collection_timeout = 5.0  # 收集超时时间（秒）
        
        # 分心状态管理
        self.distraction_detected = False
        self.distraction_start_time = None
        self.waiting_for_confirmation = False
        self.confirmation_timeout = 10.0  # 等待确认的超时时间（秒）
        self._last_confirmation_method = None  # 上次确认的方式
        
        # 启动定期检查收集状态的定时器
        self._start_collection_watchdog()
        
        print("✅ 多模态数据收集器初始化完成")
    
    def _start_collection_watchdog(self):
        """启动收集状态看门狗，定期检查是否卡在收集状态"""
        def check_collection_state():
            with self._lock:
                if (self.is_collecting and self.collection_start_time and 
                    time.time() - self.collection_start_time > self.collection_timeout):
                    # 超时，强制重置收集状态
                    print(f"⚠️ 收集状态超时（已经收集{time.time() - self.collection_start_time:.1f}秒），强制重置")
                    self.is_collecting = False
                    self.collection_start_time = None
            
            # 继续定期检查
            threading.Timer(2.0, check_collection_state).start()
        
        # 启动第一个定时器
        threading.Timer(2.0, check_collection_state).start()
        print("🔄 收集状态监控已启动")
    
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
                
                # 检查是否从分心状态恢复 - 只有在已经检测到分心且视线回到中心时才进入等待确认状态
                if state == "center" and self.distraction_detected and not self.waiting_for_confirmation:
                    self.waiting_for_confirmation = True
                    print("👀 检测到视线回到中心，请通过语音或手势确认您已恢复注意力...")
            
            # 更新当前状态持续时间
            if self.current_gaze_state:
                self.current_gaze_state.duration = current_time - self.current_gaze_state.start_time
                
                # 判断偏离程度
                if state != "center":
                    if self.current_gaze_state.duration > self.gaze_threshold:
                        self.current_gaze_state.deviation_level = "severe"
                        
                        # 第一次检测到分心时立即触发分析
                        if not self.distraction_detected and not self.is_collecting:
                            self.distraction_detected = True
                            self.distraction_start_time = current_time
                            print(f"🚨 分心驾驶检测！偏离时间: {self.current_gaze_state.duration:.1f}秒")
                            print(f"🔍 调试: 眼动状态={state}, 持续时间={self.current_gaze_state.duration:.1f}秒, 是否在收集={self.is_collecting}, 是否检测到分心={self.distraction_detected}")
                            
                            # 立即触发数据收集，无需等待
                            self._immediate_collection()
                        else:
                            # 已经处于分心状态或收集中，打印调试信息
                            print(f"🔍 调试: 眼动状态={state}, 持续时间={self.current_gaze_state.duration:.1f}秒, 是否在收集={self.is_collecting}, 是否检测到分心={self.distraction_detected}")
                    elif self.current_gaze_state.duration > self.gaze_threshold / 2:
                        self.current_gaze_state.deviation_level = "mild"
                        print(f"🔍 调试: 眼动偏离（轻度）: {state}, 持续时间={self.current_gaze_state.duration:.1f}秒")
                else:
                    # 删除这里的重复代码，不需要在这里设置等待确认状态
                    pass
    
    def update_gesture_data(self, gesture_data: Dict[str, Any]):
        """更新手势数据"""
        with self._lock:
            gesture = gesture_data.get("gesture")
            confidence = float(gesture_data.get("conf", 0.0))  # 确保是Python原生float类型
            
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
                
                # 检查是否为确认手势（等待确认状态）
                if self.waiting_for_confirmation and intent in ["confirm", "ok"]:
                    print("✅ 检测到确认手势，驾驶员已恢复注意力")
                    self._handle_confirmation("手势")
                    return
                
                # 正常处理手势，可能触发数据收集
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
                
                # 检查是否为确认语音（等待确认状态）
                if self.waiting_for_confirmation:
                    if self._is_confirmation_speech(text):
                        print("✅ 检测到确认语音，驾驶员已恢复注意力")
                        self._handle_confirmation("语音")
                        return
                
                # 正常处理语音，可能触发数据收集
                self._trigger_collection_if_needed()
    
    def _infer_gesture_intent(self, gesture: str) -> str:
        """推断手势意图"""
        gesture_intent_map = {
            "Thumbs Up": "confirm",
            "Thumbs Down": "reject",
            "OK": "ok",
            "Close": "stop music",
            "Open": "attention",
            "Point": "select"
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
            "好的", "收到", "确定", "是的", "没问题", "我已恢复注意力",
            "注意前方", "我在看路", "恢复注意", "明白了", "我会注意"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in confirmation_keywords)
    
    def _handle_confirmation(self, confirmation_type: str):
        """处理确认事件"""
        print(f"✅ 收到{confirmation_type}确认，分心状态已恢复")
        
        # 保存上次确认方式
        self._last_confirmation_method = confirmation_type
        
        # 重置分心状态
        self.distraction_detected = False
        self.waiting_for_confirmation = False
        self.distraction_start_time = None
        
        # 触发恢复确认的数据收集
        self._immediate_collection()
    
    def _trigger_collection_if_needed(self):
        """根据条件触发数据收集"""
        current_time = time.time()
        
        # 检查是否满足收集条件
        should_collect = False
        
        # 条件1: 眼动偏离超过阈值 (不再通过这里触发，使用_immediate_collection)
        if (self.current_gaze_state and 
            self.current_gaze_state.state != "center" and
            self.current_gaze_state.duration >= self.gaze_threshold and
            not self.distraction_detected):  # 只有未检测到分心时才通过这里触发
            should_collect = True
            print(f"🚨 触发条件: 眼动偏离 {self.current_gaze_state.duration:.1f}秒")
        else:
            if self.current_gaze_state and self.current_gaze_state.state != "center":
                print(f"🔍 调试: 眼动触发条件未满足 - 状态={self.current_gaze_state.state}, 持续时间={self.current_gaze_state.duration:.1f}秒, 阈值={self.gaze_threshold}秒")
        
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
        
        # 条件4: 确认超时 - 当等待确认超时时，再次提醒
        if (self.waiting_for_confirmation and self.distraction_start_time and
            current_time - self.distraction_start_time > self.confirmation_timeout):
            should_collect = True
            print("🚨 触发条件: 确认超时，再次提醒")
            
            # 重置确认超时，避免频繁提醒
            self.distraction_start_time = current_time
        
        if should_collect and not self.is_collecting:
            print("✅ 条件满足，开始收集数据...")
            self._start_collection()
        elif should_collect and self.is_collecting:
            print("⚠️ 条件满足，但已经在收集数据中...")
        elif not should_collect:
            print("❌ 条件不满足，不触发数据收集")
    
    def _start_collection(self):
        """开始数据收集"""
        self.is_collecting = True
        self.collection_start_time = time.time()
        print("📊 开始多模态数据收集...")
        
        # 延迟收集，给其他模态一些时间
        threading.Timer(1.0, self._complete_collection).start()
    
    def _complete_collection(self):
        """完成数据收集并生成多模态输入"""
        try:
            with self._lock:
                if not self.is_collecting:
                    print("⚠️ 收集已被取消或已完成")
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
                    print("🔄 调用多模态数据回调函数...")
                    self.on_multimodal_ready(multimodal_input)
                else:
                    print("❌ 错误: 多模态数据回调函数未设置!")
        except Exception as e:
            # 确保即使发生异常也能重置收集状态
            print(f"❌ 数据收集过程中发生错误: {e}")
            self.is_collecting = False
            self.collection_start_time = None
    
    def _get_gaze_data(self) -> Dict[str, Any]:
        """获取眼动数据"""
        if self.current_gaze_state:
            return {
                "state": self.current_gaze_state.state,
                "duration": float(self.current_gaze_state.duration),  # 确保是Python原生float类型
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
                "confidence": float(self.current_gesture_state.confidence),  # 确保是Python原生float类型
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
        print(f"✅ 多模态数据回调已设置: {callback.__qualname__ if hasattr(callback, '__qualname__') else str(callback)}")
    
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

    def _immediate_collection(self):
        """立即收集当前数据并触发AI分析，用于分心检测的紧急情况"""
        print("📊 立即收集多模态数据（分心检测）...")
        
        # 标记为收集中，避免重复触发
        self.is_collecting = True
        self.collection_start_time = time.time()
        
        # 记录当前是恢复确认还是分心检测
        is_confirmation = not self.distraction_detected and not self.waiting_for_confirmation
        context_type = "attention_restored" if is_confirmation else "distraction_detected"
        
        # 立即构建多模态输入数据
        multimodal_input = MultimodalInput(
            gaze_data=self._get_gaze_data(),
            gesture_data=self._get_gesture_data(),
            speech_data=self._get_speech_data(),
            timestamp=time.time(),
            duration=0.1,  # 几乎立即完成
            context={
                "type": context_type,
                "previous_distraction": not is_confirmation,
                "confirmed_by": self._last_confirmation_method if is_confirmation else None
            }
        )
        
        print(f"📋 多模态数据紧急收集完成")
        print(f"   - 眼动: {multimodal_input.gaze_data['state']} ({multimodal_input.gaze_data['duration']:.1f}秒)")
        print(f"   - 手势: {multimodal_input.gesture_data['gesture']}")
        print(f"   - 语音: '{multimodal_input.speech_data['text']}'")
        print(f"   - 上下文: {context_type}" + (" (已通过确认恢复注意力)" if is_confirmation else ""))
        
        # 重置收集状态
        self.is_collecting = False
        self.collection_start_time = None
        
        # 触发回调
        if self.on_multimodal_ready:
            print("🔄 调用多模态数据回调函数...")
            self.on_multimodal_ready(multimodal_input)
        else:
            print("❌ 错误: 多模态数据回调函数未设置!")


# 全局多模态收集器实例
multimodal_collector = MultimodalCollector() 