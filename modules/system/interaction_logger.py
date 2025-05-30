# -*- coding: utf-8 -*-
"""
多模态交互日志记录器

记录和分析多模态交互日志，帮助优化用户体验
"""

import json
import os
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import threading
from collections import defaultdict


class InteractionLogger:
    """多模态交互日志记录器"""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.db_path = os.path.join(log_dir, "interactions.db")
        
        # 可视化日志文件路径
        self.readable_log_path = os.path.join(log_dir, "interactions_readable.json")
        self.daily_log_path = os.path.join(log_dir, f"interactions_{datetime.now().strftime('%Y%m%d')}.json")
        
        self.lock = threading.Lock()
        self.db_available = False  # 数据库可用标志
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化可视化日志文件
        self._init_readable_logs()
        
        # 初始化数据库
        try:
            print("📊 开始初始化交互日志数据库...")
            self._init_database()
            self.db_available = True
            print("📊 交互日志记录器初始化完成")
        except Exception as e:
            print(f"❌ 交互日志记录器初始化失败: {e}")
            print("⚠️ 将在无数据库模式下运行，但可视化日志仍可用")
            self.db_available = False
    
    def _init_readable_logs(self):
        """初始化可视化日志文件"""
        try:
            # 如果今日日志文件不存在，创建一个空的JSON数组
            if not os.path.exists(self.daily_log_path):
                with open(self.daily_log_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"📄 创建可视化日志文件: {self.daily_log_path}")
        except Exception as e:
            print(f"⚠️ 初始化可视化日志失败: {e}")
    
    def _append_to_readable_log(self, log_entry: Dict[str, Any]):
        """添加条目到可视化日志文件"""
        try:
            # 读取现有日志
            daily_logs = []
            if os.path.exists(self.daily_log_path):
                try:
                    with open(self.daily_log_path, 'r', encoding='utf-8') as f:
                        daily_logs = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    daily_logs = []
            
            # 添加新条目
            daily_logs.append(log_entry)
            
            # 写回文件
            with open(self.daily_log_path, 'w', encoding='utf-8') as f:
                json.dump(daily_logs, f, ensure_ascii=False, indent=2)
            
            # 同时更新总日志文件（最近100条）
            if len(daily_logs) > 100:
                recent_logs = daily_logs[-100:]  # 只保留最近100条
            else:
                recent_logs = daily_logs
            
            with open(self.readable_log_path, 'w', encoding='utf-8') as f:
                json.dump(recent_logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ 写入可视化日志失败: {e}")
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            print("📊 尝试连接数据库...")
            # 设置更短的数据库连接超时
            conn = sqlite3.connect(self.db_path, timeout=1.0)
            
            print("📊 设置数据库参数...")
            conn.execute("PRAGMA journal_mode=WAL")  # 使用WAL模式避免锁定
            conn.execute("PRAGMA synchronous=NORMAL")  # 提高性能
            conn.execute("PRAGMA temp_store=memory")  # 使用内存临时存储
            conn.execute("PRAGMA busy_timeout=1000")  # 设置忙等待超时为1秒
            
            cursor = conn.cursor()
            
            print("📊 创建交互日志表...")
            # 创建交互日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    interaction_type TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    input_data TEXT,
                    ai_response TEXT,
                    confidence REAL,
                    processing_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    context_data TEXT
                )
            """)
            
            print("📊 创建性能统计表...")
            # 创建性能统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    session_id TEXT,
                    user_id TEXT
                )
            """)
            
            print("📊 创建用户行为分析表...")
            # 创建用户行为分析表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_behavior (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    behavior_type TEXT NOT NULL,
                    behavior_data TEXT,
                    session_id TEXT
                )
            """)
            
            print("📊 提交数据库更改...")
            conn.commit()
            conn.close()
            print("📊 数据库表创建完成")
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("⚠️ 数据库被锁定，尝试删除锁定文件...")
                try:
                    # 尝试删除WAL和SHM文件
                    import os
                    wal_file = self.db_path + "-wal"
                    shm_file = self.db_path + "-shm"
                    if os.path.exists(wal_file):
                        os.remove(wal_file)
                        print("🗑️ 已删除WAL文件")
                    if os.path.exists(shm_file):
                        os.remove(shm_file)
                        print("🗑️ 已删除SHM文件")
                    
                    # 重试连接
                    print("🔄 重试数据库连接...")
                    conn = sqlite3.connect(self.db_path, timeout=1.0)
                    conn.close()
                    print("✅ 数据库连接恢复")
                except Exception as retry_e:
                    print(f"❌ 重试失败: {retry_e}")
                    raise e
            else:
                print(f"❌ 数据库操作错误: {e}")
                raise e
        except Exception as e:
            print(f"❌ 数据库初始化错误: {e}")
            raise e
    
    def log_interaction(self, 
                       interaction_type: str,
                       modality: str,
                       input_data: Dict[str, Any],
                       ai_response: Optional[Dict[str, Any]] = None,
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       processing_time: Optional[float] = None,
                       success: bool = True,
                       error_message: Optional[str] = None,
                       context_data: Optional[Dict[str, Any]] = None):
        """记录交互日志"""
        
        # 计算置信度
        confidence = None
        if ai_response and 'confidence' in ai_response:
            confidence = ai_response['confidence']
        
        # 准备日志条目（无论数据库是否可用都记录到可视化日志）
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "interaction_type": interaction_type,
            "modality": modality,
            "input_data": input_data,
            "ai_response": ai_response,
            "confidence": confidence,
            "processing_time": processing_time,
            "success": success,
            "error_message": error_message,
            "context_data": context_data
        }
        
        # 记录到可视化日志文件
        self._append_to_readable_log(log_entry)
        
        # 如果数据库可用，也记录到数据库
        if not self.db_available:
            print("⚠️ 数据库不可用，但已记录到可视化日志文件")
            return
        
        try:
            with self.lock:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO interaction_logs 
                        (timestamp, user_id, session_id, interaction_type, modality, 
                         input_data, ai_response, confidence, processing_time, 
                         success, error_message, context_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        log_entry["timestamp"],
                        user_id,
                        session_id,
                        interaction_type,
                        modality,
                        json.dumps(input_data, ensure_ascii=False),
                        json.dumps(ai_response, ensure_ascii=False) if ai_response else None,
                        confidence,
                        processing_time,
                        success,
                        error_message,
                        json.dumps(context_data, ensure_ascii=False) if context_data else None
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ 记录交互日志到数据库失败: {e}，但已记录到可视化日志文件")
    
    def log_performance_metric(self, 
                              metric_name: str, 
                              metric_value: float,
                              user_id: Optional[str] = None,
                              session_id: Optional[str] = None):
        """记录性能指标"""
        if not self.db_available:
            print("⚠️ 数据库不可用，跳过性能指标记录")
            return
            
        try:
            with self.lock:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO performance_stats 
                        (timestamp, metric_name, metric_value, session_id, user_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        metric_name,
                        metric_value,
                        session_id,
                        user_id
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ 记录性能指标失败: {e}")
    
    def log_user_behavior(self,
                         behavior_type: str,
                         behavior_data: Dict[str, Any],
                         user_id: str,
                         session_id: Optional[str] = None):
        """记录用户行为"""
        if not self.db_available:
            print("⚠️ 数据库不可用，跳过用户行为记录")
            return
            
        try:
            with self.lock:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO user_behavior 
                        (timestamp, user_id, behavior_type, behavior_data, session_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        user_id,
                        behavior_type,
                        json.dumps(behavior_data, ensure_ascii=False),
                        session_id
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ 记录用户行为失败: {e}")
    
    def get_interaction_stats(self, 
                             user_id: Optional[str] = None,
                             days: int = 7) -> Dict[str, Any]:
        """获取交互统计信息"""
        if not self.db_available:
            print("⚠️ 数据库不可用，返回默认统计信息")
            return {
                "total_interactions": 0,
                "success_rate": 0,
                "avg_processing_time": 0,
                "avg_confidence": 0,
                "modality_distribution": {},
                "interaction_type_distribution": {},
                "daily_trend": {},
                "period_days": days
            }
        
        try:
            print(f"📊 开始获取交互统计信息 (用户: {user_id}, 天数: {days})...")
            
            # 使用超时连接
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            # 时间范围
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 基础查询条件
            where_clause = "timestamp >= ?"
            params = [start_time]
            
            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)
            
            print("📊 查询总交互次数...")
            # 总交互次数
            cursor.execute(f"""
                SELECT COUNT(*) FROM interaction_logs WHERE {where_clause}
            """, params)
            total_interactions = cursor.fetchone()[0]
            
            print("📊 查询成功率...")
            # 成功率
            cursor.execute(f"""
                SELECT COUNT(*) FROM interaction_logs 
                WHERE {where_clause} AND success = 1
            """, params)
            successful_interactions = cursor.fetchone()[0]
            
            success_rate = successful_interactions / total_interactions if total_interactions > 0 else 0
            
            print("📊 查询模态分布...")
            # 模态分布
            cursor.execute(f"""
                SELECT modality, COUNT(*) FROM interaction_logs 
                WHERE {where_clause}
                GROUP BY modality
            """, params)
            modality_distribution = dict(cursor.fetchall())
            
            print("📊 查询平均处理时间...")
            # 平均处理时间
            cursor.execute(f"""
                SELECT AVG(processing_time) FROM interaction_logs 
                WHERE {where_clause} AND processing_time IS NOT NULL
            """, params)
            avg_processing_time = cursor.fetchone()[0] or 0
            
            print("📊 查询置信度分布...")
            # 置信度分布
            cursor.execute(f"""
                SELECT AVG(confidence) FROM interaction_logs 
                WHERE {where_clause} AND confidence IS NOT NULL
            """, params)
            avg_confidence = cursor.fetchone()[0] or 0
            
            print("📊 查询交互类型分布...")
            # 交互类型分布
            cursor.execute(f"""
                SELECT interaction_type, COUNT(*) FROM interaction_logs 
                WHERE {where_clause}
                GROUP BY interaction_type
            """, params)
            interaction_type_distribution = dict(cursor.fetchall())
            
            print("📊 查询每日交互趋势...")
            # 每日交互趋势
            cursor.execute(f"""
                SELECT DATE(timestamp) as date, COUNT(*) FROM interaction_logs 
                WHERE {where_clause}
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, params)
            daily_trend = dict(cursor.fetchall())
            
            conn.close()
            print("📊 交互统计信息获取完成")
            
            return {
                "total_interactions": total_interactions,
                "success_rate": round(success_rate, 3),
                "avg_processing_time": round(avg_processing_time, 3),
                "avg_confidence": round(avg_confidence, 3),
                "modality_distribution": modality_distribution,
                "interaction_type_distribution": interaction_type_distribution,
                "daily_trend": daily_trend,
                "period_days": days
            }
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("⚠️ 数据库被锁定，返回空统计信息")
                return {}
            else:
                print(f"❌ 数据库操作错误: {e}")
                return {}
        except Exception as e:
            print(f"❌ 获取交互统计失败: {e}")
            return {}
    
    def get_user_behavior_analysis(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取用户行为分析"""
        if not self.db_available:
            print("⚠️ 数据库不可用，返回默认用户行为分析")
            return {
                "activity_trend": {},
                "preferred_modalities": [],
                "hourly_distribution": {},
                "behavior_types": {},
                "analysis_period": days
            }
        
        try:
            print(f"📊 开始获取用户行为分析 (用户: {user_id}, 天数: {days})...")
            
            # 使用超时连接
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            print("📊 查询用户活跃度...")
            # 用户活跃度
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) FROM interaction_logs 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (user_id, start_time))
            activity_trend = dict(cursor.fetchall())
            
            print("📊 查询偏好的交互方式...")
            # 偏好的交互方式
            cursor.execute("""
                SELECT modality, COUNT(*) as count FROM interaction_logs 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY modality
                ORDER BY count DESC
            """, (user_id, start_time))
            preferred_modalities = cursor.fetchall()
            
            print("📊 查询交互时间分布...")
            # 交互时间分布
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) FROM interaction_logs 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """, (user_id, start_time))
            hourly_distribution = dict(cursor.fetchall())
            
            print("📊 查询用户行为类型统计...")
            # 用户行为类型统计
            cursor.execute("""
                SELECT behavior_type, COUNT(*) FROM user_behavior 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY behavior_type
            """, (user_id, start_time))
            behavior_types = dict(cursor.fetchall())
            
            conn.close()
            print("📊 用户行为分析获取完成")
            
            return {
                "activity_trend": activity_trend,
                "preferred_modalities": preferred_modalities,
                "hourly_distribution": hourly_distribution,
                "behavior_types": behavior_types,
                "analysis_period": days
            }
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("⚠️ 数据库被锁定，返回空行为分析")
                return {}
            else:
                print(f"❌ 数据库操作错误: {e}")
                return {}
        except Exception as e:
            print(f"❌ 获取用户行为分析失败: {e}")
            return {}
    
    def get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """获取错误分析报告"""
        if not self.db_available:
            print("⚠️ 数据库不可用，返回默认错误分析")
            return {
                "error_types": [],
                "error_trend": {},
                "modality_error_rates": {},
                "analysis_period": days
            }
        
        try:
            print(f"📊 开始获取错误分析报告 (天数: {days})...")
            
            # 使用超时连接
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            print("📊 查询错误统计...")
            # 错误统计
            cursor.execute("""
                SELECT error_message, COUNT(*) FROM interaction_logs 
                WHERE timestamp >= ? AND success = 0 AND error_message IS NOT NULL
                GROUP BY error_message
                ORDER BY COUNT(*) DESC
            """, (start_time,))
            error_types = cursor.fetchall()
            
            print("📊 查询错误趋势...")
            # 错误趋势
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) FROM interaction_logs 
                WHERE timestamp >= ? AND success = 0
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (start_time,))
            error_trend = dict(cursor.fetchall())
            
            print("📊 查询按模态分组的错误率...")
            # 按模态分组的错误率
            cursor.execute("""
                SELECT modality, 
                       COUNT(*) as total,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                FROM interaction_logs 
                WHERE timestamp >= ?
                GROUP BY modality
            """, (start_time,))
            
            modality_error_rates = {}
            for row in cursor.fetchall():
                modality, total, errors = row
                error_rate = errors / total if total > 0 else 0
                modality_error_rates[modality] = {
                    "total": total,
                    "errors": errors,
                    "error_rate": round(error_rate, 3)
                }
            
            conn.close()
            print("📊 错误分析报告获取完成")
            
            return {
                "error_types": error_types,
                "error_trend": error_trend,
                "modality_error_rates": modality_error_rates,
                "analysis_period": days
            }
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("⚠️ 数据库被锁定，返回空错误分析")
                return {}
            else:
                print(f"❌ 数据库操作错误: {e}")
                return {}
        except Exception as e:
            print(f"❌ 获取错误分析失败: {e}")
            return {}
    
    def export_logs(self, 
                   output_file: str,
                   user_id: Optional[str] = None,
                   days: Optional[int] = None) -> bool:
        """导出日志数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询
                where_clauses = []
                params = []
                
                if days:
                    start_time = (datetime.now() - timedelta(days=days)).isoformat()
                    where_clauses.append("timestamp >= ?")
                    params.append(start_time)
                
                if user_id:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                cursor.execute(f"""
                    SELECT * FROM interaction_logs WHERE {where_clause}
                    ORDER BY timestamp DESC
                """, params)
                
                logs = []
                columns = [description[0] for description in cursor.description]
                
                for row in cursor.fetchall():
                    log_entry = dict(zip(columns, row))
                    # 解析JSON字段
                    for field in ['input_data', 'ai_response', 'context_data']:
                        if log_entry[field]:
                            try:
                                log_entry[field] = json.loads(log_entry[field])
                            except json.JSONDecodeError:
                                pass
                    logs.append(log_entry)
                
                # 保存到文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 日志已导出到: {output_file}")
                return True
                
        except Exception as e:
            print(f"❌ 导出日志失败: {e}")
            return False
    
    def cleanup_old_logs(self, keep_days: int = 90):
        """清理旧日志（保留指定天数）"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cutoff_time = (datetime.now() - timedelta(days=keep_days)).isoformat()
                    
                    # 删除旧的交互日志
                    cursor.execute("""
                        DELETE FROM interaction_logs WHERE timestamp < ?
                    """, (cutoff_time,))
                    
                    # 删除旧的性能统计
                    cursor.execute("""
                        DELETE FROM performance_stats WHERE timestamp < ?
                    """, (cutoff_time,))
                    
                    # 删除旧的用户行为记录
                    cursor.execute("""
                        DELETE FROM user_behavior WHERE timestamp < ?
                    """, (cutoff_time,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    print(f"🧹 已清理 {deleted_count} 条旧日志记录")
                    
        except Exception as e:
            print(f"❌ 清理旧日志失败: {e}")


# 全局交互日志记录器实例 - 使用延迟初始化
_interaction_logger_instance = None

def get_interaction_logger():
    """获取交互日志记录器实例（延迟初始化）"""
    global _interaction_logger_instance
    if _interaction_logger_instance is None:
        _interaction_logger_instance = InteractionLogger()
    return _interaction_logger_instance

# 为了保持向后兼容性，提供一个属性访问器
class InteractionLoggerProxy:
    def __getattr__(self, name):
        return getattr(get_interaction_logger(), name)

interaction_logger = InteractionLoggerProxy() 