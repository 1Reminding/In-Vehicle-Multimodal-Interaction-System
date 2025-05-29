#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API测试脚本 - 无TTS版本

测试多模态数据融合功能，不使用语音反馈
"""

import time
from modules.ai.deepseek_client import deepseek_client, MultimodalInput


def test_distraction_complete_scenario():
    """测试完整的分心驾驶场景：检测→确认→恢复"""
    print("🚨 测试场景: 完整分心驾驶流程")
    print("=" * 50)
    
    # 第一步：分心检测
    print("📍 步骤1: 分心驾驶检测")
    multimodal_input_1 = MultimodalInput(
        gaze_data={
            "state": "right",
            "duration": 4.5,
            "deviation": "severe"
        },
        gesture_data={
            "gesture": "none",
            "confidence": 0.0,
            "intent": "unknown"
        },
        speech_data={
            "text": "",
            "intent": "unknown",
            "emotion": "neutral"
        },
        timestamp=time.time(),
        duration=4.5
    )
    
    print("📊 输入数据:")
    print(f"   👁 眼动: {multimodal_input_1.gaze_data['state']} ({multimodal_input_1.gaze_data['duration']:.1f}s)")
    print(f"   🖐 手势: {multimodal_input_1.gesture_data['gesture']}")
    print(f"   🎤 语音: '{multimodal_input_1.speech_data['text']}'")
    
    print("\n🤖 正在调用DeepSeek API...")
    ai_response_1 = deepseek_client.analyze_multimodal_data(multimodal_input_1)
    
    print(f"\n🧠 AI分析结果:")
    print(f"   📋 推荐操作: {ai_response_1.recommendation_text}")
    print(f"   🎯 置信度: {ai_response_1.confidence:.2f}")
    print(f"   💭 推理过程: {ai_response_1.reasoning}")
    print(f"   ⚙️ 操作指令: {ai_response_1.action_code}")
    
    # 模拟用户反应时间
    print("\n⏳ 等待用户响应...")
    time.sleep(2)
    
    # 第二步：用户语音确认
    print("\n📍 步骤2: 用户语音确认")
    multimodal_input_2 = MultimodalInput(
        gaze_data={
            "state": "center",  # 用户已将视线转回
            "duration": 1.0,
            "deviation": "normal"
        },
        gesture_data={
            "gesture": "thumbs_up",  # 竖拇指确认
            "confidence": 0.88,
            "intent": "confirm"
        },
        speech_data={
            "text": "已注意道路",  # 语音确认
            "intent": "confirm",
            "emotion": "positive"
        },
        timestamp=time.time(),
        duration=2.0
    )
    
    print("📊 输入数据:")
    print(f"   👁 眼动: {multimodal_input_2.gaze_data['state']} ({multimodal_input_2.gaze_data['duration']:.1f}s)")
    print(f"   🖐 手势: {multimodal_input_2.gesture_data['gesture']} (置信度: {multimodal_input_2.gesture_data['confidence']:.2f})")
    print(f"   🎤 语音: '{multimodal_input_2.speech_data['text']}'")
    
    print("\n🤖 正在调用DeepSeek API...")
    ai_response_2 = deepseek_client.analyze_multimodal_data(multimodal_input_2)
    
    print(f"\n🧠 AI分析结果:")
    print(f"   📋 推荐操作: {ai_response_2.recommendation_text}")
    print(f"   🎯 置信度: {ai_response_2.confidence:.2f}")
    print(f"   💭 推理过程: {ai_response_2.reasoning}")
    print(f"   ⚙️ 操作指令: {ai_response_2.action_code}")


def test_distraction_gesture_only():
    """测试仅手势确认的分心恢复"""
    print("\n" + "="*50)
    print("🖐 测试场景: 手势确认恢复")
    
    # 分心状态 + 手势确认（无语音）
    multimodal_input = MultimodalInput(
        gaze_data={
            "state": "center",  # 已回到中心
            "duration": 0.8,
            "deviation": "normal"
        },
        gesture_data={
            "gesture": "peace",  # V手势表示OK
            "confidence": 0.92,
            "intent": "ok"
        },
        speech_data={
            "text": "",  # 无语音输入
            "intent": "unknown",
            "emotion": "neutral"
        },
        timestamp=time.time(),
        duration=1.5
    )
    
    print("📊 输入数据:")
    print(f"   👁 眼动: {multimodal_input.gaze_data['state']}")
    print(f"   🖐 手势: {multimodal_input.gesture_data['gesture']} (置信度: {multimodal_input.gesture_data['confidence']:.2f})")
    print(f"   🎤 语音: '{multimodal_input.speech_data['text']}'")
    
    print("\n🤖 正在调用DeepSeek API...")
    ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
    
    print(f"\n🧠 AI分析结果:")
    print(f"   📋 推荐操作: {ai_response.recommendation_text}")
    print(f"   🎯 置信度: {ai_response.confidence:.2f}")
    print(f"   💭 推理过程: {ai_response.reasoning}")
    print(f"   ⚙️ 操作指令: {ai_response.action_code}")


def test_voice_command_scenario():
    """测试语音命令场景"""
    print("\n" + "="*50)
    print("🎤 测试场景: 语音命令")
    
    # 模拟语音命令输入
    multimodal_input = MultimodalInput(
        gaze_data={
            "state": "center",
            "duration": 1.0,
            "deviation": "normal"
        },
        gesture_data={
            "gesture": "thumbs_up",
            "confidence": 0.85,
            "intent": "confirm"
        },
        speech_data={
            "text": "导航到家",
            "intent": "navigation",
            "emotion": "neutral"
        },
        timestamp=time.time(),
        duration=2.0
    )
    
    print("📊 输入数据:")
    print(f"   👁 眼动: {multimodal_input.gaze_data['state']}")
    print(f"   🖐 手势: {multimodal_input.gesture_data['gesture']} (置信度: {multimodal_input.gesture_data['confidence']:.2f})")
    print(f"   🎤 语音: '{multimodal_input.speech_data['text']}'")
    
    print("\n🤖 正在调用DeepSeek API...")
    ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
    
    print(f"\n🧠 AI分析结果:")
    print(f"   📋 推荐操作: {ai_response.recommendation_text}")
    print(f"   🎯 置信度: {ai_response.confidence:.2f}")
    print(f"   💭 推理过程: {ai_response.reasoning}")
    print(f"   ⚙️ 操作指令: {ai_response.action_code}")


def test_emergency_scenario():
    """测试紧急情况场景"""
    print("\n" + "="*50)
    print("🚨 测试场景: 紧急情况处理")
    
    # 模拟紧急情况：长时间分心 + 无响应
    multimodal_input = MultimodalInput(
        gaze_data={
            "state": "left",  # 持续偏离
            "duration": 8.0,  # 很长时间
            "deviation": "severe"
        },
        gesture_data={
            "gesture": "none",
            "confidence": 0.0,
            "intent": "unknown"
        },
        speech_data={
            "text": "",
            "intent": "unknown",
            "emotion": "neutral"
        },
        timestamp=time.time(),
        duration=8.0
    )
    
    print("📊 输入数据:")
    print(f"   👁 眼动: {multimodal_input.gaze_data['state']} ({multimodal_input.gaze_data['duration']:.1f}s)")
    print(f"   🖐 手势: {multimodal_input.gesture_data['gesture']}")
    print(f"   🎤 语音: '{multimodal_input.speech_data['text']}'")
    
    print("\n🤖 正在调用DeepSeek API...")
    ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
    
    print(f"\n🧠 AI分析结果:")
    print(f"   📋 推荐操作: {ai_response.recommendation_text}")
    print(f"   🎯 置信度: {ai_response.confidence:.2f}")
    print(f"   💭 推理过程: {ai_response.reasoning}")
    print(f"   ⚙️ 操作指令: {ai_response.action_code}")


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 DeepSeek API 多模态融合测试 - 无TTS版本")
    print("=" * 60)
    
    try:
        # 测试完整的分心驾驶流程
        test_distraction_complete_scenario()
        
        # 等待一段时间
        time.sleep(1)
        
        # 测试仅手势确认
        test_distraction_gesture_only()
        
        # 等待一段时间
        time.sleep(1)
        
        # 测试语音命令场景
        test_voice_command_scenario()
        
        # 等待一段时间
        time.sleep(1)
        
        # 测试紧急情况
        test_emergency_scenario()
        
        print("\n" + "="*60)
        print("✅ 所有测试场景完成")
        print("📋 测试总结:")
        print("   🚨 分心检测 → 语音+手势确认 → 恢复正常")
        print("   🖐 分心检测 → 仅手势确认 → 恢复正常")
        print("   🎤 正常语音命令 → 多模态确认 → 执行操作")
        print("   🚨 紧急情况 → 长时间分心 → 升级警报")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 