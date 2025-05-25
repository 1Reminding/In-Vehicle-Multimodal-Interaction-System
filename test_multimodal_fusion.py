#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态融合系统测试脚本

测试各种融合场景和决策策略：
1. 分心提醒场景测试
2. 语音命令场景测试
3. 手势控制场景测试
4. 冲突解决测试
5. 系统性能测试
"""

import time
import threading
import unittest
from typing import List, Dict, Any

from modules.fusion import (
    initialize_fusion_system, get_system_status,
    event_bus, state_manager, fusion_engine, scenario_handler,
    ModalityEvent, EventType, ModalityType,
    AudioEvent, VisionEvent, GestureEvent,
    SystemState, InteractionScenario
)


class TestMultimodalFusion(unittest.TestCase):
    """多模态融合系统测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 重置系统状态
        if state_manager.current_session:
            state_manager.end_current_session("test_reset")
        
        # 清理事件历史
        event_bus._event_history.clear()
        fusion_engine.interaction_log.clear()
        scenario_handler.response_history.clear()
        
        print(f"\n🧪 开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试后清理"""
        if state_manager.current_session:
            state_manager.end_current_session("test_cleanup")
        print(f"✅ 测试完成: {self._testMethodName}")
    
    def test_distraction_alert_scenario(self):
        """测试分心提醒场景"""
        print("   测试分心提醒场景...")
        
        # 1. 触发分心检测
        gaze_event = VisionEvent(
            event_type=EventType.GAZE_CHANGED,
            data={"state": "left", "timestamp": time.time()},
            confidence=0.9
        )
        event_bus.publish(gaze_event)
        
        # 验证会话已创建
        self.assertIsNotNone(state_manager.current_session)
        self.assertEqual(state_manager.current_session.scenario, InteractionScenario.DISTRACTION_ALERT)
        self.assertEqual(state_manager.current_state, SystemState.WAITING_RESPONSE)
        
        # 2. 语音确认
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
        
        # 3. 手势确认
        gesture_event = GestureEvent(
            event_type=EventType.GESTURE_DETECTED,
            data={"gesture": "thumbs_up"},
            confidence=0.8
        )
        event_bus.publish(gesture_event)
        
        # 等待融合处理
        time.sleep(0.1)
        
        # 验证融合结果
        self.assertEqual(state_manager.current_state, SystemState.IDLE)
        self.assertIsNone(state_manager.current_session)
        self.assertGreater(len(fusion_engine.interaction_log), 0)
        
        # 验证最后一次融合决策
        last_fusion = fusion_engine.interaction_log[-1]
        self.assertIn(last_fusion["fusion_result"]["decision"], ["confirm", "attention"])
        
        print(f"     ✓ 融合决策: {last_fusion['fusion_result']['decision']}")
        print(f"     ✓ 置信度: {last_fusion['fusion_result']['confidence']:.2f}")
    
    def test_voice_command_scenario(self):
        """测试语音命令场景"""
        print("   测试语音命令场景...")
        
        # 触发语音命令场景
        session_id = scenario_handler.trigger_voice_command_scenario("打开导航", 0.9)
        
        # 验证会话状态
        self.assertIsNotNone(state_manager.current_session)
        self.assertEqual(state_manager.current_session.scenario, InteractionScenario.VOICE_COMMAND)
        
        # 添加确认手势
        gesture_event = GestureEvent(
            event_type=EventType.GESTURE_DETECTED,
            data={"gesture": "ok"},
            confidence=0.8
        )
        event_bus.publish(gesture_event)
        
        time.sleep(0.1)
        
        # 验证结果
        self.assertGreater(len(fusion_engine.interaction_log), 0)
        print(f"     ✓ 语音命令场景完成")
    
    def test_gesture_control_scenario(self):
        """测试手势控制场景"""
        print("   测试手势控制场景...")
        
        # 触发手势控制场景
        session_id = scenario_handler.trigger_gesture_control_scenario("wave", 0.8)
        
        # 验证会话状态
        self.assertIsNotNone(state_manager.current_session)
        self.assertEqual(state_manager.current_session.scenario, InteractionScenario.GESTURE_CONTROL)
        
        # 添加视线确认
        gaze_event = VisionEvent(
            event_type=EventType.GAZE_CHANGED,
            data={"state": "center"},
            confidence=0.9
        )
        event_bus.publish(gaze_event)
        
        time.sleep(0.1)
        
        print(f"     ✓ 手势控制场景完成")
    
    def test_conflict_resolution(self):
        """测试冲突解决"""
        print("   测试冲突解决...")
        
        # 创建分心提醒会话
        gaze_event = VisionEvent(
            event_type=EventType.GAZE_CHANGED,
            data={"state": "right"},
            confidence=0.9
        )
        event_bus.publish(gaze_event)
        
        # 添加冲突的响应
        # 语音说确认
        speech_event = AudioEvent(
            event_type=EventType.INTENT_CLASSIFIED,
            data={"intent": "attention_confirm"},
            confidence=0.8
        )
        event_bus.publish(speech_event)
        
        # 手势说拒绝
        gesture_event = GestureEvent(
            event_type=EventType.GESTURE_DETECTED,
            data={"gesture": "thumbs_down"},
            confidence=0.7
        )
        event_bus.publish(gesture_event)
        
        time.sleep(0.1)
        
        # 验证冲突解决
        if fusion_engine.interaction_log:
            last_fusion = fusion_engine.interaction_log[-1]
            decision = last_fusion["fusion_result"]["decision"]
            strategy = last_fusion["fusion_result"]["strategy"]
            print(f"     ✓ 冲突解决策略: {strategy}")
            print(f"     ✓ 最终决策: {decision}")
    
    def test_timeout_handling(self):
        """测试超时处理"""
        print("   测试超时处理...")
        
        # 创建短超时的会话
        session_id = state_manager.start_interaction(
            scenario=InteractionScenario.DISTRACTION_ALERT,
            expected_modalities=[ModalityType.AUDIO, ModalityType.GESTURE],
            timeout=0.5  # 0.5秒超时
        )
        
        # 等待超时
        time.sleep(0.6)
        
        # 尝试添加事件（应该失败）
        speech_event = AudioEvent(
            event_type=EventType.SPEECH_RECOGNIZED,
            data={"text": "测试"},
            confidence=0.8
        )
        
        result = state_manager.add_event_to_session(speech_event)
        self.assertFalse(result)  # 应该返回False，因为会话已超时
        
        print(f"     ✓ 超时处理正常")
    
    def test_fusion_strategies(self):
        """测试不同的融合策略"""
        print("   测试融合策略...")
        
        strategies_tested = []
        
        # 测试置信度加权策略（语音命令场景）
        session_id = scenario_handler.trigger_voice_command_scenario("测试命令", 0.9)
        gesture_event = GestureEvent(
            event_type=EventType.GESTURE_DETECTED,
            data={"gesture": "ok"},
            confidence=0.6
        )
        event_bus.publish(gesture_event)
        time.sleep(0.1)
        
        if fusion_engine.interaction_log:
            strategy = fusion_engine.interaction_log[-1]["fusion_result"]["strategy"]
            strategies_tested.append(strategy)
        
        # 测试优先级策略（分心提醒场景）
        gaze_event = VisionEvent(
            event_type=EventType.GAZE_CHANGED,
            data={"state": "left"},
            confidence=0.9
        )
        event_bus.publish(gaze_event)
        
        speech_event = AudioEvent(
            event_type=EventType.INTENT_CLASSIFIED,
            data={"intent": "attention_confirm"},
            confidence=0.8
        )
        event_bus.publish(speech_event)
        time.sleep(0.1)
        
        if len(fusion_engine.interaction_log) > 1:
            strategy = fusion_engine.interaction_log[-1]["fusion_result"]["strategy"]
            strategies_tested.append(strategy)
        
        print(f"     ✓ 测试的策略: {strategies_tested}")
    
    def test_system_performance(self):
        """测试系统性能"""
        print("   测试系统性能...")
        
        start_time = time.time()
        
        # 快速发送多个事件
        for i in range(10):
            gaze_event = VisionEvent(
                event_type=EventType.GAZE_CHANGED,
                data={"state": "left" if i % 2 == 0 else "center"},
                confidence=0.8
            )
            event_bus.publish(gaze_event)
            
            if i % 3 == 0:  # 每3个事件添加一个语音事件
                speech_event = AudioEvent(
                    event_type=EventType.SPEECH_RECOGNIZED,
                    data={"text": f"测试{i}"},
                    confidence=0.7
                )
                event_bus.publish(speech_event)
        
        processing_time = time.time() - start_time
        
        # 验证性能
        self.assertLess(processing_time, 1.0)  # 应该在1秒内完成
        
        print(f"     ✓ 处理10个事件用时: {processing_time:.3f}秒")
        print(f"     ✓ 事件历史大小: {len(event_bus._event_history)}")


def run_interactive_demo():
    """运行交互式演示"""
    print("🎭 多模态融合系统交互式演示")
    print("=" * 50)
    
    # 初始化系统
    initialize_fusion_system()
    
    def print_status():
        status = get_system_status()
        print(f"\n📊 系统状态: {status['current_state']}")
        if status['active_session']:
            session = status['active_session']
            print(f"   活跃会话: {session['scenario']} ({session['duration']:.1f}s)")
            print(f"   期望模态: {', '.join(session['expected_modalities'])}")
            print(f"   已收到模态: {', '.join(session['received_modalities'])}")
    
    scenarios = [
        ("分心提醒场景", demo_distraction_scenario),
        ("语音命令场景", demo_voice_command_scenario),
        ("手势控制场景", demo_gesture_control_scenario),
        ("冲突解决演示", demo_conflict_resolution)
    ]
    
    for name, demo_func in scenarios:
        print(f"\n🎯 演示: {name}")
        print("-" * 30)
        demo_func()
        print_status()
        time.sleep(1)
    
    # 打印最终统计
    print("\n📈 最终统计:")
    status = get_system_status()
    print(f"   会话统计: {status['session_stats']}")
    print(f"   融合统计: {status['fusion_stats']}")
    print(f"   响应统计: {status['response_stats']}")


def demo_distraction_scenario():
    """演示分心提醒场景"""
    # 1. 视线偏离
    gaze_event = VisionEvent(
        event_type=EventType.GAZE_CHANGED,
        data={"state": "left"},
        confidence=0.9
    )
    event_bus.publish(gaze_event)
    print("   1. 视线偏离 -> 触发分心检测")
    time.sleep(1)
    
    # 2. 语音确认
    intent_event = AudioEvent(
        event_type=EventType.INTENT_CLASSIFIED,
        data={"intent": "attention_confirm"},
        confidence=0.8
    )
    event_bus.publish(intent_event)
    print("   2. 语音确认 -> 融合处理")
    time.sleep(1)
    
    # 3. 手势确认
    gesture_event = GestureEvent(
        event_type=EventType.GESTURE_DETECTED,
        data={"gesture": "thumbs_up"},
        confidence=0.8
    )
    event_bus.publish(gesture_event)
    print("   3. 手势确认 -> 完成交互")
    time.sleep(0.5)


def demo_voice_command_scenario():
    """演示语音命令场景"""
    session_id = scenario_handler.trigger_voice_command_scenario("打开音乐", 0.9)
    print("   1. 语音命令: '打开音乐'")
    time.sleep(1)
    
    gesture_event = GestureEvent(
        event_type=EventType.GESTURE_DETECTED,
        data={"gesture": "ok"},
        confidence=0.8
    )
    event_bus.publish(gesture_event)
    print("   2. 手势确认: OK")
    time.sleep(0.5)


def demo_gesture_control_scenario():
    """演示手势控制场景"""
    session_id = scenario_handler.trigger_gesture_control_scenario("wave", 0.8)
    print("   1. 手势控制: 挥手")
    time.sleep(1)
    
    gaze_event = VisionEvent(
        event_type=EventType.GAZE_CHANGED,
        data={"state": "center"},
        confidence=0.9
    )
    event_bus.publish(gaze_event)
    print("   2. 视线确认: 中心")
    time.sleep(0.5)


def demo_conflict_resolution():
    """演示冲突解决"""
    # 触发分心检测
    gaze_event = VisionEvent(
        event_type=EventType.GAZE_CHANGED,
        data={"state": "right"},
        confidence=0.9
    )
    event_bus.publish(gaze_event)
    print("   1. 视线偏离 -> 分心检测")
    time.sleep(1)
    
    # 冲突的响应
    speech_event = AudioEvent(
        event_type=EventType.INTENT_CLASSIFIED,
        data={"intent": "attention_confirm"},
        confidence=0.8
    )
    event_bus.publish(speech_event)
    print("   2. 语音确认: 已注意")
    
    gesture_event = GestureEvent(
        event_type=EventType.GESTURE_DETECTED,
        data={"gesture": "thumbs_down"},
        confidence=0.7
    )
    event_bus.publish(gesture_event)
    print("   3. 手势拒绝: 拇指向下")
    print("   4. 冲突解决: 基于优先级选择语音")
    time.sleep(0.5)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_interactive_demo()
    else:
        # 运行单元测试
        print("🧪 运行多模态融合系统测试")
        unittest.main(verbosity=2) 