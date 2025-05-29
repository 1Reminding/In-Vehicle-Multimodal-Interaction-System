#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理命令行工具

管理系统用户配置、日志分析和权限管理
"""

import argparse
import json
import sys
import time
from typing import Dict, Any

# 导入系统管理模块
from modules.system import (
    SystemManager, UserConfigManager, InteractionLogger, PermissionManager,
    UserRole, SafetyContext, PermissionLevel
)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="车载多模态交互系统 - 系统管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 用户管理命令
    user_parser = subparsers.add_parser('user', help='用户管理')
    user_subparsers = user_parser.add_subparsers(dest='user_action')
    
    # 创建用户
    create_parser = user_subparsers.add_parser('create', help='创建新用户')
    create_parser.add_argument('user_id', help='用户ID')
    create_parser.add_argument('name', help='用户姓名')
    create_parser.add_argument('--role', choices=['driver', 'passenger'], default='driver', help='用户角色')
    
    # 列出用户
    user_subparsers.add_parser('list', help='列出所有用户')
    
    # 用户详情
    info_parser = user_subparsers.add_parser('info', help='查看用户详情')
    info_parser.add_argument('user_id', help='用户ID')
    
    # 权限管理命令
    perm_parser = subparsers.add_parser('permission', help='权限管理')
    perm_subparsers = perm_parser.add_subparsers(dest='perm_action')
    
    # 检查权限
    check_parser = perm_subparsers.add_parser('check', help='检查权限')
    check_parser.add_argument('user_role', choices=['driver', 'passenger'], help='用户角色')
    check_parser.add_argument('resource', help='资源名称')
    check_parser.add_argument('--context', choices=['parked', 'driving', 'emergency'], 
                             default='parked', help='安全上下文')
    
    # 权限报告
    perm_subparsers.add_parser('report', help='生成权限报告')
    
    # 日志分析命令
    log_parser = subparsers.add_parser('logs', help='日志分析')
    log_subparsers = log_parser.add_subparsers(dest='log_action')
    
    # 统计信息
    stats_parser = log_subparsers.add_parser('stats', help='获取统计信息')
    stats_parser.add_argument('--user', help='指定用户ID')
    stats_parser.add_argument('--days', type=int, default=7, help='统计天数')
    
    # 导出日志
    export_parser = log_subparsers.add_parser('export', help='导出日志')
    export_parser.add_argument('output_file', help='输出文件路径')
    export_parser.add_argument('--user', help='指定用户ID')
    export_parser.add_argument('--days', type=int, help='导出天数')
    
    # 清理日志
    cleanup_parser = log_subparsers.add_parser('cleanup', help='清理旧日志')
    cleanup_parser.add_argument('--days', type=int, default=90, help='保留天数')
    
    # 系统状态命令
    system_parser = subparsers.add_parser('system', help='系统状态管理')
    system_subparsers = system_parser.add_subparsers(dest='system_action')
    
    # 状态信息
    system_subparsers.add_parser('status', help='显示系统状态')
    
    # 设置车辆状态
    vehicle_parser = system_subparsers.add_parser('vehicle', help='设置车辆状态')
    vehicle_parser.add_argument('state', choices=['parked', 'driving', 'emergency'], help='车辆状态')
    
    # 演示命令
    demo_parser = subparsers.add_parser('demo', help='运行完整功能演示')
    demo_parser.add_argument('--scenario', choices=['complete', 'driver', 'passenger', 'emergency'], 
                           default='complete', help='演示场景')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 初始化系统管理器
    try:
        print("🔧 正在初始化系统管理器...")
        
        # 使用线程超时机制
        import threading
        import queue
        
        def init_system_manager(result_queue):
            try:
                from modules.system.system_manager import get_system_manager
                system_manager = get_system_manager()
                result_queue.put(("success", system_manager))
            except Exception as e:
                result_queue.put(("error", e))
        
        result_queue = queue.Queue()
        init_thread = threading.Thread(target=init_system_manager, args=(result_queue,))
        init_thread.daemon = True
        init_thread.start()
        
        # 等待30秒
        init_thread.join(timeout=30)
        
        if init_thread.is_alive():
            print("❌ 系统管理器初始化超时（30秒）")
            print("💡 建议：")
            print("   1. 检查 data/logs/interactions.db 文件是否被其他进程占用")
            print("   2. 尝试删除 data/logs/interactions.db-wal 和 data/logs/interactions.db-shm 文件")
            print("   3. 重启终端后重试")
            sys.exit(1)
        
        try:
            result_type, result = result_queue.get_nowait()
            if result_type == "error":
                raise result
            system_manager = result
        except queue.Empty:
            print("❌ 系统管理器初始化失败：未返回结果")
            sys.exit(1)
        
        print("✅ 系统管理器初始化完成")
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 请确保项目依赖已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 系统管理器初始化失败: {e}")
        print("💡 请检查系统配置和权限")
        sys.exit(1)
    
    try:
        if args.command == 'user':
            handle_user_commands(args, system_manager)
        elif args.command == 'permission':
            handle_permission_commands(args, system_manager)
        elif args.command == 'logs':
            handle_log_commands(args, system_manager)
        elif args.command == 'system':
            handle_system_commands(args, system_manager)
        elif args.command == 'demo':
            run_demo(args, system_manager)
            
    except KeyboardInterrupt:
        print("\n👋 退出系统管理工具")
    except Exception as e:
        print(f"❌ 执行命令时发生错误: {e}")
        import traceback
        traceback.print_exc()


def handle_user_commands(args, system_manager: SystemManager):
    """处理用户管理命令"""
    if args.user_action == 'create':
        success = system_manager.create_user_profile(args.user_id, args.name, args.role)
        if success:
            print(f"✅ 用户创建成功: {args.name} ({args.role})")
        else:
            print(f"❌ 用户创建失败")
    
    elif args.user_action == 'list':
        users = system_manager.user_config.list_users()
        if users:
            print("📋 用户列表:")
            for user in users:
                print(f"  - {user['name']} ({user['user_id']}) - {user['role']} - 最后登录: {user['last_login']}")
        else:
            print("📋 暂无用户")
    
    elif args.user_action == 'info':
        try:
            print("📂 正在加载用户配置...")
            if system_manager.user_config.load_user(args.user_id):
                print("✅ 用户配置加载成功")
                
                print("📊 正在获取用户控制面板...")
                dashboard = system_manager.get_user_dashboard()
                print("✅ 用户控制面板获取成功")
                
                print(f"👤 用户信息: {args.user_id}")
                print(json.dumps(dashboard, ensure_ascii=False, indent=2))
            else:
                print(f"❌ 用户不存在: {args.user_id}")
        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")


def handle_permission_commands(args, system_manager: SystemManager):
    """处理权限管理命令"""
    if args.perm_action == 'check':
        # 转换角色和上下文
        role = UserRole.DRIVER if args.user_role == 'driver' else UserRole.PASSENGER
        context_map = {
            'parked': SafetyContext.PARKED,
            'driving': SafetyContext.DRIVING,
            'emergency': SafetyContext.EMERGENCY
        }
        context = context_map[args.context]
        
        # 设置安全上下文
        system_manager.permission.set_safety_context(context)
        
        # 检查权限
        permission = system_manager.permission.check_permission(role, args.resource, PermissionLevel.WRITE)
        
        print(f"🔒 权限检查结果:")
        print(f"  用户角色: {args.user_role}")
        print(f"  资源: {args.resource}")
        print(f"  安全上下文: {args.context}")
        print(f"  权限: {'✅ 允许' if permission else '❌ 拒绝'}")
    
    elif args.perm_action == 'report':
        report = system_manager.permission.get_permission_report(days=7)
        print("📊 权限报告 (最近7天):")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def handle_log_commands(args, system_manager: SystemManager):
    """处理日志分析命令"""
    if args.log_action == 'stats':
        stats = system_manager.logger.get_interaction_stats(
            user_id=args.user,
            days=args.days
        )
        print(f"📈 交互统计 (最近{args.days}天):")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.log_action == 'export':
        success = system_manager.logger.export_logs(
            output_file=args.output_file,
            user_id=args.user,
            days=args.days
        )
        if success:
            print(f"✅ 日志导出成功: {args.output_file}")
        else:
            print(f"❌ 日志导出失败")
    
    elif args.log_action == 'cleanup':
        system_manager.cleanup_system(keep_days=args.days)
        print(f"✅ 已清理 {args.days} 天前的旧日志")


def handle_system_commands(args, system_manager: SystemManager):
    """处理系统状态命令"""
    if args.system_action == 'status':
        dashboard = system_manager.get_user_dashboard()
        print("🎛️ 系统状态:")
        print(json.dumps(dashboard['system_status'], ensure_ascii=False, indent=2))
        
        # 显示系统分析
        analytics = system_manager.get_system_analytics(days=7)
        print("\n📈 系统分析 (最近7天):")
        print(json.dumps(analytics, ensure_ascii=False, indent=2))
    
    elif args.system_action == 'vehicle':
        is_driving = args.state == 'driving'
        is_emergency = args.state == 'emergency'
        
        result = system_manager.set_vehicle_state(is_driving, is_emergency)
        print(f"🚗 车辆状态已更新: {result['old_context']} -> {result['new_context']}")
        print(f"安全限制: {result['restrictions']['safety_notes']}")


def run_demo(args, system_manager: SystemManager):
    """运行完整功能演示"""
    print("🎬 车载多模态交互系统 - 完整功能演示")
    print("=" * 60)
    
    if args.scenario == 'complete':
        run_complete_demo(system_manager)
    elif args.scenario == 'driver':
        run_driver_demo(system_manager)
    elif args.scenario == 'passenger':
        run_passenger_demo(system_manager)
    elif args.scenario == 'emergency':
        run_emergency_demo(system_manager)


def run_complete_demo(system_manager: SystemManager):
    """运行完整系统演示"""
    print("🚀 开始完整系统功能演示\n")
    
    # 1. 用户管理演示
    print("📋 1. 用户管理功能演示")
    print("-" * 30)
    
    # 创建演示用户
    demo_users = [
        ("demo_driver", "张驾驶员", "driver"),
        ("demo_passenger", "李乘客", "passenger")
    ]
    
    for user_id, name, role in demo_users:
        if not system_manager.user_config.load_user(user_id):
            success = system_manager.create_user_profile(user_id, name, role)
            print(f"✅ 创建用户: {name} ({role}) - {'成功' if success else '失败'}")
        else:
            print(f"✅ 用户已存在: {name} ({role})")
    
    # 显示用户列表
    users = system_manager.user_config.list_users()
    print(f"📋 当前系统用户数: {len(users)}")
    
    # 2. 权限管理演示
    print("\n🔒 2. 权限管理功能演示")
    print("-" * 30)
    
    # 测试不同场景下的权限
    test_scenarios = [
        ("driver", "navigation", "parked", "驾驶员停车时导航"),
        ("driver", "navigation", "driving", "驾驶员行驶时导航"),
        ("passenger", "navigation", "driving", "乘客行驶时导航"),
        ("driver", "music", "emergency", "驾驶员紧急状态播放音乐")
    ]
    
    for role, resource, context, description in test_scenarios:
        user_role = UserRole.DRIVER if role == 'driver' else UserRole.PASSENGER
        context_map = {
            'parked': SafetyContext.PARKED,
            'driving': SafetyContext.DRIVING,
            'emergency': SafetyContext.EMERGENCY
        }
        safety_context = context_map[context]
        
        system_manager.permission.set_safety_context(safety_context)
        permission = system_manager.permission.check_permission(user_role, resource, PermissionLevel.WRITE)
        
        status = "✅ 允许" if permission else "❌ 拒绝"
        print(f"{status} {description}")
    
    # 3. 交互日志演示
    print("\n📊 3. 交互日志功能演示")
    print("-" * 30)
    
    # 加载驾驶员用户
    system_manager.user_config.load_user("demo_driver")
    session_id = system_manager.start_session("demo_driver")
    print(f"📋 开始会话: {session_id}")
    
    # 模拟一些交互
    demo_interactions = [
        {
            "modality": "voice",
            "type": "navigation_command",
            "category": "navigation",
            "text": "导航到北京大学",
            "ai_response": {"confidence": 0.95, "action": "set_navigation"},
            "processing_time": 1.2,
            "success": True
        },
        {
            "modality": "gesture",
            "type": "volume_control",
            "category": "music",
            "text": "手势调节音量",
            "ai_response": {"confidence": 0.88, "action": "adjust_volume"},
            "processing_time": 0.5,
            "success": True
        },
        {
            "modality": "voice",
            "type": "climate_control",
            "category": "climate",
            "text": "设置温度22度",
            "ai_response": {"confidence": 0.92, "action": "set_temperature"},
            "processing_time": 0.8,
            "success": True
        }
    ]
    
    for interaction in demo_interactions:
        result = system_manager.process_multimodal_interaction(
            interaction_data=interaction,
            ai_response=interaction.get("ai_response"),
            processing_time=interaction["processing_time"],
            success=interaction["success"]
        )
        print(f"📝 记录交互: {interaction['type']} - {interaction['modality']}")
    
    # 结束会话
    system_manager.end_session()
    print("📋 会话结束")
    
    # 4. 系统状态演示
    print("\n🎛️ 4. 系统状态管理演示")
    print("-" * 30)
    
    # 测试不同车辆状态
    states = [
        (False, False, "停车状态"),
        (True, False, "行驶状态"),
        (True, True, "紧急状态")
    ]
    
    for is_driving, is_emergency, description in states:
        result = system_manager.set_vehicle_state(is_driving, is_emergency)
        print(f"🚗 {description}: {result['new_context']}")
        print(f"   安全限制: {len(result['restrictions']['restricted_actions'])} 项")
    
    # 5. 数据分析演示
    print("\n📈 5. 数据分析功能演示")
    print("-" * 30)
    
    # 获取交互统计
    stats = system_manager.logger.get_interaction_stats(user_id="demo_driver", days=1)
    print(f"📊 今日交互统计:")
    print(f"   总交互次数: {stats.get('total_interactions', 0)}")
    print(f"   成功率: {stats.get('success_rate', 0):.1%}")
    print(f"   平均响应时间: {stats.get('avg_response_time', 0):.2f}秒")
    
    # 获取用户行为分析
    user_stats = system_manager.user_config.get_interaction_stats()
    print(f"👤 用户行为分析:")
    print(f"   最常用手势: {user_stats.get('most_used_gesture', 'none')}")
    print(f"   最常用语音指令: {user_stats.get('most_used_voice_command', 'none')}")
    
    # 6. 权限报告演示
    print("\n📋 6. 权限使用报告")
    print("-" * 30)
    
    report = system_manager.permission.get_permission_report(days=1)
    print(f"🔒 权限检查统计:")
    print(f"   总检查次数: {report.get('total_checks', 0)}")
    print(f"   拒绝次数: {report.get('denied_requests', 0)}")
    print(f"   最常访问资源: {report.get('most_accessed_resource', 'none')}")
    
    print("\n🎉 完整功能演示结束！")
    print("💡 提示: 使用以下命令查看详细信息:")
    print("   python system_admin_tool.py user info demo_driver")
    print("   python system_admin_tool.py logs stats --user demo_driver --days 1")
    print("   python system_admin_tool.py permission report")


def run_driver_demo(system_manager: SystemManager):
    """驾驶员场景演示"""
    print("🚗 驾驶员使用场景演示\n")
    
    # 创建/加载驾驶员用户
    if not system_manager.user_config.load_user("demo_driver"):
        system_manager.create_user_profile("demo_driver", "张驾驶员", "driver")
        system_manager.user_config.load_user("demo_driver")
    
    session_id = system_manager.start_session("demo_driver")
    print(f"📋 驾驶员会话开始: {session_id}")
    
    try:
        # 停车状态 - 设置导航
        print("\n1️⃣ 停车状态 - 设置导航目的地")
        system_manager.set_vehicle_state(is_driving=False)
        
        interaction = {
            "modality": "voice",
            "type": "navigation_command",
            "category": "navigation",
            "text": "导航到北京大学"
        }
        
        result = system_manager.process_multimodal_interaction(
            interaction_data=interaction,
            ai_response={"confidence": 0.95, "action": "set_navigation"},
            processing_time=1.2,
            success=True
        )
        print(f"✅ 导航设置成功 - 会话ID: {result['session_id']}")
        
        # 行驶状态 - 语音控制音乐
        print("\n2️⃣ 行驶状态 - 语音控制音乐")
        system_manager.set_vehicle_state(is_driving=True)
        
        interaction = {
            "modality": "voice",
            "type": "music_command",
            "category": "music",
            "text": "播放轻音乐"
        }
        
        result = system_manager.process_multimodal_interaction(
            interaction_data=interaction,
            ai_response={"confidence": 0.88, "action": "play_music"},
            processing_time=0.8,
            success=True
        )
        print(f"✅ 音乐播放成功 - 响应时间: {result['processing_time']}秒")
        
        # 行驶状态 - 手势控制空调
        print("\n3️⃣ 行驶状态 - 手势控制空调")
        
        interaction = {
            "modality": "gesture",
            "type": "climate_control",
            "category": "climate",
            "text": "手势调节温度"
        }
        
        result = system_manager.process_multimodal_interaction(
            interaction_data=interaction,
            ai_response={"confidence": 0.85, "action": "adjust_temperature"},
            processing_time=0.6,
            success=True
        )
        print(f"✅ 空调调节成功 - 置信度: {result['ai_response']['confidence']}")
        
        # 显示驾驶员统计
        print("\n📊 驾驶员使用统计:")
        stats = system_manager.user_config.get_interaction_stats()
        dashboard = system_manager.get_user_dashboard()
        
        print(f"   总交互次数: {stats['total_interactions']}")
        print(f"   用户角色: {dashboard['user_info']['role']}")
        print(f"   当前权限: {len(dashboard['permissions']['admin'])} 项管理权限")
        
    finally:
        system_manager.end_session()
        print("\n📋 驾驶员会话结束")


def run_passenger_demo(system_manager: SystemManager):
    """乘客场景演示"""
    print("👥 乘客使用场景演示\n")
    
    # 创建/加载乘客用户
    if not system_manager.user_config.load_user("demo_passenger"):
        system_manager.create_user_profile("demo_passenger", "李乘客", "passenger")
        system_manager.user_config.load_user("demo_passenger")
    
    session_id = system_manager.start_session("demo_passenger")
    print(f"📋 乘客会话开始: {session_id}")
    
    try:
        # 行驶状态 - 尝试设置导航 (应该被拒绝)
        print("\n1️⃣ 行驶状态 - 尝试更改导航 (权限测试)")
        system_manager.set_vehicle_state(is_driving=True)
        
        # 检查权限
        permission = system_manager.permission.check_permission(
            UserRole.PASSENGER, "navigation", PermissionLevel.WRITE
        )
        
        if not permission:
            print("❌ 权限被拒绝: 乘客在行驶状态下无法更改导航")
            
            result = system_manager.process_multimodal_interaction(
                interaction_data={
                    "modality": "voice",
                    "type": "navigation_command",
                    "category": "navigation",
                    "text": "改变目的地"
                },
                processing_time=0.5,
                success=False,
                error_message="权限不足：乘客在行驶状态下无法更改导航"
            )
            print(f"📝 记录失败交互 - 错误: {result.get('error_message', '')}")
        
        # 行驶状态 - 控制音乐 (应该被允许)
        print("\n2️⃣ 行驶状态 - 控制音乐播放 (允许操作)")
        
        permission = system_manager.permission.check_permission(
            UserRole.PASSENGER, "music", PermissionLevel.WRITE
        )
        
        if permission:
            result = system_manager.process_multimodal_interaction(
                interaction_data={
                    "modality": "voice",
                    "type": "music_command",
                    "category": "music",
                    "text": "切换下一首歌"
                },
                ai_response={"confidence": 0.85, "action": "next_song"},
                processing_time=0.6,
                success=True
            )
            print(f"✅ 音乐控制成功 - 乘客可以控制娱乐功能")
        
        # 停车状态 - 设置导航 (应该被允许)
        print("\n3️⃣ 停车状态 - 设置导航 (权限恢复)")
        system_manager.set_vehicle_state(is_driving=False)
        
        permission = system_manager.permission.check_permission(
            UserRole.PASSENGER, "navigation", PermissionLevel.WRITE
        )
        
        if permission:
            result = system_manager.process_multimodal_interaction(
                interaction_data={
                    "modality": "touch",
                    "type": "navigation_command",
                    "category": "navigation",
                    "text": "搜索附近餐厅"
                },
                ai_response={"confidence": 0.92, "action": "search_poi"},
                processing_time=1.1,
                success=True
            )
            print(f"✅ 导航搜索成功 - 停车状态下乘客可以设置导航")
        
        # 显示乘客统计
        print("\n📊 乘客使用统计:")
        dashboard = system_manager.get_user_dashboard()
        
        print(f"   用户角色: {dashboard['user_info']['role']}")
        print(f"   读取权限: {len(dashboard['permissions']['read'])} 项")
        print(f"   写入权限: {len(dashboard['permissions']['write'])} 项")
        print(f"   当前安全上下文: {dashboard['system_status']['safety_context']}")
        
    finally:
        system_manager.end_session()
        print("\n📋 乘客会话结束")


def run_emergency_demo(system_manager: SystemManager):
    """紧急状态场景演示"""
    print("🚨 紧急状态场景演示\n")
    
    # 加载驾驶员用户
    if not system_manager.user_config.load_user("demo_driver"):
        system_manager.create_user_profile("demo_driver", "张驾驶员", "driver")
        system_manager.user_config.load_user("demo_driver")
    
    session_id = system_manager.start_session("demo_driver")
    print(f"📋 紧急状态会话开始: {session_id}")
    
    try:
        # 进入紧急状态
        print("\n🚨 1️⃣ 进入紧急状态")
        result = system_manager.set_vehicle_state(is_driving=True, is_emergency=True)
        print(f"⚠️ 车辆状态: {result['new_context']}")
        print(f"🔒 安全限制: {result['restrictions']['safety_notes']}")
        
        # 紧急导航
        print("\n🏥 2️⃣ 紧急导航到医院")
        
        permission = system_manager.permission.check_permission(
            UserRole.DRIVER, "navigation", PermissionLevel.ADMIN
        )
        
        if permission:
            result = system_manager.process_multimodal_interaction(
                interaction_data={
                    "modality": "voice",
                    "type": "emergency_navigation",
                    "category": "navigation",
                    "text": "导航到最近的医院"
                },
                ai_response={"confidence": 0.98, "action": "emergency_navigation"},
                processing_time=0.5,
                success=True
            )
            print(f"✅ 紧急导航启动 - 优先级最高")
        
        # 紧急通讯
        print("\n📞 3️⃣ 紧急通讯功能")
        
        result = system_manager.process_multimodal_interaction(
            interaction_data={
                "modality": "voice",
                "type": "emergency_call",
                "category": "communication",
                "text": "拨打急救电话"
            },
            ai_response={"confidence": 0.99, "action": "emergency_call"},
            processing_time=0.3,
            success=True
        )
        print(f"✅ 紧急通讯功能激活")
        
        # 尝试娱乐功能 (应该被拒绝)
        print("\n🎵 4️⃣ 尝试娱乐功能 (安全限制)")
        
        permission = system_manager.permission.check_permission(
            UserRole.DRIVER, "music", PermissionLevel.WRITE
        )
        
        if not permission:
            result = system_manager.process_multimodal_interaction(
                interaction_data={
                    "modality": "voice",
                    "type": "music_command",
                    "category": "music",
                    "text": "播放音乐"
                },
                processing_time=0.3,
                success=False,
                error_message="紧急状态下娱乐功能被禁用"
            )
            print(f"❌ 娱乐功能被禁用 - 紧急状态安全限制")
        
        # 显示紧急状态统计
        print("\n📊 紧急状态系统状态:")
        dashboard = system_manager.get_user_dashboard()
        
        print(f"   安全上下文: {dashboard['system_status']['safety_context']}")
        print(f"   受限操作: {len(dashboard['system_status']['safety_restrictions']['restricted_actions'])} 项")
        print(f"   允许模态: {dashboard['system_status']['safety_restrictions']['allowed_modalities']}")
        
        # 恢复正常状态
        print("\n✅ 5️⃣ 恢复正常行驶状态")
        result = system_manager.set_vehicle_state(is_driving=True, is_emergency=False)
        print(f"🚗 状态恢复: {result['new_context']}")
        
    finally:
        system_manager.end_session()
        print("\n📋 紧急状态会话结束")


if __name__ == "__main__":
    main() 