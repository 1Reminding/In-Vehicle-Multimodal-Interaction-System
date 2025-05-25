from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import json
from dataclasses import dataclass
from .events import ModalityEvent, EventType, ModalityType, event_bus
from .state_manager import SystemState, InteractionScenario, state_manager


class FusionStrategy(Enum):
    """融合策略枚举"""
    MAJORITY_VOTE = "majority_vote"         # 多数投票
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # 置信度加权
    PRIORITY_BASED = "priority_based"       # 优先级策略
    TIME_WINDOW = "time_window"             # 时间窗口策略


class ConflictResolution(Enum):
    """冲突解决策略"""
    HIGHEST_CONFIDENCE = "highest_confidence"  # 选择置信度最高的
    MODALITY_PRIORITY = "modality_priority"    # 按模态优先级
    TEMPORAL_ORDER = "temporal_order"          # 按时间顺序
    USER_PREFERENCE = "user_preference"        # 用户偏好


@dataclass
class FusionRule:
    """融合规则"""
    scenario: InteractionScenario
    required_modalities: List[ModalityType]
    optional_modalities: List[ModalityType]
    time_window: float  # 时间窗口（秒）
    fusion_strategy: FusionStrategy
    conflict_resolution: ConflictResolution
    modality_weights: Dict[ModalityType, float]
    priority_order: List[ModalityType]


class RuleFusionEngine:
    """基于规则的融合引擎"""
    
    def __init__(self):
        self.fusion_rules = self._initialize_rules()
        self.interaction_log = []
        
        # 订阅相关事件
        event_bus.subscribe(EventType.GAZE_CHANGED, self._handle_gaze_event)
        event_bus.subscribe(EventType.GESTURE_DETECTED, self._handle_gesture_event)
        event_bus.subscribe(EventType.SPEECH_RECOGNIZED, self._handle_speech_event)
        event_bus.subscribe(EventType.INTENT_CLASSIFIED, self._handle_intent_event)
        event_bus.subscribe(EventType.HEAD_POSE_CHANGED, self._handle_head_pose_event)
    
    def _initialize_rules(self) -> Dict[InteractionScenario, FusionRule]:
        """初始化融合规则"""
        return {
            # 分心提醒场景
            InteractionScenario.DISTRACTION_ALERT: FusionRule(
                scenario=InteractionScenario.DISTRACTION_ALERT,
                required_modalities=[ModalityType.GAZE],  # 必须有视线检测
                optional_modalities=[ModalityType.AUDIO, ModalityType.GESTURE],  # 语音或手势确认
                time_window=10.0,
                fusion_strategy=FusionStrategy.PRIORITY_BASED,
                conflict_resolution=ConflictResolution.MODALITY_PRIORITY,
                modality_weights={
                    ModalityType.GAZE: 0.4,
                    ModalityType.AUDIO: 0.4,
                    ModalityType.GESTURE: 0.2
                },
                priority_order=[ModalityType.AUDIO, ModalityType.GESTURE, ModalityType.GAZE]
            ),
            
            # 语音命令场景
            InteractionScenario.VOICE_COMMAND: FusionRule(
                scenario=InteractionScenario.VOICE_COMMAND,
                required_modalities=[ModalityType.AUDIO],
                optional_modalities=[ModalityType.GESTURE, ModalityType.GAZE],
                time_window=5.0,
                fusion_strategy=FusionStrategy.CONFIDENCE_WEIGHTED,
                conflict_resolution=ConflictResolution.HIGHEST_CONFIDENCE,
                modality_weights={
                    ModalityType.AUDIO: 0.6,
                    ModalityType.GESTURE: 0.3,
                    ModalityType.GAZE: 0.1
                },
                priority_order=[ModalityType.AUDIO, ModalityType.GESTURE, ModalityType.GAZE]
            ),
            
            # 手势控制场景
            InteractionScenario.GESTURE_CONTROL: FusionRule(
                scenario=InteractionScenario.GESTURE_CONTROL,
                required_modalities=[ModalityType.GESTURE],
                optional_modalities=[ModalityType.GAZE, ModalityType.AUDIO],
                time_window=3.0,
                fusion_strategy=FusionStrategy.MAJORITY_VOTE,
                conflict_resolution=ConflictResolution.TEMPORAL_ORDER,
                modality_weights={
                    ModalityType.GESTURE: 0.5,
                    ModalityType.GAZE: 0.3,
                    ModalityType.AUDIO: 0.2
                },
                priority_order=[ModalityType.GESTURE, ModalityType.GAZE, ModalityType.AUDIO]
            )
        }
    
    def _handle_gaze_event(self, event: ModalityEvent):
        """处理视线事件"""
        if event.data.get("state") in ["left", "right"]:  # 视线偏离
            self._trigger_distraction_scenario(event)
        
        # 将事件添加到当前会话
        state_manager.add_event_to_session(event)
        self._check_fusion_completion()
    
    def _handle_gesture_event(self, event: ModalityEvent):
        """处理手势事件"""
        gesture = event.data.get("gesture")
        
        # 根据手势类型判断意图
        if gesture in ["thumbs_up", "ok"]:
            event.data["intent"] = "confirm"
        elif gesture in ["thumbs_down", "stop"]:
            event.data["intent"] = "reject"
        elif gesture in ["wave"]:
            event.data["intent"] = "attention"
        
        state_manager.add_event_to_session(event)
        self._check_fusion_completion()
    
    def _handle_speech_event(self, event: ModalityEvent):
        """处理语音识别事件"""
        state_manager.add_event_to_session(event)
        self._check_fusion_completion()
    
    def _handle_intent_event(self, event: ModalityEvent):
        """处理意图分类事件"""
        intent = event.data.get("intent")
        
        # 根据意图判断是否为注意力确认
        if intent in ["attention_confirm", "road_focus"]:
            event.data["response_type"] = "attention_confirmed"
        elif intent in ["reject", "busy"]:
            event.data["response_type"] = "attention_rejected"
        
        state_manager.add_event_to_session(event)
        self._check_fusion_completion()
    
    def _handle_head_pose_event(self, event: ModalityEvent):
        """处理头部姿态事件"""
        state_manager.add_event_to_session(event)
        self._check_fusion_completion()
    
    def _trigger_distraction_scenario(self, trigger_event: ModalityEvent):
        """触发分心提醒场景"""
        if state_manager.current_state != SystemState.IDLE:
            return  # 已有活跃会话
        
        # 开始分心提醒会话
        session_id = state_manager.start_interaction(
            scenario=InteractionScenario.DISTRACTION_ALERT,
            expected_modalities=[ModalityType.AUDIO, ModalityType.GESTURE],
            timeout=15.0,
            metadata={
                "trigger_event": {
                    "type": trigger_event.event_type.value,
                    "data": trigger_event.data,
                    "timestamp": trigger_event.timestamp
                }
            }
        )
        
        # 发布分心检测事件
        distraction_event = ModalityEvent(
            event_type=EventType.DISTRACTION_DETECTED,
            modality=ModalityType.VISION,
            timestamp=time.time(),
            confidence=trigger_event.confidence,
            data={
                "reason": "gaze_deviation",
                "gaze_state": trigger_event.data.get("state"),
                "session_id": session_id
            },
            session_id=session_id
        )
        event_bus.publish(distraction_event)
        
        print(f"🚨 检测到分心: {trigger_event.data.get('state')} (会话: {session_id[:8]})")
    
    def _check_fusion_completion(self):
        """检查融合是否完成"""
        if not state_manager.current_session:
            return
        
        session = state_manager.current_session
        rule = self.fusion_rules.get(session.scenario)
        
        if not rule:
            return
        
        # 获取时间窗口内的事件
        recent_events = self._get_session_events_in_window(session, rule.time_window)
        
        # 检查是否满足融合条件
        if self._can_perform_fusion(recent_events, rule):
            fusion_result = self._perform_fusion(recent_events, rule)
            self._handle_fusion_result(fusion_result, session)
    
    def _get_session_events_in_window(self, session, time_window: float) -> List[ModalityEvent]:
        """获取会话中时间窗口内的事件"""
        current_time = time.time()
        recent_events = []
        
        for event in session.received_events:
            if current_time - event.timestamp <= time_window:
                recent_events.append(event)
        
        return recent_events
    
    def _can_perform_fusion(self, events: List[ModalityEvent], rule: FusionRule) -> bool:
        """检查是否可以执行融合"""
        # 检查必需模态
        received_modalities = set(event.modality for event in events)
        required_modalities = set(rule.required_modalities)
        
        # 必须包含所有必需模态
        if not required_modalities.issubset(received_modalities):
            return False
        
        # 至少要有一个可选模态（如果有定义）
        if rule.optional_modalities:
            optional_modalities = set(rule.optional_modalities)
            if not optional_modalities.intersection(received_modalities):
                return False
        
        return True
    
    def _perform_fusion(self, events: List[ModalityEvent], rule: FusionRule) -> Dict[str, Any]:
        """执行多模态融合"""
        fusion_result = {
            "strategy": rule.fusion_strategy.value,
            "events_count": len(events),
            "modalities": list(set(event.modality.value for event in events)),
            "timestamp": time.time(),
            "confidence": 0.0,
            "decision": None,
            "conflicts": [],
            "details": {}
        }
        
        if rule.fusion_strategy == FusionStrategy.CONFIDENCE_WEIGHTED:
            fusion_result = self._confidence_weighted_fusion(events, rule, fusion_result)
        elif rule.fusion_strategy == FusionStrategy.PRIORITY_BASED:
            fusion_result = self._priority_based_fusion(events, rule, fusion_result)
        elif rule.fusion_strategy == FusionStrategy.MAJORITY_VOTE:
            fusion_result = self._majority_vote_fusion(events, rule, fusion_result)
        
        return fusion_result
    
    def _confidence_weighted_fusion(self, events: List[ModalityEvent], 
                                   rule: FusionRule, result: Dict[str, Any]) -> Dict[str, Any]:
        """置信度加权融合"""
        weighted_scores = {}
        total_weight = 0.0
        
        for event in events:
            modality = event.modality
            weight = rule.modality_weights.get(modality, 1.0)
            confidence = event.confidence
            
            # 根据事件数据判断意图
            intent = self._extract_intent_from_event(event)
            if intent:
                if intent not in weighted_scores:
                    weighted_scores[intent] = 0.0
                weighted_scores[intent] += weight * confidence
                total_weight += weight
        
        if weighted_scores and total_weight > 0:
            # 归一化分数
            for intent in weighted_scores:
                weighted_scores[intent] /= total_weight
            
            # 选择得分最高的意图
            best_intent = max(weighted_scores, key=weighted_scores.get)
            result["decision"] = best_intent
            result["confidence"] = weighted_scores[best_intent]
            result["details"]["scores"] = weighted_scores
        
        return result
    
    def _priority_based_fusion(self, events: List[ModalityEvent], 
                              rule: FusionRule, result: Dict[str, Any]) -> Dict[str, Any]:
        """基于优先级的融合"""
        # 按优先级排序事件
        priority_events = {}
        for event in events:
            modality = event.modality
            if modality not in priority_events:
                priority_events[modality] = []
            priority_events[modality].append(event)
        
        # 按优先级顺序处理
        for modality in rule.priority_order:
            if modality in priority_events:
                # 选择该模态中置信度最高的事件
                best_event = max(priority_events[modality], key=lambda e: e.confidence)
                intent = self._extract_intent_from_event(best_event)
                
                if intent:
                    result["decision"] = intent
                    result["confidence"] = best_event.confidence
                    result["details"]["selected_modality"] = modality.value
                    result["details"]["selected_event"] = {
                        "type": best_event.event_type.value,
                        "data": best_event.data
                    }
                    break
        
        return result
    
    def _majority_vote_fusion(self, events: List[ModalityEvent], 
                             rule: FusionRule, result: Dict[str, Any]) -> Dict[str, Any]:
        """多数投票融合"""
        intent_votes = {}
        
        for event in events:
            intent = self._extract_intent_from_event(event)
            if intent:
                if intent not in intent_votes:
                    intent_votes[intent] = []
                intent_votes[intent].append(event)
        
        if intent_votes:
            # 选择票数最多的意图
            best_intent = max(intent_votes, key=lambda i: len(intent_votes[i]))
            vote_count = len(intent_votes[best_intent])
            total_votes = len(events)
            
            result["decision"] = best_intent
            result["confidence"] = vote_count / total_votes
            result["details"]["votes"] = {intent: len(events) for intent, events in intent_votes.items()}
            result["details"]["vote_count"] = vote_count
            result["details"]["total_votes"] = total_votes
        
        return result
    
    def _extract_intent_from_event(self, event: ModalityEvent) -> Optional[str]:
        """从事件中提取意图"""
        # 语音意图
        if event.modality == ModalityType.AUDIO:
            return event.data.get("intent") or event.data.get("response_type")
        
        # 手势意图
        elif event.modality == ModalityType.GESTURE:
            gesture = event.data.get("gesture")
            if gesture in ["thumbs_up", "ok"]:
                return "confirm"
            elif gesture in ["thumbs_down", "stop"]:
                return "reject"
            elif gesture in ["wave"]:
                return "attention"
        
        # 视线意图
        elif event.modality == ModalityType.GAZE:
            gaze_state = event.data.get("state")
            if gaze_state == "center":
                return "attention"
            elif gaze_state in ["left", "right"]:
                return "distraction"
        
        return None
    
    def _handle_fusion_result(self, fusion_result: Dict[str, Any], session):
        """处理融合结果"""
        decision = fusion_result.get("decision")
        confidence = fusion_result.get("confidence", 0.0)
        
        # 记录融合日志
        log_entry = {
            "session_id": session.session_id,
            "scenario": session.scenario.value,
            "fusion_result": fusion_result,
            "timestamp": time.time()
        }
        self.interaction_log.append(log_entry)
        
        print(f"🔀 融合决策: {decision} (置信度: {confidence:.2f})")
        print(f"   策略: {fusion_result['strategy']}, 模态: {fusion_result['modalities']}")
        
        # 根据决策结果处理
        if decision == "confirm" or decision == "attention":
            # 用户确认注意力
            attention_event = ModalityEvent(
                event_type=EventType.ATTENTION_CONFIRMED,
                modality=ModalityType.VISION,  # 融合结果
                timestamp=time.time(),
                confidence=confidence,
                data={
                    "decision": decision,
                    "fusion_details": fusion_result
                },
                session_id=session.session_id
            )
            event_bus.publish(attention_event)
            
            # 结束会话
            state_manager.end_current_session("attention_confirmed")
            print("✅ 用户已确认注意力，分心提醒结束")
            
        elif decision == "reject":
            # 用户拒绝或仍然分心
            print("⚠️ 用户拒绝或仍然分心，继续监控")
            # 可以选择继续等待或采取其他措施
            
        # 保持日志大小
        if len(self.interaction_log) > 1000:
            self.interaction_log = self.interaction_log[-500:]
    
    def get_fusion_stats(self) -> Dict[str, Any]:
        """获取融合统计信息"""
        if not self.interaction_log:
            return {"total_fusions": 0}
        
        total_fusions = len(self.interaction_log)
        successful_fusions = len([log for log in self.interaction_log 
                                if log["fusion_result"].get("decision")])
        
        # 按场景统计
        scenario_stats = {}
        for log in self.interaction_log:
            scenario = log["scenario"]
            if scenario not in scenario_stats:
                scenario_stats[scenario] = 0
            scenario_stats[scenario] += 1
        
        # 按策略统计
        strategy_stats = {}
        for log in self.interaction_log:
            strategy = log["fusion_result"]["strategy"]
            if strategy not in strategy_stats:
                strategy_stats[strategy] = 0
            strategy_stats[strategy] += 1
        
        return {
            "total_fusions": total_fusions,
            "successful_fusions": successful_fusions,
            "success_rate": successful_fusions / total_fusions if total_fusions > 0 else 0,
            "scenario_stats": scenario_stats,
            "strategy_stats": strategy_stats
        }


# 全局融合引擎实例
fusion_engine = RuleFusionEngine()
