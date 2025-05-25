from typing import Dict, List, Optional, Any
from enum import Enum
import time
import threading
from dataclasses import dataclass
from .events import ModalityEvent, EventType, ModalityType, event_bus
from .state_manager import SystemState, InteractionScenario, state_manager


class ResponseType(Enum):
    """响应类型枚举"""
    TEXT = "text"
    AUDIO = "audio"
    VISUAL = "visual"
    HAPTIC = "haptic"


@dataclass
class SystemResponse:
    """系统响应"""
    response_type: ResponseType
    content: str
    metadata: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class ScenarioHandler:
    """场景处理器 - 管理具体的多模态交互场景"""
    
    def __init__(self):
        self.active_scenarios = {}
        self.response_history = []
        
        # 订阅系统事件
        event_bus.subscribe(EventType.DISTRACTION_DETECTED, self._handle_distraction_detected)
        event_bus.subscribe(EventType.ATTENTION_CONFIRMED, self._handle_attention_confirmed)
        event_bus.subscribe(EventType.INTERACTION_COMPLETED, self._handle_interaction_completed)
        
        # 订阅状态变化
        state_manager.subscribe_state_change(SystemState.WAITING_RESPONSE, self._on_waiting_response)
        state_manager.subscribe_state_change(SystemState.INTERACTION_COMPLETE, self._on_interaction_complete)
    
    def _handle_distraction_detected(self, event: ModalityEvent):
        """处理分心检测事件"""
        session_id = event.session_id
        gaze_state = event.data.get("gaze_state", "unknown")
        
        # 生成分心提醒响应
        responses = self._generate_distraction_alert_responses(gaze_state, session_id)
        
        # 发送响应
        for response in responses:
            self._send_response(response)
            
        print(f"🚨 分心提醒已发送: {len(responses)} 个响应")
    
    def _handle_attention_confirmed(self, event: ModalityEvent):
        """处理注意力确认事件"""
        session_id = event.session_id
        decision = event.data.get("decision")
        
        # 生成确认响应
        responses = self._generate_attention_confirmed_responses(decision, session_id)
        
        # 发送响应
        for response in responses:
            self._send_response(response)
            
        print(f"✅ 注意力确认响应已发送: {len(responses)} 个响应")
    
    def _handle_interaction_completed(self, event: ModalityEvent):
        """处理交互完成事件"""
        session_id = event.session_id
        print(f"🎯 交互完成: {session_id}")
    
    def _on_waiting_response(self, old_state, new_state, metadata):
        """当系统进入等待响应状态时"""
        session_id = metadata.get("session_id")
        scenario = metadata.get("scenario")
        expected_modalities = metadata.get("expected_modalities", [])
        
        print(f"⏳ 等待用户响应: {scenario} (期望模态: {expected_modalities})")
        
        # 可以在这里设置超时提醒
        self._schedule_timeout_reminder(session_id, 8.0)  # 8秒后提醒
    
    def _on_interaction_complete(self, old_state, new_state, metadata):
        """当交互完成时"""
        print("🎉 交互流程完成")
    
    def _generate_distraction_alert_responses(self, gaze_state: str, session_id: str) -> List[SystemResponse]:
        """生成分心提醒响应"""
        responses = []
        
        # 文本响应
        text_content = f"检测到您的视线偏向{gaze_state}，请注意道路安全！"
        responses.append(SystemResponse(
            response_type=ResponseType.TEXT,
            content=text_content,
            metadata={
                "session_id": session_id,
                "scenario": "distraction_alert",
                "gaze_state": gaze_state
            }
        ))
        
        # 语音响应
        audio_content = "请注意道路，确保行车安全。您可以说'已注意道路'或做手势确认。"
        responses.append(SystemResponse(
            response_type=ResponseType.AUDIO,
            content=audio_content,
            metadata={
                "session_id": session_id,
                "scenario": "distraction_alert",
                "voice_prompt": True
            }
        ))
        
        # 视觉响应
        visual_content = "⚠️ 分心提醒 - 请将注意力转回道路"
        responses.append(SystemResponse(
            response_type=ResponseType.VISUAL,
            content=visual_content,
            metadata={
                "session_id": session_id,
                "scenario": "distraction_alert",
                "display_duration": 5.0,
                "priority": "high"
            }
        ))
        
        return responses
    
    def _generate_attention_confirmed_responses(self, decision: str, session_id: str) -> List[SystemResponse]:
        """生成注意力确认响应"""
        responses = []
        
        if decision in ["confirm", "attention"]:
            # 确认响应
            text_content = "感谢您的确认，请继续保持注意力集中。"
            audio_content = "好的，请继续安全驾驶。"
            visual_content = "✅ 注意力已确认"
            
        else:
            # 其他情况
            text_content = "请继续关注道路安全。"
            audio_content = "请保持注意力集中。"
            visual_content = "⚠️ 请注意道路"
        
        responses.extend([
            SystemResponse(
                response_type=ResponseType.TEXT,
                content=text_content,
                metadata={"session_id": session_id, "decision": decision}
            ),
            SystemResponse(
                response_type=ResponseType.AUDIO,
                content=audio_content,
                metadata={"session_id": session_id, "decision": decision}
            ),
            SystemResponse(
                response_type=ResponseType.VISUAL,
                content=visual_content,
                metadata={
                    "session_id": session_id,
                    "decision": decision,
                    "display_duration": 3.0
                }
            )
        ])
        
        return responses
    
    def _send_response(self, response: SystemResponse):
        """发送系统响应"""
        # 记录响应历史
        self.response_history.append(response)
        
        # 根据响应类型处理
        if response.response_type == ResponseType.TEXT:
            print(f"📝 文本响应: {response.content}")
            
        elif response.response_type == ResponseType.AUDIO:
            print(f"🔊 语音响应: {response.content}")
            # 这里可以集成TTS系统
            
        elif response.response_type == ResponseType.VISUAL:
            print(f"👁 视觉响应: {response.content}")
            # 这里可以集成UI显示系统
            
        elif response.response_type == ResponseType.HAPTIC:
            print(f"📳 触觉响应: {response.content}")
            # 这里可以集成触觉反馈系统
        
        # 保持历史记录大小
        if len(self.response_history) > 500:
            self.response_history = self.response_history[-250:]
    
    def _schedule_timeout_reminder(self, session_id: str, delay: float):
        """安排超时提醒"""
        def timeout_reminder():
            time.sleep(delay)
            
            # 检查会话是否仍然活跃
            if (state_manager.current_session and 
                state_manager.current_session.session_id == session_id and
                state_manager.current_state == SystemState.WAITING_RESPONSE):
                
                # 发送提醒
                reminder_responses = [
                    SystemResponse(
                        response_type=ResponseType.AUDIO,
                        content="请确认您是否已注意道路安全。",
                        metadata={"session_id": session_id, "type": "timeout_reminder"}
                    ),
                    SystemResponse(
                        response_type=ResponseType.VISUAL,
                        content="⏰ 等待确认中...",
                        metadata={"session_id": session_id, "type": "timeout_reminder"}
                    )
                ]
                
                for response in reminder_responses:
                    self._send_response(response)
                
                print(f"⏰ 发送超时提醒: {session_id[:8]}")
        
        # 在后台线程中执行
        threading.Thread(target=timeout_reminder, daemon=True).start()
    
    def trigger_voice_command_scenario(self, command: str, confidence: float = 0.9):
        """触发语音命令场景"""
        session_id = state_manager.start_interaction(
            scenario=InteractionScenario.VOICE_COMMAND,
            expected_modalities=[ModalityType.AUDIO, ModalityType.GESTURE],
            timeout=8.0,
            metadata={"command": command}
        )
        
        # 创建语音事件
        speech_event = ModalityEvent(
            event_type=EventType.SPEECH_RECOGNIZED,
            modality=ModalityType.AUDIO,
            timestamp=time.time(),
            confidence=confidence,
            data={"text": command, "command": command},
            session_id=session_id
        )
        
        event_bus.publish(speech_event)
        return session_id
    
    def trigger_gesture_control_scenario(self, gesture: str, confidence: float = 0.8):
        """触发手势控制场景"""
        session_id = state_manager.start_interaction(
            scenario=InteractionScenario.GESTURE_CONTROL,
            expected_modalities=[ModalityType.GESTURE, ModalityType.GAZE],
            timeout=5.0,
            metadata={"gesture": gesture}
        )
        
        # 创建手势事件
        gesture_event = ModalityEvent(
            event_type=EventType.GESTURE_DETECTED,
            modality=ModalityType.GESTURE,
            timestamp=time.time(),
            confidence=confidence,
            data={"gesture": gesture},
            session_id=session_id
        )
        
        event_bus.publish(gesture_event)
        return session_id
    
    def get_response_stats(self) -> Dict[str, Any]:
        """获取响应统计信息"""
        if not self.response_history:
            return {"total_responses": 0}
        
        total_responses = len(self.response_history)
        
        # 按类型统计
        type_stats = {}
        for response in self.response_history:
            response_type = response.response_type.value
            if response_type not in type_stats:
                type_stats[response_type] = 0
            type_stats[response_type] += 1
        
        # 按场景统计
        scenario_stats = {}
        for response in self.response_history:
            scenario = response.metadata.get("scenario", "unknown")
            if scenario not in scenario_stats:
                scenario_stats[scenario] = 0
            scenario_stats[scenario] += 1
        
        return {
            "total_responses": total_responses,
            "type_stats": type_stats,
            "scenario_stats": scenario_stats,
            "recent_responses": len([r for r in self.response_history 
                                   if time.time() - r.timestamp < 300])  # 最近5分钟
        }


# 全局场景处理器实例
scenario_handler = ScenarioHandler() 