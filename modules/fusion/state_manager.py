from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time
import uuid
from .events import ModalityEvent, EventType, ModalityType


class SystemState(Enum):
    """系统状态枚举"""
    IDLE = "idle"                           # 空闲状态
    MONITORING = "monitoring"               # 监控状态
    DISTRACTION_DETECTED = "distraction_detected"  # 检测到分心
    WAITING_RESPONSE = "waiting_response"   # 等待用户响应
    PROCESSING_RESPONSE = "processing_response"  # 处理用户响应
    INTERACTION_COMPLETE = "interaction_complete"  # 交互完成


class InteractionScenario(Enum):
    """交互场景枚举"""
    DISTRACTION_ALERT = "distraction_alert"  # 分心提醒场景
    VOICE_COMMAND = "voice_command"          # 语音命令场景
    GESTURE_CONTROL = "gesture_control"      # 手势控制场景


@dataclass
class InteractionSession:
    """交互会话"""
    session_id: str
    scenario: InteractionScenario
    start_time: float
    state: SystemState
    expected_modalities: List[ModalityType]  # 期望的响应模态
    received_events: List[ModalityEvent] = field(default_factory=list)
    timeout: float = 10.0  # 超时时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """检查会话是否超时"""
        return time.time() - self.start_time > self.timeout
    
    @property
    def duration(self) -> float:
        """获取会话持续时间"""
        return time.time() - self.start_time


class StateManager:
    """状态管理器 - 管理系统状态和交互会话"""
    
    def __init__(self):
        self.current_state = SystemState.IDLE
        self.current_session: Optional[InteractionSession] = None
        self.session_history: List[InteractionSession] = []
        self.state_change_callbacks = {}
        
    def subscribe_state_change(self, state: SystemState, callback):
        """订阅状态变化"""
        if state not in self.state_change_callbacks:
            self.state_change_callbacks[state] = []
        self.state_change_callbacks[state].append(callback)
    
    def change_state(self, new_state: SystemState, metadata: Dict[str, Any] = None):
        """改变系统状态"""
        old_state = self.current_state
        self.current_state = new_state
        
        print(f"🔄 状态变化: {old_state.value} → {new_state.value}")
        
        # 通知状态变化回调
        if new_state in self.state_change_callbacks:
            for callback in self.state_change_callbacks[new_state]:
                try:
                    callback(old_state, new_state, metadata or {})
                except Exception as e:
                    print(f"状态变化回调错误: {e}")
    
    def start_interaction(self, scenario: InteractionScenario, 
                         expected_modalities: List[ModalityType],
                         timeout: float = 10.0,
                         metadata: Dict[str, Any] = None) -> str:
        """开始新的交互会话"""
        # 结束当前会话（如果存在）
        if self.current_session:
            self.end_current_session("new_session_started")
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        self.current_session = InteractionSession(
            session_id=session_id,
            scenario=scenario,
            start_time=time.time(),
            state=SystemState.WAITING_RESPONSE,
            expected_modalities=expected_modalities,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        self.change_state(SystemState.WAITING_RESPONSE, {
            "session_id": session_id,
            "scenario": scenario.value,
            "expected_modalities": [m.value for m in expected_modalities]
        })
        
        print(f"🎯 开始交互会话: {scenario.value} (ID: {session_id[:8]})")
        return session_id
    
    def add_event_to_session(self, event: ModalityEvent):
        """向当前会话添加事件"""
        if not self.current_session:
            return False
        
        # 检查会话是否超时
        if self.current_session.is_expired:
            self.end_current_session("timeout")
            return False
        
        # 添加事件到会话
        self.current_session.received_events.append(event)
        print(f"📝 会话事件: {event.modality.value} - {event.event_type.value}")
        
        return True
    
    def check_session_completion(self) -> bool:
        """检查当前会话是否完成"""
        if not self.current_session:
            return False
        
        # 检查是否收到了所有期望的模态响应
        received_modalities = set()
        for event in self.current_session.received_events:
            received_modalities.add(event.modality)
        
        expected_modalities = set(self.current_session.expected_modalities)
        
        # 如果收到了所有期望的模态响应
        if expected_modalities.issubset(received_modalities):
            self.end_current_session("completed")
            return True
        
        return False
    
    def end_current_session(self, reason: str = "manual"):
        """结束当前会话"""
        if not self.current_session:
            return
        
        session = self.current_session
        session.metadata["end_reason"] = reason
        session.metadata["duration"] = session.duration
        
        # 添加到历史记录
        self.session_history.append(session)
        
        # 清理历史记录（保留最近100个会话）
        if len(self.session_history) > 100:
            self.session_history.pop(0)
        
        print(f"✅ 会话结束: {session.scenario.value} (原因: {reason}, 时长: {session.duration:.1f}s)")
        
        self.current_session = None
        self.change_state(SystemState.IDLE)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not self.session_history:
            return {"total_sessions": 0}
        
        total_sessions = len(self.session_history)
        completed_sessions = len([s for s in self.session_history 
                                if s.metadata.get("end_reason") == "completed"])
        timeout_sessions = len([s for s in self.session_history 
                              if s.metadata.get("end_reason") == "timeout"])
        
        avg_duration = sum(s.duration for s in self.session_history) / total_sessions
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "timeout_sessions": timeout_sessions,
            "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0,
            "avg_duration": avg_duration
        }
    
    def get_current_session_info(self) -> Optional[Dict[str, Any]]:
        """获取当前会话信息"""
        if not self.current_session:
            return None
        
        session = self.current_session
        received_modalities = list(set(event.modality.value for event in session.received_events))
        expected_modalities = [m.value for m in session.expected_modalities]
        
        return {
            "session_id": session.session_id,
            "scenario": session.scenario.value,
            "state": session.state.value,
            "duration": session.duration,
            "timeout": session.timeout,
            "is_expired": session.is_expired,
            "expected_modalities": expected_modalities,
            "received_modalities": received_modalities,
            "events_count": len(session.received_events)
        }


# 全局状态管理器实例
state_manager = StateManager()
