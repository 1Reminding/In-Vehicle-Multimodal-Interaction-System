# -*- coding: utf-8 -*-
"""
用户个性化配置管理器

负责保存和管理驾驶员的常用指令和交互习惯
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import threading


class UserConfigManager:
    """用户个性化配置管理器"""
    
    def __init__(self, config_dir: str = "data/user_configs"):
        self.config_dir = config_dir
        self.current_user = None
        self.user_config = {}
        self.lock = threading.Lock()
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "user_info": {
                "name": "",
                "role": "driver",  # driver 或 passenger
                "created_at": "",
                "last_login": ""
            },
            "interaction_preferences": {
                "preferred_voice_commands": [],
                "gesture_sensitivity": 0.7,
                "gaze_timeout": 3.0,
                "preferred_response_style": "concise"  # concise, detailed, friendly
            },
            "common_commands": {
                "navigation": [],
                "music": [],
                "climate": [],
                "communication": []
            },
            "interaction_patterns": {
                "most_used_gestures": {},
                "voice_command_frequency": {},
                "interaction_times": []
            },
            "accessibility": {
                "text_size": "medium",
                "voice_speed": 1.0,
                "high_contrast": False
            }
        }
    
    def create_user(self, user_id: str, name: str, role: str = "driver") -> bool:
        """创建新用户配置"""
        try:
            with self.lock:
                config_path = os.path.join(self.config_dir, f"{user_id}.json")
                
                if os.path.exists(config_path):
                    return False  # 用户已存在
                
                # 创建用户配置
                user_config = self.default_config.copy()
                user_config["user_info"]["name"] = name
                user_config["user_info"]["role"] = role
                user_config["user_info"]["created_at"] = datetime.now().isoformat()
                user_config["user_info"]["last_login"] = datetime.now().isoformat()
                
                # 保存配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(user_config, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            return False
    
    def load_user(self, user_id: str) -> bool:
        """加载用户配置"""
        try:
            with self.lock:
                config_path = os.path.join(self.config_dir, f"{user_id}.json")
                
                if not os.path.exists(config_path):
                    return False
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.user_config = json.load(f)
                
                self.current_user = user_id
                
                # 更新最后登录时间
                self.user_config["user_info"]["last_login"] = datetime.now().isoformat()
                
                # 直接保存，避免死锁（因为已经持有锁）
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.user_config, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            return False
    
    def save_config(self):
        """保存当前用户配置"""
        if not self.current_user:
            return False
        
        try:
            with self.lock:
                config_path = os.path.join(self.config_dir, f"{self.current_user}.json")
                
                # 检查目录是否存在
                if not os.path.exists(self.config_dir):
                    os.makedirs(self.config_dir, exist_ok=True)
                
                # 直接写入，不使用临时文件
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.user_config, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            return False
    
    def add_common_command(self, category: str, command: str):
        """添加常用指令"""
        if not self.current_user or category not in self.user_config["common_commands"]:
            return False
        
        with self.lock:
            commands = self.user_config["common_commands"][category]
            if command not in commands:
                commands.append(command)
                # 限制每个类别最多保存20条
                if len(commands) > 20:
                    commands.pop(0)
                
                # 直接保存，避免死锁（因为已经持有锁）
                config_path = os.path.join(self.config_dir, f"{self.current_user}.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.user_config, f, ensure_ascii=False, indent=2)
    
    def update_interaction_pattern(self, interaction_type: str, value: str):
        """更新交互模式统计"""
        if not self.current_user:
            return
        
        with self.lock:
            patterns = self.user_config["interaction_patterns"]
            
            if interaction_type == "gesture":
                if value not in patterns["most_used_gestures"]:
                    patterns["most_used_gestures"][value] = 0
                patterns["most_used_gestures"][value] += 1
                
            elif interaction_type == "voice":
                if value not in patterns["voice_command_frequency"]:
                    patterns["voice_command_frequency"][value] = 0
                patterns["voice_command_frequency"][value] += 1
            
            # 记录交互时间
            patterns["interaction_times"].append(datetime.now().isoformat())
            # 只保留最近1000条记录
            if len(patterns["interaction_times"]) > 1000:
                patterns["interaction_times"] = patterns["interaction_times"][-1000:]
            
            # 直接保存，避免死锁（因为已经持有锁）
            config_path = os.path.join(self.config_dir, f"{self.current_user}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, ensure_ascii=False, indent=2)
    
    def get_preference(self, key: str, default=None):
        """获取用户偏好设置"""
        if not self.current_user:
            return default
        
        keys = key.split('.')
        value = self.user_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_preference(self, key: str, value: Any):
        """设置用户偏好"""
        if not self.current_user:
            return False
        
        keys = key.split('.')
        config = self.user_config
        
        try:
            with self.lock:
                # 导航到最后一层
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                # 设置值
                config[keys[-1]] = value
                
                # 直接保存，避免死锁（因为已经持有锁）
                config_path = os.path.join(self.config_dir, f"{self.current_user}.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.user_config, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            return False
    
    def get_user_role(self) -> str:
        """获取用户角色"""
        return self.get_preference("user_info.role", "passenger")
    
    def get_common_commands(self, category: str = None) -> Dict[str, List[str]]:
        """获取常用指令"""
        if not self.current_user:
            return {}
        
        commands = self.user_config.get("common_commands", {})
        if category:
            return {category: commands.get(category, [])}
        return commands
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """获取交互统计信息"""
        if not self.current_user:
            return {}
        
        patterns = self.user_config.get("interaction_patterns", {})
        
        # 计算最常用的手势和语音指令
        most_used_gesture = max(patterns.get("most_used_gestures", {}), 
                               key=patterns.get("most_used_gestures", {}).get, 
                               default="none")
        
        most_used_voice = max(patterns.get("voice_command_frequency", {}), 
                             key=patterns.get("voice_command_frequency", {}).get, 
                             default="none")
        
        return {
            "most_used_gesture": most_used_gesture,
            "most_used_voice_command": most_used_voice,
            "total_interactions": len(patterns.get("interaction_times", [])),
            "gesture_stats": patterns.get("most_used_gestures", {}),
            "voice_stats": patterns.get("voice_command_frequency", {})
        }
    
    def list_users(self) -> List[Dict[str, str]]:
        """列出所有用户"""
        users = []
        try:
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    user_id = filename[:-5]  # 移除.json后缀
                    config_path = os.path.join(self.config_dir, filename)
                    
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    users.append({
                        "user_id": user_id,
                        "name": config.get("user_info", {}).get("name", user_id),
                        "role": config.get("user_info", {}).get("role", "unknown"),
                        "last_login": config.get("user_info", {}).get("last_login", "")
                    })
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")
        
        return users


# 全局用户配置管理器实例 - 使用延迟初始化
_user_config_manager_instance = None

def get_user_config_manager():
    """获取用户配置管理器实例（延迟初始化）"""
    global _user_config_manager_instance
    if _user_config_manager_instance is None:
        _user_config_manager_instance = UserConfigManager()
    return _user_config_manager_instance

# 为了保持向后兼容性，提供一个属性访问器
class UserConfigManagerProxy:
    def __getattr__(self, name):
        return getattr(get_user_config_manager(), name)

user_config_manager = UserConfigManagerProxy() 