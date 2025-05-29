# -*- coding: utf-8 -*-
"""
系统管理器主模块

整合用户个性化配置、交互日志记录和权限管理功能
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .user_config import user_config_manager, UserConfigManager
from .interaction_logger import interaction_logger, InteractionLogger
from .permission_manager import permission_manager, PermissionManager, UserRole, SafetyContext, PermissionLevel


class SystemManager:
    """系统管理器主类"""
    
    def __init__(self):
        self.user_config = user_config_manager
        self.logger = interaction_logger
        self.permission = permission_manager
        
        # 当前会话信息
        self.current_session_id = None
        self.session_start_time = None
        
        print("🎛️ 系统管理器初始化完成")
    
    def start_session(self, user_id: str = None) -> str:
        """开始新的用户会话"""
        self.current_session_id = str(uuid.uuid4())
        self.session_start_time = time.time()
        
        # 如果指定了用户ID，加载用户配置
        if user_id:
            if self.user_config.load_user(user_id):
                # 根据用户角色设置初始安全上下文
                user_role = self.user_config.get_user_role()
                print(f"📋 用户会话开始: {self.user_config.user_config['user_info']['name']} ({user_role})")
                
                # 记录会话开始
                self.logger.log_user_behavior(
                    behavior_type="session_start",
                    behavior_data={
                        "user_role": user_role,
                        "session_id": self.current_session_id
                    },
                    user_id=user_id,
                    session_id=self.current_session_id
                )
            else:
                print(f"⚠️ 无法加载用户配置: {user_id}，使用默认设置")
        else:
            print("📋 匿名会话开始")
        
        return self.current_session_id
    
    def end_session(self):
        """结束当前会话"""
        if self.current_session_id:
            session_duration = time.time() - self.session_start_time
            
            # 记录会话结束
            if self.user_config.current_user:
                self.logger.log_user_behavior(
                    behavior_type="session_end",
                    behavior_data={
                        "duration": session_duration,
                        "session_id": self.current_session_id
                    },
                    user_id=self.user_config.current_user,
                    session_id=self.current_session_id
                )
            
            print(f"📋 会话结束，持续时间: {session_duration:.1f}秒")
            
            self.current_session_id = None
            self.session_start_time = None
    
    def process_multimodal_interaction(self, 
                                     interaction_data: Dict[str, Any],
                                     ai_response: Optional[Dict[str, Any]] = None,
                                     processing_time: Optional[float] = None,
                                     success: bool = True,
                                     error_message: Optional[str] = None) -> Dict[str, Any]:
        """处理多模态交互，整合日志记录和权限检查"""
        
        # 获取当前用户角色
        current_user_role = UserRole.PASSENGER  # 默认为乘客
        if self.user_config.current_user:
            role_str = self.user_config.get_user_role()
            current_user_role = UserRole(role_str) if role_str in [r.value for r in UserRole] else UserRole.PASSENGER
        
        # 提取交互信息
        modality = interaction_data.get("modality", "unknown")
        interaction_type = interaction_data.get("type", "unknown")
        category = interaction_data.get("category", "system")
        
        # 权限验证
        validation_result = self.permission.validate_action(current_user_role, {
            "type": interaction_type,
            "category": category
        })
        
        if not validation_result["allowed"]:
            # 记录权限拒绝
            self.logger.log_interaction(
                interaction_type=interaction_type,
                modality=modality,
                input_data=interaction_data,
                user_id=self.user_config.current_user,
                session_id=self.current_session_id,
                success=False,
                error_message=f"权限拒绝: {validation_result['reason']}"
            )
            
            return {
                "success": False,
                "message": validation_result["reason"],
                "suggestions": validation_result.get("alternative_suggestions", []),
                "safety_warning": validation_result.get("safety_warning", "")
            }
        
        # 记录成功的交互
        self.logger.log_interaction(
            interaction_type=interaction_type,
            modality=modality,
            input_data=interaction_data,
            ai_response=ai_response,
            user_id=self.user_config.current_user,
            session_id=self.current_session_id,
            processing_time=processing_time,
            success=success,
            error_message=error_message
        )
        
        # 更新用户交互模式
        if self.user_config.current_user and success:
            if modality == "voice" and "text" in interaction_data:
                self.user_config.update_interaction_pattern("voice", interaction_data["text"])
                # 添加到常用指令
                if category in self.user_config.user_config.get("common_commands", {}):
                    self.user_config.add_common_command(category, interaction_data["text"])
            
            elif modality == "gesture" and "gesture" in interaction_data:
                self.user_config.update_interaction_pattern("gesture", interaction_data["gesture"])
        
        # 记录性能指标
        if processing_time:
            self.logger.log_performance_metric(
                metric_name=f"{modality}_processing_time",
                metric_value=processing_time,
                user_id=self.user_config.current_user,
                session_id=self.current_session_id
            )
        
        return {
            "success": True,
            "message": "交互处理成功",
            "user_role": current_user_role.value,
            "safety_context": self.permission.current_safety_context.value
        }
    
    def set_vehicle_state(self, is_driving: bool, is_emergency: bool = False):
        """设置车辆状态，自动调整安全上下文"""
        if is_emergency:
            new_context = SafetyContext.EMERGENCY
        elif is_driving:
            new_context = SafetyContext.DRIVING
        else:
            new_context = SafetyContext.PARKED
        
        old_context = self.permission.current_safety_context
        self.permission.set_safety_context(new_context)
        
        # 记录状态变更
        if self.user_config.current_user:
            self.logger.log_user_behavior(
                behavior_type="vehicle_state_change",
                behavior_data={
                    "old_context": old_context.value,
                    "new_context": new_context.value,
                    "is_driving": is_driving,
                    "is_emergency": is_emergency
                },
                user_id=self.user_config.current_user,
                session_id=self.current_session_id
            )
        
        return {
            "old_context": old_context.value,
            "new_context": new_context.value,
            "restrictions": self.permission.get_safety_restrictions()
        }
    
    def get_user_dashboard(self) -> Dict[str, Any]:
        """获取用户控制面板信息"""
        print("📊 开始构建用户控制面板...")
        dashboard = {
            "user_info": {},
            "permissions": {},
            "interaction_stats": {},
            "common_commands": {},
            "system_status": {}
        }
        
        # 用户信息
        if self.user_config.current_user:
            print("👤 获取用户信息...")
            dashboard["user_info"] = {
                "user_id": self.user_config.current_user,
                "name": self.user_config.get_preference("user_info.name", "未知用户"),
                "role": self.user_config.get_user_role(),
                "last_login": self.user_config.get_preference("user_info.last_login", ""),
                "interaction_preferences": self.user_config.get_preference("interaction_preferences", {})
            }
            print("✅ 用户信息获取完成")
            
            # 获取用户常用指令
            print("📝 获取用户常用指令...")
            dashboard["common_commands"] = self.user_config.get_common_commands()
            print("✅ 常用指令获取完成")
            
            # 获取用户交互统计
            print("📈 获取用户交互统计...")
            dashboard["interaction_stats"] = self.user_config.get_interaction_stats()
            print("✅ 交互统计获取完成")
            
            # 获取用户权限
            print("🔒 获取用户权限...")
            user_role = UserRole(self.user_config.get_user_role())
            dashboard["permissions"] = self.permission.get_allowed_actions(user_role)
            print("✅ 用户权限获取完成")
        
        # 系统状态
        print("🎛️ 获取系统状态...")
        dashboard["system_status"] = {
            "safety_context": self.permission.current_safety_context.value,
            "session_id": self.current_session_id,
            "session_duration": time.time() - self.session_start_time if self.session_start_time else 0,
            "safety_restrictions": self.permission.get_safety_restrictions()
        }
        print("✅ 系统状态获取完成")
        
        print("📊 用户控制面板构建完成")
        return dashboard
    
    def get_system_analytics(self, days: int = 7) -> Dict[str, Any]:
        """获取系统分析报告"""
        analytics = {}
        
        # 交互统计
        if self.user_config.current_user:
            analytics["user_stats"] = self.logger.get_interaction_stats(
                user_id=self.user_config.current_user, 
                days=days
            )
            analytics["user_behavior"] = self.logger.get_user_behavior_analysis(
                user_id=self.user_config.current_user,
                days=days
            )
        
        # 全局统计
        analytics["global_stats"] = self.logger.get_interaction_stats(days=days)
        
        # 错误分析
        analytics["error_analysis"] = self.logger.get_error_analysis(days=days)
        
        # 权限报告
        analytics["permission_report"] = self.permission.get_permission_report(days=days)
        
        return analytics
    
    def update_user_preference(self, key: str, value: Any) -> bool:
        """更新用户偏好设置"""
        if not self.user_config.current_user:
            return False
        
        result = self.user_config.set_preference(key, value)
        
        if result:
            # 记录偏好更新
            self.logger.log_user_behavior(
                behavior_type="preference_update",
                behavior_data={
                    "key": key,
                    "value": value
                },
                user_id=self.user_config.current_user,
                session_id=self.current_session_id
            )
        
        return result
    
    def create_user_profile(self, user_id: str, name: str, role: str = "driver") -> bool:
        """创建新的用户档案"""
        success = self.user_config.create_user(user_id, name, role)
        
        if success:
            # 记录用户创建
            self.logger.log_user_behavior(
                behavior_type="user_created",
                behavior_data={
                    "name": name,
                    "role": role
                },
                user_id=user_id
            )
        
        return success
    
    def export_user_data(self, output_dir: str = "data/exports") -> Dict[str, str]:
        """导出用户数据"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        exported_files = {}
        
        if self.user_config.current_user:
            user_id = self.user_config.current_user
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 导出交互日志
            log_file = os.path.join(output_dir, f"logs_{user_id}_{timestamp}.json")
            if self.logger.export_logs(log_file, user_id=user_id, days=30):
                exported_files["logs"] = log_file
            
            # 导出用户配置
            config_file = os.path.join(output_dir, f"config_{user_id}_{timestamp}.json")
            import json
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.user_config.user_config, f, ensure_ascii=False, indent=2)
                exported_files["config"] = config_file
            except Exception as e:
                print(f"❌ 导出用户配置失败: {e}")
            
            # 导出系统分析
            analytics_file = os.path.join(output_dir, f"analytics_{user_id}_{timestamp}.json")
            try:
                analytics = self.get_system_analytics(days=30)
                with open(analytics_file, 'w', encoding='utf-8') as f:
                    json.dump(analytics, f, ensure_ascii=False, indent=2)
                exported_files["analytics"] = analytics_file
            except Exception as e:
                print(f"❌ 导出系统分析失败: {e}")
        
        return exported_files
    
    def cleanup_system(self, keep_days: int = 90):
        """清理系统数据"""
        # 清理旧日志
        self.logger.cleanup_old_logs(keep_days)
        
        # 清理权限历史记录
        if len(self.permission.permission_history) > 1000:
            self.permission.permission_history = self.permission.permission_history[-1000:]
        
        print(f"🧹 系统清理完成，保留 {keep_days} 天数据")


# 全局系统管理器实例 - 使用延迟初始化
_system_manager_instance = None

def get_system_manager():
    """获取系统管理器实例（延迟初始化）"""
    global _system_manager_instance
    if _system_manager_instance is None:
        _system_manager_instance = SystemManager()
    return _system_manager_instance

# 为了保持向后兼容性，提供一个属性访问器
class SystemManagerProxy:
    def __getattr__(self, name):
        return getattr(get_system_manager(), name)

system_manager = SystemManagerProxy() 