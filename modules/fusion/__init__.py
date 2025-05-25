"""
多模态融合模块

该模块实现了多模态数据融合和决策系统，包括：
- 事件系统：统一的多模态事件处理
- 状态管理：系统状态和交互会话管理
- 融合引擎：基于规则的多模态数据融合
- 场景处理：具体交互场景的处理逻辑
"""

from .events import (
    ModalityType, EventType, ModalityEvent, 
    AudioEvent, VisionEvent, GestureEvent,
    EventBus, event_bus
)

from .state_manager import (
    SystemState, InteractionScenario, InteractionSession,
    StateManager, state_manager
)

from .rule_fusion import (
    FusionStrategy, ConflictResolution, FusionRule,
    RuleFusionEngine, fusion_engine
)

from .scenario_handler import (
    ResponseType, SystemResponse,
    ScenarioHandler, scenario_handler
)

__all__ = [
    # 事件系统
    'ModalityType', 'EventType', 'ModalityEvent',
    'AudioEvent', 'VisionEvent', 'GestureEvent',
    'EventBus', 'event_bus',
    
    # 状态管理
    'SystemState', 'InteractionScenario', 'InteractionSession',
    'StateManager', 'state_manager',
    
    # 融合引擎
    'FusionStrategy', 'ConflictResolution', 'FusionRule',
    'RuleFusionEngine', 'fusion_engine',
    
    # 场景处理
    'ResponseType', 'SystemResponse',
    'ScenarioHandler', 'scenario_handler'
]


def initialize_fusion_system():
    """初始化融合系统"""
    print("🔧 初始化多模态融合系统...")
    
    # 系统已通过导入自动初始化
    print("✅ 融合系统初始化完成")
    print(f"   - 事件总线: {len(event_bus._subscribers)} 个订阅者")
    print(f"   - 状态管理器: {state_manager.current_state.value}")
    print(f"   - 融合引擎: {len(fusion_engine.fusion_rules)} 个规则")
    print(f"   - 场景处理器: 已就绪")


def get_system_status():
    """获取系统状态"""
    return {
        "current_state": state_manager.current_state.value,
        "active_session": state_manager.get_current_session_info(),
        "session_stats": state_manager.get_session_stats(),
        "fusion_stats": fusion_engine.get_fusion_stats(),
        "response_stats": scenario_handler.get_response_stats(),
        "event_subscribers": len(event_bus._subscribers),
        "event_history_size": len(event_bus._event_history)
    }
