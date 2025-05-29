# 系统管理功能说明

## 概述

本项目已集成了完善的系统管理功能，包括：

1. **用户个性化配置** - 保存驾驶员的常用指令和交互习惯
2. **多模态交互日志记录** - 记录和分析交互数据，优化用户体验
3. **权限管理系统** - 区分驾驶员与乘客权限，确保行车安全

## 功能特性

### 1. 用户个性化配置 (`UserConfigManager`)

- **用户档案管理**：创建和管理驾驶员、乘客档案
- **偏好设置**：保存语音、手势、界面偏好
- **常用指令学习**：自动记录和推荐常用指令
- **交互习惯分析**：统计最常用的手势和语音指令

### 2. 交互日志记录 (`InteractionLogger`)

- **完整日志记录**：记录所有多模态交互数据
- **性能分析**：统计响应时间、成功率等指标
- **用户行为分析**：分析使用模式和偏好
- **错误追踪**：详细记录和分析系统错误

### 3. 权限管理系统 (`PermissionManager`)

- **角色区分**：驾驶员、乘客、管理员三种角色
- **安全上下文**：停车、行驶、紧急三种状态
- **动态权限**：根据车辆状态动态调整权限
- **安全防护**：防止行驶中进行危险操作

## 使用方法

### 基本用户管理

```bash
# 创建新用户
python system_admin_tool.py user create <用户ID> "<用户姓名>" --role <角色>
# 示例：python system_admin_tool.py user create driver1 "张驾驶员" --role driver

# 查看所有用户
python system_admin_tool.py user list

# 查看用户详细信息
python system_admin_tool.py user info <用户ID>
# 示例：python system_admin_tool.py user info driver1
```

### 权限管理

```bash
# 检查用户权限
python system_admin_tool.py permission check <用户ID> <功能> --context <状态>
# 示例：python system_admin_tool.py permission check driver1 navigation --context driving

# 生成权限报告
python system_admin_tool.py permission report
```

### 系统状态管理

```bash
# 查看系统状态
python system_admin_tool.py system status

# 设置车辆状态
python system_admin_tool.py system vehicle <状态>
# 状态选项：parked（停车）、driving（行驶）、emergency（紧急）
```

### 日志和统计

```bash
# 查看交互统计
python system_admin_tool.py logs stats --user <用户ID> --days <天数>
# 示例：python system_admin_tool.py logs stats --user driver1 --days 7

# 导出日志数据
python system_admin_tool.py logs export <文件名> --user <用户ID>
# 示例：python system_admin_tool.py logs export logs.json --user driver1

# 清理旧日志
python system_admin_tool.py logs cleanup --days <天数>
# 示例：python system_admin_tool.py logs cleanup --days 90
```

### 功能演示

```bash
# 运行完整功能演示（推荐）
python system_admin_tool.py demo

# 运行特定场景演示
python system_admin_tool.py demo --scenario driver      # 驾驶员场景
python system_admin_tool.py demo --scenario passenger   # 乘客场景
python system_admin_tool.py demo --scenario emergency   # 紧急状态场景
python system_admin_tool.py demo --scenario complete    # 完整功能演示（默认）
```

### 程序集成

在主应用中，系统管理功能已自动集成：

```python
from modules.system import system_manager

# 系统会自动：
# 1. 记录所有交互日志
# 2. 验证用户权限
# 3. 学习用户习惯
# 4. 生成分析报告
```

## 权限配置

### 默认权限规则

| 功能 | 驾驶员(停车) | 驾驶员(行驶) | 驾驶员(紧急) | 乘客(停车) | 乘客(行驶) | 乘客(紧急) |
|------|-------------|-------------|-------------|-----------|-----------|-----------|
| 导航 | 全部权限 | 只读 | 全部权限 | 读写 | 无权限 | 只读 |
| 音乐 | 全部权限 | 读写 | 无权限 | 读写 | 读写 | 无权限 |
| 空调 | 全部权限 | 读写 | 只读 | 读写 | 读写 | 无权限 |
| 通讯 | 全部权限 | 只读 | 全部权限 | 读写 | 无权限 | 读写 |
| 设置 | 全部权限 | 无权限 | 无权限 | 只读 | 无权限 | 无权限 |
| 语音控制 | 全部权限 | 全部权限 | 全部权限 | 读写 | 只读 | 读写 |
| 手势控制 | 全部权限 | 读写 | 读写 | 读写 | 只读 | 无权限 |

### 权限级别说明

- **无权限 (NONE)**：完全不允许访问
- **只读 (READ)**：只能查看信息，不能操作
- **读写 (WRITE)**：可以进行基本操作
- **全部权限 (ADMIN)**：完全控制权限

## 安全特性

### 行驶安全保护

- **视觉分心防护**：行驶中禁止复杂界面操作
- **操作简化**：优先语音和简单手势控制
- **权限动态调整**：根据车速和状态自动调整

### 紧急状态处理

- **功能优先级**：紧急状态下只允许必要功能
- **快速响应**：导航和通讯功能优先处理
- **娱乐限制**：暂停非必要的娱乐功能

## 数据存储

### 文件结构

```
data/
├── user_configs/          # 用户配置文件
│   ├── driver1.json      # 用户配置
│   └── passenger1.json
├── logs/
│   └── interactions.db   # SQLite交互日志数据库
├── permissions.json      # 权限配置文件
└── exports/             # 数据导出目录
```

### 数据库结构

- **interaction_logs**：交互记录表
- **performance_stats**：性能统计表
- **user_behavior**：用户行为表

## 分析报告

系统提供多种分析报告：

### 交互统计
- 总交互次数
- 成功率
- 平均响应时间
- 模态使用分布

### 用户行为分析
- 活跃度趋势
- 偏好的交互方式
- 使用时间分布
- 行为类型统计

### 权限使用报告
- 权限检查次数
- 拒绝请求统计
- 资源访问统计
- 最常被拒绝的操作

## 个性化功能

### 常用指令学习
系统自动记录用户的常用指令，按类别整理：
- 导航类：常用目的地
- 音乐类：喜欢的歌曲/歌手
- 空调类：温度偏好
- 通讯类：常用联系人

### 交互习惯适应
- 自动调整手势识别敏感度
- 记录最常用的交互方式
- 提供个性化建议

### 界面偏好
- 字体大小设置
- 语音播放速度
- 高对比度模式

## 扩展性

系统采用模块化设计，便于扩展：

1. **新权限类型**：可轻松添加新的权限类别
2. **新用户角色**：支持添加自定义用户角色
3. **新安全上下文**：可根据需要添加新的安全状态
4. **新分析指标**：支持添加自定义分析维度

## 注意事项

1. **隐私保护**：用户数据存储在本地，不会上传到云端
2. **定期清理**：建议定期清理90天以上的旧日志
3. **备份重要**：用户配置文件建议定期备份
4. **权限谨慎**：修改权限配置时请谨慎，确保行车安全

## 故障排除

### 常见问题及解决方案

1. **用户配置加载失败**
   - 检查用户ID是否正确
   - 确认配置文件是否存在于 `data/user_configs/` 目录
   - 使用 `python system_admin_tool.py user list` 查看所有用户

2. **权限检查异常**
   - 确认用户角色设置正确
   - 检查当前安全上下文状态
   - 使用 `python system_admin_tool.py permission report` 查看权限配置

3. **数据库连接问题**
   - 确认 `data/logs/` 目录存在
   - 检查数据库文件权限
   - 重启应用程序

4. **系统响应缓慢**
   - 检查日志文件大小，考虑清理旧数据
   - 使用 `python system_admin_tool.py system status` 查看系统状态

### 调试命令

```bash
# 查看详细系统状态
python system_admin_tool.py system status

# 检查特定用户权限
python system_admin_tool.py permission check <用户ID> <功能>

# 导出最近日志进行分析
python system_admin_tool.py logs export debug.json --days 1
```

### 数据维护

```bash
# 定期清理旧日志（建议每月执行）
python system_admin_tool.py logs cleanup --days 90

# 备份用户配置
cp -r data/user_configs/ backup/user_configs_$(date +%Y%m%d)/
``` 