#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载多模态智能交互系统 - AI增强版

集成DeepSeek API进行智能多模态融合和语音反馈
集成完整的系统管理功能：用户配置、权限管理、交互日志
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

# 导入系统管理模块
from modules.system.system_manager import system_manager
from modules.system import UserRole, SafetyContext, PermissionLevel

import os
import requests
from PyQt5.QtGui     import QGuiApplication
from PyQt5.QtQml     import QQmlApplicationEngine
from PyQt5.QtCore   import QUrl, QObject, pyqtSignal, pyqtSlot, QTimer


class UIBackend(QObject):
    """暴露给 QML 的桥接对象"""
    commandIssued = pyqtSignal(str)
    weatherUpdated = pyqtSignal(str)
    
    # 新增系统管理相关信号
    userStatusUpdated = pyqtSignal(str)  # 用户状态更新
    permissionDenied = pyqtSignal(str)   # 权限被拒绝
    systemAlert = pyqtSignal(str)        # 系统警告

    @pyqtSlot(str)
    def requestAction(self, cmd):
        print(f"🔷 前端请求动作：{cmd}")
        handle_action(cmd)
    
    @pyqtSlot(str)
    def setCurrentUser(self, user_id):
        """设置当前用户"""
        print(f"👤 切换用户：{user_id}")
        if system_manager.user_config.load_user(user_id):
            system_manager.start_session(user_id)
            self.userStatusUpdated.emit(f"用户 {user_id} 已登录")
        else:
            self.userStatusUpdated.emit(f"用户 {user_id} 不存在")
    
    @pyqtSlot(str)
    def setVehicleState(self, state):
        """设置车辆状态"""
        print(f"🚗 设置车辆状态：{state}")
        is_driving = state in ["driving", "emergency"]
        is_emergency = state == "emergency"
        
        result = system_manager.set_vehicle_state(is_driving, is_emergency)
        self.systemAlert.emit(f"车辆状态：{result['new_context']}")

# 使用基本的UI后端
ui_backend = UIBackend()

class AIMultimodalApp:
    """AI增强的多模态交互应用"""
    
    def __init__(self):
        self.running = False
        self.audio_thread = None
        self.vision_thread = None
        
        # 当前用户信息
        self.current_user_id = None
        self.current_user_role = UserRole.DRIVER  # 默认驾驶员
        
        # 统计信息
        self.stats = {
            "ai_requests": 0,
            "successful_responses": 0,
            "speech_inputs": 0,
            "gesture_detections": 0,
            "gaze_changes": 0,
            "permission_checks": 0,
            "permission_denials": 0,
            "start_time": time.time()
        }
        
        # 设置多模态数据回调
        multimodal_collector.set_callback(self.on_multimodal_data_ready)
        
        # 初始化系统管理
        self._initialize_system_management()
        
        print("🚀 AI多模态交互系统初始化完成")
        print("📋 功能说明:")
        print("   - 眼动偏离超过3秒触发AI分析")
        print("   - 语音输入立即触发AI分析")
        print("   - 手势识别触发AI分析")
        print("   - AI分析结果通过文本显示")
        print("   - 集成系统管理功能（用户配置、日志记录、权限管理）")
        print("   - 按 Ctrl+C 退出系统")
    
    def _initialize_system_management(self):
        """初始化系统管理功能"""
        try:
            # 设置默认用户（如果没有用户则创建默认驾驶员）
            default_user_id = "default_driver"
            if not system_manager.user_config.load_user(default_user_id):
                print(f"📋 创建默认用户：{default_user_id}")
                system_manager.create_user_profile(default_user_id, "默认驾驶员", "driver")
            
            # 加载默认用户并开始会话
            if system_manager.user_config.load_user(default_user_id):
                self.current_user_id = default_user_id
                self.current_user_role = UserRole.DRIVER
                system_manager.start_session(default_user_id)
                print(f"✅ 系统管理初始化完成，当前用户：{default_user_id}")
            else:
                print("⚠️ 无法加载默认用户，系统将以访客模式运行")
                
        except Exception as e:
            print(f"❌ 系统管理初始化失败：{e}")
            print("⚠️ 系统将以基础模式运行，部分功能可能受限")
    
    def _check_interaction_permission(self, interaction_category: str) -> tuple[bool, str]:
        """检查交互权限"""
        if not self.current_user_id:
            return False, "未登录用户"
        
        self.stats["permission_checks"] += 1
        
        # 检查权限
        permission = system_manager.permission.check_permission(
            self.current_user_role, 
            interaction_category, 
            PermissionLevel.WRITE
        )
        
        if not permission:
            self.stats["permission_denials"] += 1
            
            # 获取当前安全上下文
            current_context = system_manager.permission.safety_context
            context_name = {
                SafetyContext.PARKED: "停车",
                SafetyContext.DRIVING: "行驶", 
                SafetyContext.EMERGENCY: "紧急"
            }.get(current_context, "未知")
            
            role_name = "驾驶员" if self.current_user_role == UserRole.DRIVER else "乘客"
            
            denial_message = f"{role_name}在{context_name}状态下无权限执行{interaction_category}操作"
            
            # 发送权限拒绝信号到UI
            ui_backend.permissionDenied.emit(denial_message)
            
            return False, denial_message
        
        return True, "权限验证通过"
    
    def _get_personalized_settings(self) -> Dict[str, Any]:
        """获取个性化设置"""
        if not self.current_user_id:
            return {}
        
        try:
            # 获取用户交互统计
            user_stats = system_manager.user_config.get_interaction_stats()
            
            # 获取用户偏好（使用get_preference方法）
            voice_speed = system_manager.user_config.get_preference('accessibility.voice_speed', 1.0)
            brief_responses = system_manager.user_config.get_preference('ui_preferences.brief_responses', False)
            
            return {
                "interaction_stats": user_stats,
                "preferences": {
                    "voice_speed": voice_speed,
                    "brief_responses": brief_responses
                },
                "most_used_gesture": user_stats.get("most_used_gesture"),
                "most_used_voice_command": user_stats.get("most_used_voice_command"),
                "preferred_response_speed": voice_speed
            }
        except Exception as e:
            print(f"⚠️ 获取个性化设置失败：{e}")
            return {}

    def on_multimodal_data_ready(self, multimodal_input: MultimodalInput):
        """处理多模态数据就绪事件"""
        print(f"\n🤖 AI分析开始...")
        print(f"📊 输入数据:")
        print(f"   👁 眼动: {multimodal_input.gaze_data['state']} ({multimodal_input.gaze_data['duration']:.1f}s)")
        print(f"   🖐 手势: {multimodal_input.gesture_data['gesture']} ({multimodal_input.gesture_data['confidence']:.2f})")
        print(f"   🎤 语音: '{multimodal_input.speech_data['text']}'")
        
        # 确定交互类别
        interaction_category = self._get_interaction_category(multimodal_input)
        
        # 权限检查
        permission_granted, permission_message = self._check_interaction_permission(interaction_category)
        
        if not permission_granted:
            print(f"🚫 权限被拒绝：{permission_message}")
            
            # 记录权限拒绝的交互
            interaction_data = {
                "modality": "multimodal",
                "type": "permission_denied",
                "category": interaction_category,
                "gaze_data": multimodal_input.gaze_data,
                "gesture_data": multimodal_input.gesture_data,
                "speech_data": multimodal_input.speech_data,
                "user_id": self.current_user_id,
                "user_role": self.current_user_role.value
            }
            
            system_manager.process_multimodal_interaction(
                interaction_data=interaction_data,
                processing_time=0.1,
                success=False,
                error_message=permission_message
            )
            
            return
        
        # 获取个性化设置
        personalized_settings = self._get_personalized_settings()
        
        # 更新统计
        self.stats["ai_requests"] += 1
        start_time = time.time()
        
        try:
            # 调用DeepSeek API进行分析
            ai_response = deepseek_client.analyze_multimodal_data(multimodal_input)
            processing_time = time.time() - start_time
            
            print(f"\n🧠 AI分析结果:")
            print(f"   📋 推荐操作: {ai_response.recommendation_text}")
            print(f"   🎯 置信度: {ai_response.confidence:.2f}")
            print(f"   💭 推理过程: {ai_response.reasoning}")
            
            # 解析操作指令
            try:
                action_data = json.loads(ai_response.action_code)
                print(f"   ⚙️ 操作指令: {action_data}")
            except json.JSONDecodeError:
                print(f"   ⚙️ 操作指令: {ai_response.action_code}")
            
            # 通过系统管理器处理交互
            interaction_data = {
                "modality": "multimodal",
                "type": "ai_analysis",
                "category": interaction_category,
                "gaze_data": multimodal_input.gaze_data,
                "gesture_data": multimodal_input.gesture_data,
                "speech_data": multimodal_input.speech_data,
                "user_id": self.current_user_id,
                "user_role": self.current_user_role.value,
                "personalized_settings": personalized_settings
            }
            
            ai_response_data = {
                "confidence": ai_response.confidence,
                "recommendation": ai_response.recommendation_text,
                "reasoning": ai_response.reasoning,
                "action_code": ai_response.action_code
            }
            
            system_result = system_manager.process_multimodal_interaction(
                interaction_data=interaction_data,
                ai_response=ai_response_data,
                processing_time=processing_time,
                success=True
            )
            
            if system_result["success"]:
                print(f"✅ 交互记录成功 - 会话ID: {system_result.get('session_id')}")
                
                # 解析操作指令并执行
                try:
                    action_data = json.loads(ai_response.action_code)
                    print(f"   ⚙️ 执行操作: {action_data}")
                    handle_action(action_data)
                    ui_backend.commandIssued.emit(json.dumps(action_data))

                except json.JSONDecodeError:
                    print(f"   ⚙️ 执行操作: {ai_response.action_code}")       
                    handle_action(ai_response.action_code)
                    ui_backend.commandIssued.emit(ai_response.action_code)
                
                # 文本反馈（根据个性化设置调整）
                if ai_response.recommendation_text:
                    feedback_text = ai_response.recommendation_text
                    
                    # 根据用户偏好调整反馈
                    if personalized_settings.get("preferences", {}).get("brief_responses", False):
                        feedback_text = feedback_text[:50] + "..." if len(feedback_text) > 50 else feedback_text
                    
                    print(f"💬 系统建议: {feedback_text}")
                
                # 添加到对话历史
                deepseek_client.add_to_conversation_history(multimodal_input, ai_response)
                
                self.stats["successful_responses"] += 1
            else:
                print(f"🚫 {system_result['message']}")
                if system_result.get("suggestions"):
                    print(f"💡 建议: {', '.join(system_result['suggestions'])}")
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ AI分析失败: {e}")
            print("💬 系统提示: 抱歉，系统暂时无法处理您的请求")
            
            # 记录错误到系统管理器
            interaction_data = {
                "modality": "multimodal",
                "type": "ai_analysis_error",
                "category": interaction_category,
                "error": str(e),
                "user_id": self.current_user_id,
                "user_role": self.current_user_role.value if self.current_user_role else None
            }
            
            system_manager.process_multimodal_interaction(
                interaction_data=interaction_data,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _get_interaction_category(self, multimodal_input: MultimodalInput) -> str:
        """根据多模态输入推断交互类别"""
        text = multimodal_input.speech_data.get('text', '').lower()
        
        if any(word in text for word in ['导航', '目的地', '路线', '地图']):
            return 'navigation'
        elif any(word in text for word in ['音乐', '歌曲', '播放', '暂停']):
            return 'music'
        elif any(word in text for word in ['温度', '空调', '暖气', '制冷']):
            return 'climate'
        elif any(word in text for word in ['电话', '通话', '联系', '短信']):
            return 'communication'
        elif any(word in text for word in ['设置', '配置', '偏好']):
            return 'settings'
        else:
            return 'system'
    
    def switch_user(self, user_id: str) -> bool:
        """切换用户"""
        try:
            # 结束当前会话
            if self.current_user_id:
                system_manager.end_session()
            
            # 加载新用户
            if system_manager.user_config.load_user(user_id):
                self.current_user_id = user_id
                
                # 获取用户角色
                user_role = system_manager.user_config.get_user_role()
                self.current_user_role = UserRole.DRIVER if user_role == "driver" else UserRole.PASSENGER
                
                # 开始新会话
                system_manager.start_session(user_id)
                
                print(f"✅ 用户切换成功：{user_id} ({self.current_user_role.value})")
                ui_backend.userStatusUpdated.emit(f"当前用户：{user_id}")
                
                return True
            else:
                print(f"❌ 用户不存在：{user_id}")
                ui_backend.userStatusUpdated.emit(f"用户 {user_id} 不存在")
                return False
                
        except Exception as e:
            print(f"❌ 用户切换失败：{e}")
            ui_backend.userStatusUpdated.emit(f"用户切换失败：{e}")
            return False
    
    def set_vehicle_state(self, is_driving: bool, is_emergency: bool = False):
        """设置车辆状态"""
        try:
            result = system_manager.set_vehicle_state(is_driving, is_emergency)
            
            state_name = {
                SafetyContext.PARKED: "停车",
                SafetyContext.DRIVING: "行驶",
                SafetyContext.EMERGENCY: "紧急"
            }.get(result["new_context"], "未知")
            
            print(f"🚗 车辆状态更新：{state_name}")
            ui_backend.systemAlert.emit(f"车辆状态：{state_name}")
            
            # 显示安全限制
            restrictions = result.get("restrictions", {})
            if restrictions.get("restricted_actions"):
                print(f"🔒 受限操作：{', '.join(restrictions['restricted_actions'])}")
            
            return result
            
        except Exception as e:
            print(f"❌ 车辆状态设置失败：{e}")
            ui_backend.systemAlert.emit(f"状态设置失败：{e}")
            return None
    
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
        print(f"   🔒 权限检查: {self.stats['permission_checks']}")
        print(f"   🚫 权限拒绝: {self.stats['permission_denials']}")
        
        # 多模态收集器状态
        collector_status = multimodal_collector.get_status()
        print(f"   📋 收集器状态: {'收集中' if collector_status['is_collecting'] else '待机'}")
        
        # 系统管理状态
        if self.current_user_id:
            print(f"   👤 当前用户: {self.current_user_id} ({self.current_user_role.value})")
            
            # 获取系统管理统计
            try:
                system_analytics = system_manager.get_system_analytics(days=1)
                print(f"   📈 今日交互: {system_analytics.get('total_interactions', 0)} 次")
                print(f"   📊 成功率: {system_analytics.get('success_rate', 0):.1%}")
                
                # 权限使用统计
                permission_stats = system_manager.permission.get_permission_report(days=1)
                print(f"   🔐 权限检查: {permission_stats.get('total_checks', 0)} 次")
                print(f"   ⛔ 权限拒绝: {permission_stats.get('denied_requests', 0)} 次")
                
            except Exception as e:
                print(f"   ⚠️ 系统管理统计获取失败: {e}")
        else:
            print(f"   👤 当前用户: 未登录")
    
    def get_system_dashboard(self) -> Dict[str, Any]:
        """获取系统控制面板信息"""
        try:
            if not self.current_user_id:
                return {
                    "user_info": {"status": "未登录"},
                    "system_status": {"message": "请先登录用户"},
                    "stats": self.stats
                }
            
            # 获取系统管理器的控制面板
            dashboard = system_manager.get_user_dashboard()
            
            # 添加应用层统计
            dashboard["app_stats"] = self.stats
            dashboard["runtime"] = time.time() - self.stats["start_time"]
            
            return dashboard
            
        except Exception as e:
            print(f"⚠️ 获取系统控制面板失败: {e}")
            return {
                "error": str(e),
                "stats": self.stats
            }
    
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
        
        # 结束系统管理会话
        try:
            if self.current_user_id:
                system_manager.end_session()
                print(f"📋 用户会话已结束: {self.current_user_id}")
        except Exception as e:
            print(f"⚠️ 结束会话时出错: {e}")
        
        # 打印最终状态和系统分析
        self.print_status()
        
        # 显示系统管理总结
        try:
            print(f"\n📈 系统管理总结:")
            analytics = system_manager.get_system_analytics(days=1)
            print(f"   📊 今日总交互: {analytics.get('total_interactions', 0)} 次")
            print(f"   ✅ 成功率: {analytics.get('success_rate', 0):.1%}")
            print(f"   ⏱️ 平均响应时间: {analytics.get('avg_response_time', 0):.2f}秒")
            
            # 用户行为分析
            if self.current_user_id:
                user_stats = system_manager.user_config.get_interaction_stats()
                print(f"   🖐 最常用手势: {user_stats.get('most_used_gesture', 'none')}")
                print(f"   🎤 最常用语音指令: {user_stats.get('most_used_voice_command', 'none')}")
                
        except Exception as e:
            print(f"⚠️ 系统管理总结获取失败: {e}")
        
        # 关闭资源
        release_camera_manager()
        
        print("✅ AI多模态交互系统已停止")


# 全局应用实例，用于UI交互
app_instance = None

def get_app_instance():
    """获取应用实例"""
    global app_instance
    return app_instance

# 为UI提供的系统管理接口
class SystemManagementAPI:
    """系统管理API，供UI调用"""
    
    @staticmethod
    def get_current_user():
        """获取当前用户信息"""
        app = get_app_instance()
        if app and app.current_user_id:
            try:
                user_role = system_manager.user_config.get_user_role()
                user_name = system_manager.user_config.get_preference('user_info.name', '未知')
                last_login = system_manager.user_config.get_preference('user_info.last_login', '未知')
                
                return {
                    "user_id": app.current_user_id,
                    "role": app.current_user_role.value,
                    "name": user_name,
                    "last_login": last_login
                }
            except:
                return None
        return None
    
    @staticmethod
    def get_system_status():
        """获取系统状态"""
        app = get_app_instance()
        if app:
            return app.get_system_dashboard()
        return {"error": "应用未初始化"}
    
    @staticmethod
    def switch_user(user_id: str):
        """切换用户"""
        app = get_app_instance()
        if app:
            return app.switch_user(user_id)
        return False
    
    @staticmethod
    def set_vehicle_state(state: str):
        """设置车辆状态"""
        app = get_app_instance()
        if app:
            is_driving = state in ["driving", "emergency"]
            is_emergency = state == "emergency"
            return app.set_vehicle_state(is_driving, is_emergency)
        return None
    
    @staticmethod
    def get_interaction_stats(days: int = 7):
        """获取交互统计"""
        try:
            return system_manager.logger.get_interaction_stats(days=days)
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_permission_report(days: int = 7):
        """获取权限报告"""
        try:
            return system_manager.permission.get_permission_report(days=days)
        except Exception as e:
            return {"error": str(e)}

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
    global app_instance
    
    print("=" * 60)
    print("🚗 车载多模态智能交互系统 - AI增强版")
    print("🔧 集成系统管理功能：用户配置、权限管理、交互日志")
    print("=" * 60)
    
    # 1. 启动后端多模态服务（在后台线程）
    backend = AIMultimodalApp()
    app_instance = backend  # 设置全局实例
    
    signal.signal(signal.SIGINT, backend.signal_handler)
    signal.signal(signal.SIGTERM, backend.signal_handler)

    threading.Thread(target=backend.start, daemon=True).start()

    # 2. 启动 QML 界面
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    # 注册系统管理API到QML上下文
    engine.rootContext().setContextProperty("UIBackend", ui_backend)
    engine.rootContext().setContextProperty("SystemAPI", SystemManagementAPI)

    qml_path = os.path.join(os.path.dirname(__file__), "ui", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))
    if not engine.rootObjects():
        print("❌ 无法加载 QML 界面，请检查路径或语法")
        return 1

    # 3. 初始化界面数据
    weather_text = fetch_weather("Tianjin")
    QTimer.singleShot(10, lambda: ui_backend.weatherUpdated.emit(weather_text))
    
    print("🎛️ 系统管理功能已集成到应用")

    # 4. 进入 Qt 事件循环（阻塞）
    try:
        return app.exec_()
    except KeyboardInterrupt:
        print("\n⌨️ 用户中断，正在退出...")
        backend.stop()
        return 0
    finally:
        # 确保清理资源
        if app_instance:
            app_instance.stop()


if __name__ == "__main__":
    main() 