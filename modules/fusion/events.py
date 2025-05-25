from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from enum import Enum
import time


class ModalityType(Enum):
    """模态类型枚举"""
    AUDIO = "audio"
    VISION = "vision"
    GESTURE = "gesture"
    GAZE = "gaze"
    HEAD_POSE = "head_pose"


class EventType(Enum):
    """事件类型枚举"""
    # 语音事件
    SPEECH_RECOGNIZED = "speech_recognized"
    INTENT_CLASSIFIED = "intent_classified"
    
    # 视觉事件
    GESTURE_DETECTED = "gesture_detected"
    GAZE_CHANGED = "gaze_changed"
    HEAD_POSE_CHANGED = "head_pose_changed"
    
    # 融合事件
    DISTRACTION_DETECTED = "distraction_detected"
    ATTENTION_CONFIRMED = "attention_confirmed"
    INTERACTION_COMPLETED = "interaction_completed"
    
    # 系统事件
    SCENARIO_STARTED = "scenario_started"
    SCENARIO_ENDED = "scenario_ended"


@dataclass
class ModalityEvent:
    """多模态事件基类"""
    event_type: EventType
    modality: ModalityType
    timestamp: float
    confidence: float
    data: Dict[str, Any]
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class AudioEvent(ModalityEvent):
    """语音事件"""
    def __init__(self, event_type: EventType, data: Dict[str, Any], 
                 confidence: float = 1.0, session_id: Optional[str] = None):
        super().__init__(
            event_type=event_type,
            modality=ModalityType.AUDIO,
            timestamp=time.time(),
            confidence=confidence,
            data=data,
            session_id=session_id
        )


@dataclass
class VisionEvent(ModalityEvent):
    """视觉事件"""
    def __init__(self, event_type: EventType, data: Dict[str, Any], 
                 confidence: float = 1.0, session_id: Optional[str] = None):
        super().__init__(
            event_type=event_type,
            modality=ModalityType.VISION,
            timestamp=time.time(),
            confidence=confidence,
            data=data,
            session_id=session_id
        )


@dataclass
class GestureEvent(ModalityEvent):
    """手势事件"""
    def __init__(self, event_type: EventType, data: Dict[str, Any], 
                 confidence: float = 1.0, session_id: Optional[str] = None):
        super().__init__(
            event_type=event_type,
            modality=ModalityType.GESTURE,
            timestamp=time.time(),
            confidence=confidence,
            data=data,
            session_id=session_id
        )


class EventBus:
    """事件总线 - 负责事件的发布和订阅"""
    
    def __init__(self):
        self._subscribers = {}
        self._event_history = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, callback):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
    
    def publish(self, event: ModalityEvent):
        """发布事件"""
        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # 通知订阅者
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"事件处理错误: {e}")
    
    def get_recent_events(self, event_type: Optional[EventType] = None, 
                         modality: Optional[ModalityType] = None,
                         time_window: float = 5.0) -> list:
        """获取最近的事件"""
        current_time = time.time()
        recent_events = []
        
        for event in reversed(self._event_history):
            if current_time - event.timestamp > time_window:
                break
            
            if event_type and event.event_type != event_type:
                continue
            
            if modality and event.modality != modality:
                continue
            
            recent_events.append(event)
        
        return list(reversed(recent_events))


# 全局事件总线实例
event_bus = EventBus()
