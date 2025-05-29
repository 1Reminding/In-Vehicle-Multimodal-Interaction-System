# -*- coding: utf-8 -*-
"""
系统权限管理器

实现系统权限管理，区分驾驶员与乘客的操作权限，确保安全
"""

import json
import os
from typing import Dict, Any, List, Set, Optional
from datetime import datetime
from enum import Enum
import threading


class UserRole(Enum):
    """用户角色枚举"""
    DRIVER = "driver"
    PASSENGER = "passenger"
    ADMIN = "admin"


class PermissionLevel(Enum):
    """权限级别枚举"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


class SafetyContext(Enum):
    """安全上下文枚举"""
    PARKED = "parked"          # 停车状态
    DRIVING = "driving"        # 行驶状态
    EMERGENCY = "emergency"    # 紧急状态


class PermissionManager:
    """系统权限管理器"""
    
    def __init__(self, config_file: str = "data/permissions.json"):
        self.config_file = config_file
        self.lock = threading.Lock()
        
        # 当前安全上下文
        self.current_safety_context = SafetyContext.PARKED
        
        # 默认权限配置
        self.default_permissions = {
            "navigation": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.READ.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.ADMIN.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.NONE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.READ.value
                }
            },
            "music": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.WRITE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.WRITE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                }
            },
            "climate": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.WRITE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.READ.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.WRITE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                }
            },
            "communication": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.READ.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.ADMIN.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.NONE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.WRITE.value
                }
            },
            "system_settings": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.NONE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.READ.value,
                    SafetyContext.DRIVING.value: PermissionLevel.NONE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                }
            },
            "voice_control": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.ADMIN.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.ADMIN.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.READ.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.WRITE.value
                }
            },
            "gesture_control": {
                UserRole.DRIVER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.ADMIN.value,
                    SafetyContext.DRIVING.value: PermissionLevel.WRITE.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.WRITE.value
                },
                UserRole.PASSENGER.value: {
                    SafetyContext.PARKED.value: PermissionLevel.WRITE.value,
                    SafetyContext.DRIVING.value: PermissionLevel.READ.value,
                    SafetyContext.EMERGENCY.value: PermissionLevel.NONE.value
                }
            }
        }
        
        # 加载权限配置
        self.permissions = self._load_permissions()
        
        # 权限检查历史记录
        self.permission_history = []
        
        print("🔒 权限管理器初始化完成")
    
    def _load_permissions(self) -> Dict[str, Any]:
        """加载权限配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 使用默认配置并保存
                self._save_permissions(self.default_permissions)
                return self.default_permissions.copy()
        except Exception as e:
            print(f"❌ 加载权限配置失败: {e}")
            return self.default_permissions.copy()
    
    def _save_permissions(self, permissions: Dict[str, Any]):
        """保存权限配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(permissions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存权限配置失败: {e}")
    
    def set_safety_context(self, context: SafetyContext):
        """设置当前安全上下文"""
        with self.lock:
            old_context = self.current_safety_context
            self.current_safety_context = context
            
            print(f"🚗 安全上下文变更: {old_context.value} -> {context.value}")
            
            # 记录上下文变更
            self.permission_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "context_change",
                "old_context": old_context.value,
                "new_context": context.value
            })
    
    def check_permission(self, 
                        user_role: UserRole, 
                        resource: str, 
                        required_level: PermissionLevel) -> bool:
        """检查用户权限"""
        try:
            with self.lock:
                # 获取当前权限级别
                current_level = self._get_permission_level(user_role, resource)
                
                # 权限检查结果
                has_permission = current_level.value >= required_level.value
                
                # 记录权限检查
                self.permission_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "permission_check",
                    "user_role": user_role.value,
                    "resource": resource,
                    "required_level": required_level.value,
                    "current_level": current_level.value,
                    "safety_context": self.current_safety_context.value,
                    "result": has_permission
                })
                
                # 只保留最近1000条记录
                if len(self.permission_history) > 1000:
                    self.permission_history = self.permission_history[-1000:]
                
                if not has_permission:
                    print(f"🚫 权限拒绝: {user_role.value} 用户无法执行 {resource} 操作 "
                          f"(需要: {required_level.name}, 当前: {current_level.name})")
                
                return has_permission
                
        except Exception as e:
            print(f"❌ 权限检查失败: {e}")
            return False
    
    def _get_permission_level(self, user_role: UserRole, resource: str) -> PermissionLevel:
        """获取用户对资源的权限级别"""
        try:
            resource_permissions = self.permissions.get(resource, {})
            role_permissions = resource_permissions.get(user_role.value, {})
            level_value = role_permissions.get(self.current_safety_context.value, 0)
            return PermissionLevel(level_value)
        except (KeyError, ValueError):
            return PermissionLevel.NONE
    
    def can_execute_command(self, user_role: UserRole, command_category: str) -> bool:
        """检查用户是否可以执行指定类别的命令"""
        return self.check_permission(user_role, command_category, PermissionLevel.WRITE)
    
    def can_read_data(self, user_role: UserRole, data_category: str) -> bool:
        """检查用户是否可以读取指定类别的数据"""
        return self.check_permission(user_role, data_category, PermissionLevel.READ)
    
    def can_modify_settings(self, user_role: UserRole, setting_category: str) -> bool:
        """检查用户是否可以修改设置"""
        return self.check_permission(user_role, setting_category, PermissionLevel.ADMIN)
    
    def get_allowed_actions(self, user_role: UserRole) -> Dict[str, List[str]]:
        """获取用户在当前安全上下文下允许的操作"""
        allowed_actions = {
            "read": [],
            "write": [],
            "admin": []
        }
        
        for resource in self.permissions.keys():
            level = self._get_permission_level(user_role, resource)
            
            if level.value >= PermissionLevel.READ.value:
                allowed_actions["read"].append(resource)
            if level.value >= PermissionLevel.WRITE.value:
                allowed_actions["write"].append(resource)
            if level.value >= PermissionLevel.ADMIN.value:
                allowed_actions["admin"].append(resource)
        
        return allowed_actions
    
    def get_safety_restrictions(self) -> Dict[str, Any]:
        """获取当前安全上下文的限制信息"""
        restrictions = {
            "current_context": self.current_safety_context.value,
            "restricted_actions": [],
            "allowed_modalities": [],
            "safety_notes": []
        }
        
        if self.current_safety_context == SafetyContext.DRIVING:
            restrictions["restricted_actions"] = [
                "系统设置修改",
                "复杂导航输入",
                "文字输入",
                "视频播放"
            ]
            restrictions["allowed_modalities"] = ["voice", "simple_gesture"]
            restrictions["safety_notes"] = [
                "行驶中优先保证驾驶安全",
                "建议使用语音控制",
                "复杂操作请在停车后进行"
            ]
        elif self.current_safety_context == SafetyContext.EMERGENCY:
            restrictions["restricted_actions"] = [
                "娱乐功能",
                "非必要设置",
                "游戏功能"
            ]
            restrictions["allowed_modalities"] = ["voice", "gesture"]
            restrictions["safety_notes"] = [
                "紧急状态，只允许必要操作",
                "导航和通讯功能优先",
                "其他功能暂时限制"
            ]
        else:  # PARKED
            restrictions["allowed_modalities"] = ["voice", "gesture", "touch", "gaze"]
            restrictions["safety_notes"] = [
                "停车状态，所有功能可用",
                "可以进行系统设置和个性化配置"
            ]
        
        return restrictions
    
    def update_permission(self, 
                         resource: str, 
                         user_role: UserRole, 
                         safety_context: SafetyContext, 
                         permission_level: PermissionLevel) -> bool:
        """更新权限配置（需要管理员权限）"""
        try:
            with self.lock:
                if resource not in self.permissions:
                    self.permissions[resource] = {}
                
                if user_role.value not in self.permissions[resource]:
                    self.permissions[resource][user_role.value] = {}
                
                self.permissions[resource][user_role.value][safety_context.value] = permission_level.value
                
                # 保存更新
                self._save_permissions(self.permissions)
                
                print(f"⚙️ 已更新权限: {resource}.{user_role.value}.{safety_context.value} = {permission_level.name}")
                
                # 记录权限修改
                self.permission_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "permission_update",
                    "resource": resource,
                    "user_role": user_role.value,
                    "safety_context": safety_context.value,
                    "new_level": permission_level.value
                })
                
                return True
                
        except Exception as e:
            print(f"❌ 更新权限失败: {e}")
            return False
    
    def get_permission_report(self, days: int = 7) -> Dict[str, Any]:
        """获取权限使用报告"""
        try:
            print(f"🔒 开始生成权限使用报告 (天数: {days})...")
            
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(days=days)
            print(f"🔒 筛选 {cutoff_time.isoformat()} 之后的权限记录...")
            
            recent_history = [
                record for record in self.permission_history
                if datetime.fromisoformat(record["timestamp"]) >= cutoff_time
            ]
            
            print(f"🔒 找到 {len(recent_history)} 条最近的权限记录")
            
            # 统计权限检查次数
            permission_checks = [r for r in recent_history if r["action"] == "permission_check"]
            print(f"🔒 其中权限检查记录: {len(permission_checks)} 条")
            
            # 拒绝统计
            denied_requests = [r for r in permission_checks if not r["result"]]
            print(f"🔒 被拒绝的请求: {len(denied_requests)} 条")
            
            # 按资源分组的访问统计
            resource_access = {}
            for record in permission_checks:
                resource = record["resource"]
                if resource not in resource_access:
                    resource_access[resource] = {"total": 0, "denied": 0}
                resource_access[resource]["total"] += 1
                if not record["result"]:
                    resource_access[resource]["denied"] += 1
            
            print(f"🔒 资源访问统计: {len(resource_access)} 种资源")
            
            # 安全上下文变更统计
            context_changes = [r for r in recent_history if r["action"] == "context_change"]
            print(f"🔒 安全上下文变更: {len(context_changes)} 次")
            
            print("🔒 权限使用报告生成完成")
            
            return {
                "period_days": days,
                "total_permission_checks": len(permission_checks),
                "denied_requests": len(denied_requests),
                "denial_rate": len(denied_requests) / len(permission_checks) if permission_checks else 0,
                "resource_access_stats": resource_access,
                "context_changes": len(context_changes),
                "most_denied_resources": sorted(
                    [(k, v["denied"]) for k, v in resource_access.items()],
                    key=lambda x: x[1], reverse=True
                )[:5]
            }
            
        except Exception as e:
            print(f"❌ 生成权限报告失败: {e}")
            return {}
    
    def reset_to_defaults(self) -> bool:
        """重置为默认权限配置"""
        try:
            with self.lock:
                self.permissions = self.default_permissions.copy()
                self._save_permissions(self.permissions)
                
                print("🔄 权限配置已重置为默认值")
                
                # 记录重置操作
                self.permission_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "reset_permissions"
                })
                
                return True
                
        except Exception as e:
            print(f"❌ 重置权限配置失败: {e}")
            return False
    
    def validate_action(self, user_role: UserRole, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证用户操作的合法性"""
        validation_result = {
            "allowed": False,
            "reason": "",
            "alternative_suggestions": [],
            "safety_warning": ""
        }
        
        try:
            action_type = action_data.get("type", "unknown")
            category = action_data.get("category", "system")
            
            # 检查基本权限
            if not self.can_execute_command(user_role, category):
                validation_result["reason"] = f"用户角色 {user_role.value} 无权限执行 {category} 类操作"
                
                # 提供替代建议
                if user_role == UserRole.PASSENGER and self.current_safety_context == SafetyContext.DRIVING:
                    validation_result["alternative_suggestions"] = [
                        "请驾驶员代为操作",
                        "等待停车后再操作",
                        "使用语音助手询问信息"
                    ]
                
                return validation_result
            
            # 安全上下文检查
            if self.current_safety_context == SafetyContext.DRIVING:
                unsafe_actions = ["text_input", "video_play", "complex_navigation", "system_config"]
                if action_type in unsafe_actions:
                    validation_result["reason"] = "行驶中不允许此类操作，确保驾驶安全"
                    validation_result["safety_warning"] = "请在停车后进行此操作"
                    return validation_result
            
            # 紧急状态检查
            if self.current_safety_context == SafetyContext.EMERGENCY:
                non_essential_actions = ["music", "games", "entertainment"]
                if category in non_essential_actions:
                    validation_result["reason"] = "紧急状态下只允许必要操作"
                    validation_result["alternative_suggestions"] = [
                        "使用导航功能",
                        "进行紧急通讯",
                        "查看车辆状态"
                    ]
                    return validation_result
            
            # 通过所有检查
            validation_result["allowed"] = True
            validation_result["reason"] = "操作被允许"
            
        except Exception as e:
            validation_result["reason"] = f"验证过程发生错误: {e}"
        
        return validation_result


# 全局权限管理器实例 - 使用延迟初始化
_permission_manager_instance = None

def get_permission_manager():
    """获取权限管理器实例（延迟初始化）"""
    global _permission_manager_instance
    if _permission_manager_instance is None:
        _permission_manager_instance = PermissionManager()
    return _permission_manager_instance

# 为了保持向后兼容性，提供一个属性访问器
class PermissionManagerProxy:
    def __getattr__(self, name):
        return getattr(get_permission_manager(), name)

permission_manager = PermissionManagerProxy() 