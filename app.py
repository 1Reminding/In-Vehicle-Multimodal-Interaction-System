#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载多模态智能交互系统 - AI增强版

集成DeepSeek API进行智能多模态融合和语音反馈
"""

import time
import cv2
import threading
import signal
import sys
import json
from typing import Dict, Any

# 导入现有模块
from modules.audio.recorder import Recorder
from modules.audio.speech_recognizer import transcribe
from modules.vision.gesture.gesture_recognizer import GestureRecognizer
from modules.vision.head.head_pose_detector import HeadPoseDetector
from modules.vision.gaze.gaze_tracking import GazeTracking
from modules.vision.camera_manager import get_camera_manager, release_camera_manager
from modules.actions.action_handler import handle_action


# 导入AI模块
from modules.ai.deepseek_client import deepseek_client, MultimodalInput, AIResponse
from modules.ai.multimodal_collector import multimodal_collector

import os
#from PySide6.QtGui import QGuiApplication
#from PySide6.QtQml import QQmlApplicationEngine
#from PySide6.QtCore import QUrl, QObject, Signal, Slot

import requests
from PyQt5.QtGui     import QGuiApplication
from PyQt5.QtQml     import QQmlApplicationEngine
from PyQt5.QtCore   import QUrl, QObject, pyqtSignal, pyqtSlot, QTimer


class UIBackend(QObject):
    """暴露给 QML 的桥接对象"""
    commandIssued = pyqtSignal(str)

    weatherUpdated = pyqtSignal(str)

    @pyqtSlot(str)
    def requestAction(self, cmd):
        print(f"🔷 前端请求动作：{cmd}")
        handle_action(cmd)

# 实例化
ui_backend = UIBackend()

class AIMultimodalApp:
    """AI增强的多模态交互应用"""
    
    def __init__(self):
        self.running = False
        self.audio_thread = None
        self.vision_thread = None
        
        # 统计信息
        self.stats = {
            "ai_requests": 0,
            "successful_responses": 0,
            "speech_inputs": 0,
            "gesture_detections": 0,
            "gaze_changes": 0,
            "start_time": time.time()
        }
        
        # 设置多模态数据回调
        multimodal_collector.set_callback(self.on_multimodal_data_ready)
        
        print("🚀 AI多模态交互系统初始化完成")
        print("📋 功能说明:")
        print("   - 眼动偏离超过3秒触发AI分析")
        print("   - 语音输入立即触发AI分析")
        print("   - 手势识别触发AI分析")
        print("   - AI分析结果通过文本显示")
        print("   - 按 Ctrl+C 退出系统")
    
    def on_multimodal_data_ready(self, multimodal_input: MultimodalInput):
        """处理多模态数据就绪事件"""
        print(f"\n🤖 AI分析开始...")
        print(f"📊 输入数据:")
        print(f"   👁 眼动: {multimodal_input.gaze_data['state']} ({multimodal_input.gaze_data['duration']:.1f}s)")
        print(f"   🖐 手势: {multimodal_input.gesture_data['gesture']} ({multimodal_input.gesture_data['confidence']:.2f})")
        print(f"   🎤 语音: '{multimodal_input.speech_data['text']}'")
        
        # 更新统计
        self.stats["ai_requests"] += 1
        
        try:
            # 调用DeepSeek API进行分析
            ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
            
            print(f"\n🧠 AI分析结果:")
            print(f"   📋 推荐操作: {ai_response.recommendation_text}")
            print(f"   🎯 置信度: {ai_response.confidence:.2f}")
            print(f"   💭 推理过程: {ai_response.reasoning}")
            
            # 解析操作指令
            try:
                action_data = json.loads(ai_response.action_code)
                print(f"   ⚙️ 操作指令: {action_data}")
                handle_action(action_data)
                ui_backend.commandIssued.emit(action_data)

            except json.JSONDecodeError:
                print(f"   ⚙️ 操作指令: {ai_response.action_code}")       
                handle_action(ai_response.action_code)
                ui_backend.commandIssued.emit(ai_response.action_code)
       
            
            # 文本反馈（不使用TTS）
            if ai_response.recommendation_text:
                print(f"💬 系统建议: {ai_response.recommendation_text}")
            
            # 添加到对话历史
            deepseek_client.add_to_conversation_history(multimodal_input, ai_response)
            
            self.stats["successful_responses"] += 1
            
        except Exception as e:
            print(f"❌ AI分析失败: {e}")
            print("💬 系统提示: 抱歉，系统暂时无法处理您的请求")
    
    def audio_worker(self):
        """音频工作线程"""
        print("🎤 音频线程启动")
        rec = Recorder()
        
        try:
            for seg in rec.record_stream():
                if not self.running:
                    break
                
                # 语音识别
                text = transcribe(seg["wav"])
                if not text or not text.strip():
                    continue
                
                # 更新统计
                self.stats["speech_inputs"] += 1
                
                print(f"🎤 语音识别: '{text}'")
                
                # 更新多模态收集器
                speech_data = {
                    "text": text,
                }
                multimodal_collector.update_speech_data(speech_data)
                
        except Exception as e:
            print(f"❌ 音频线程错误: {e}")
        finally:
            print("🎤 音频线程结束")
    
    def vision_worker(self):
        """视觉工作线程"""
        print("👁 视觉线程启动")
        
        # 获取摄像头管理器
        camera_manager = get_camera_manager()
        
        # 初始化视觉模块
        gr = GestureRecognizer()
        hp = HeadPoseDetector()
        gaze = GazeTracking()
        
        if not camera_manager.is_opened:
            print("❌ 摄像头无法打开")
            return
        
        # 状态变量
        last_gesture = None
        last_gaze_state = None
        stable_gesture = None
        stable_start_time = None
        stability_threshold = 0.5
        
        try:
            while self.running:
                ok, frame = camera_manager.read_frame()
                if not ok:
                    time.sleep(0.01)
                    continue
                
                frame = cv2.flip(frame, 1)
                
                # 眼动追踪
                gaze.refresh(frame)
                current_gaze_state = "center"
                if gaze.is_right():
                    current_gaze_state = "right"
                elif gaze.is_left():
                    current_gaze_state = "left"
                elif gaze.is_center():
                    current_gaze_state = "center"
                
                # 眼动状态变化时更新收集器
                if current_gaze_state != last_gaze_state:
                    last_gaze_state = current_gaze_state
                    self.stats["gaze_changes"] += 1
                    
                    gaze_data = {
                        "state": current_gaze_state,
                        "ts": time.time()
                    }
                    multimodal_collector.update_gaze_data(gaze_data)
                
                # 头部姿态检测
                head_pose_result = hp.process_frame(frame)
                if head_pose_result:
                    if head_pose_result["type"] == "head_pose_calibrated":
                        print(f"🎯 头部姿态基线校准: pitch0={head_pose_result['pitch0']:.1f}°")
                    elif head_pose_result["type"] == "head_pose":
                        print(f"🗣 头部姿态: {head_pose_result}")
                
                # 手势识别
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = gr.hands.process(rgb)
                rgb.flags.writeable = True
                
                current_time = time.time()
                current_gesture = None
                current_conf = 0.0
                
                if res.multi_hand_landmarks:
                    for hlm in res.multi_hand_landmarks:
                        gesture, conf = gr._recognize_gesture(hlm)
                        if gesture:
                            current_gesture = gesture
                            current_conf = conf
                            break
                
                # 手势稳定性检测
                if current_gesture == stable_gesture:
                    if stable_start_time is not None:
                        stable_duration = current_time - stable_start_time
                        if stable_duration >= stability_threshold and current_gesture != last_gesture:
                            last_gesture = current_gesture
                            self.stats["gesture_detections"] += 1
                            
                            gesture_data = {
                                "gesture": current_gesture,
                                "conf": current_conf,
                                "ts": current_time,
                                "stable_duration": stable_duration
                            }
                            
                            print(f"🖐 手势检测: {current_gesture} (置信度: {current_conf:.2f})")
                            multimodal_collector.update_gesture_data(gesture_data)
                else:
                    stable_gesture = current_gesture
                    stable_start_time = current_time if current_gesture else None
                
        except Exception as e:
            print(f"❌ 视觉线程错误: {e}")
        finally:
            gr.hands.close()
            print("👁 视觉线程结束")
    
    def print_status(self):
        """打印系统状态"""
        runtime = time.time() - self.stats["start_time"]
        
        print(f"\n📊 系统状态 (运行时间: {runtime:.1f}秒)")
        print(f"   🤖 AI请求次数: {self.stats['ai_requests']}")
        print(f"   ✅ 成功响应: {self.stats['successful_responses']}")
        print(f"   🎤 语音输入: {self.stats['speech_inputs']}")
        print(f"   🖐 手势检测: {self.stats['gesture_detections']}")
        print(f"   👁 眼动变化: {self.stats['gaze_changes']}")
        
        # 多模态收集器状态
        collector_status = multimodal_collector.get_status()
        print(f"   📋 收集器状态: {'收集中' if collector_status['is_collecting'] else '待机'}")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🛑 接收到退出信号 ({signum})")
        self.stop()
    
    def start(self):
        """启动应用"""
        print("🚀 启动AI多模态交互系统...")
        
        # 注册信号处理器
        #signal.signal(signal.SIGINT, self.signal_handler)
        #signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        
        # 启动音频线程
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
        
        # 启动视觉线程（主线程）
        try:
            self.vision_worker()
        except KeyboardInterrupt:
            print("\n⌨️ 用户中断")
        finally:
            self.stop()
    
    def stop(self):
        """停止应用"""
        if not self.running:
            return
        
        print("🛑 正在停止AI多模态交互系统...")
        self.running = False
        
        # 等待线程结束
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        # 打印最终状态
        self.print_status()
        
        # 关闭资源
        release_camera_manager()
        
        print("✅ AI多模态交互系统已停止")


def fetch_weather(city="Tianjin"):
    #api_key = "e8527d822a260a90258bbbcf110506e8"
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tianjin&appid=e8527d822a260a90258bbbcf110506e8&units=metric&lang=zh_cn"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code == 200:
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"{round(temp)}°C {desc}"
        else:
            print("❌ 天气 API 响应失败：", data)
            return "天气加载失败"
    except Exception as e:
        print("❌ 请求天气失败：", e)
        return "天气异常"

def main():
    """主函数"""
    print("=" * 60)
    print("🚗 车载多模态智能交互系统 - AI增强版")
    print("=" * 60)
    
    # 1. 启动后端多模态服务（在后台线程）
    backend = AIMultimodalApp()
    
    signal.signal(signal.SIGINT, backend.signal_handler)
    signal.signal(signal.SIGTERM, backend.signal_handler)

    threading.Thread(target=backend.start, daemon=True).start()


    # 2. 实例化 UIBackend
    #ui_backend = UIBackend()

    # 3. 启动 QML 界面
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("UIBackend", ui_backend)

    qml_path = os.path.join(os.path.dirname(__file__), "ui", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))
    if not engine.rootObjects():
        print("❌ 无法加载 QML 界面，请检查路径或语法")
        return 1

    weather_text = fetch_weather("Tianjin")
    QTimer.singleShot(10, lambda: ui_backend.weatherUpdated.emit(weather_text))

    # 4. 进入 Qt 事件循环（阻塞）
    return app.exec_()


if __name__ == "__main__":
    main() 