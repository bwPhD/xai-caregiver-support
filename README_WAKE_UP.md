# GitHub Actions 自动唤醒系统 - 完整实现方案

## 📋 概述

这个自动唤醒系统使用 GitHub Actions 解决 Streamlit Cloud 免费层应用休眠的问题。通过定时任务模拟用户访问，保持应用 24/7 可用。

## 🎯 实现的功能

### 1. 自动定时唤醒
- **频率**: 每 4 小时自动访问应用 (0, 4, 8, 12, 16, 20 点)
- **技术**: 使用 Selenium WebDriver 模拟真实用户访问
- **触发**: 支持手动触发唤醒

### 2. 智能错误处理
- **重试机制**: 最多 3 次自动重试
- **日志记录**: 详细的运行日志
- **错误提示**: 友好的错误信息和状态报告

### 3. 完整的 CI/CD 配置
- **工作流**: GitHub Actions 自动化配置
- **依赖管理**: 自动安装所需依赖
- **兼容性**: 跨平台支持 (Ubuntu)

## 📁 文件结构

```
.github/
├── workflows/
│   └── wake_up_app.yml          # GitHub Actions 工作流配置
├── scripts/
│   └── wake_up_app.py           # 唤醒脚本 (主要逻辑)
└── logs/
    ├── .gitkeep                 # 日志目录占位符
    └── wake_up.log              # 运行日志 (自动生成)
README_WAKE_UP.md                # 本文档
```

## 🚀 部署步骤

### 步骤 1: 配置 GitHub Secrets

1. 进入你的 GitHub 仓库
2. 点击 **Settings** 标签页
3. 在左侧菜单中找到 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 添加以下 Secret：
   ```
   Name: STREAMLIT_URL
   Value: https://your-app-name.streamlit.app
   ```
   ⚠️ **重要**: 将 `your-app-name` 替换为你的实际应用名称

### 步骤 2: 推送代码

```bash
git add .
git commit -m "Add automatic wake-up system for Streamlit app"
git push origin main
```

### 步骤 3: 启用工作流

1. 进入 GitHub 仓库的 **Actions** 标签页
2. 找到 **"Wake Up Streamlit App"** 工作流
3. 点击工作流名称进入详情页
4. 工作流会自动开始定时运行

## ⚙️ 技术实现详解

### GitHub Actions 工作流 (`.github/workflows/wake_up_app.yml`)

```yaml
name: Wake Up Streamlit App
on:
  schedule:
    - cron: '0 */4 * * *'  # 每4小时
  workflow_dispatch:        # 手动触发
```

**触发条件**:
- `schedule`: 定时任务 (cron 表达式)
- `workflow_dispatch`: 允许手动触发

### Python 唤醒脚本 (`.github/scripts/wake_up_app.py`)

**核心功能**:
- 使用 Selenium WebDriver 自动访问应用
- 智能等待页面加载完成
- 与应用进行交互 (滚动、点击) 确保完全唤醒
- 完整的错误处理和日志记录

**关键特性**:
- 健康检查: 先通过 HTTP 请求检查应用状态
- 页面验证: 确认 Streamlit 应用成功加载
- 交互模拟: 滚动页面和元素交互
- 重试机制: 失败时自动重试

## 📊 资源消耗与成本

### GitHub Actions 免费额度
- **每月免费额度**: 2000 分钟
- **每次运行时间**: 约 1-2 分钟
- **每月可用次数**: 约 1000-2000 次
- **实际成本**: 完全免费 (在免费额度内)

### 资源使用明细
- **运行环境**: Ubuntu Latest
- **Python 版本**: 3.9
- **浏览器**: Chrome Headless
- **主要依赖**: selenium, webdriver-manager

## 🔧 自定义配置

### 修改唤醒频率

在 `.github/workflows/wake_up_app.yml` 中修改 cron 表达式:

```yaml
schedule:
  # 每2小时唤醒一次
  - cron: '0 */2 * * *'
  # 每天早上9点唤醒
  - cron: '0 9 * * *'
  # 工作日每小时唤醒一次
  - cron: '0 * * * 1-5'
```

**常用 cron 表达式**:
- `0 */4 * * *`: 每4小时 (0,4,8,12,16,20点)
- `0 */2 * * *`: 每2小时
- `0 9 * * *`: 每天早上9点
- `0 */6 * * *`: 每6小时
- `0 9,13,17 * * *`: 每天9,13,17点

### 修改重试次数

在脚本中修改 `max_retries` 参数:

```python
# 在 wake_up_app.py 中
wake_up = StreamlitWakeUp(app_url, max_retries=5)  # 增加到5次重试
```

### 调整超时时间

```python
# 在 wake_up_app.py 中
wake_up = StreamlitWakeUp(app_url, timeout=60)  # 增加到60秒超时
```

## 📈 监控和维护

### 查看运行状态

1. 进入 GitHub 仓库的 **Actions** 标签页
2. 点击 **"Wake Up Streamlit App"** 工作流
3. 查看运行历史和每次执行的详细日志
4. 监控成功率和错误模式

### 日志文件

- **GitHub Actions 日志**: 在 Actions 页面查看每次运行的完整日志
- **本地日志文件**: `.github/logs/wake_up.log` (推送后可见)

### 常见日志信息

**成功唤醒**:
```
2024-01-15 08:00:01 - INFO - 开始唤醒 Streamlit 应用: https://your-app.streamlit.app
2024-01-15 08:00:05 - INFO - Chrome WebDriver 创建成功
2024-01-15 08:00:10 - INFO - 页面标题: Your App Title
2024-01-15 08:00:15 - INFO - ✅ 应用唤醒成功!
```

**唤醒失败**:
```
2024-01-15 08:00:01 - ERROR - 唤醒过程中出错: TimeoutException: Message: timeout
2024-01-15 08:00:31 - WARNING - 第 1 次尝试失败
2024-01-15 08:01:01 - INFO - ✅ 第 2 次尝试成功!
```

## 💡 优势总结

### 完全自动化
- ✅ 一旦设置好，无需手动干预
- ✅ 24/7 无人值守运行
- ✅ 智能重试机制

### 成本效益
- ✅ 完全免费 (GitHub Actions 免费额度内)
- ✅ 资源消耗极低
- ✅ 高性价比解决方案

### 高可靠性
- ✅ 智能错误处理和重试
- ✅ 多种验证机制
- ✅ 详细的监控和日志

### 易于维护
- ✅ 代码化配置，便于修改
- ✅ 版本控制和回滚
- ✅ 完整的文档和注释

## 🔒 安全考虑

### 数据保护
- ✅ 应用 URL 通过 GitHub Secrets 安全存储
- ✅ 不记录敏感信息到日志文件
- ✅ 脚本只进行合法的页面访问

### 访问限制
- ✅ 不执行任何数据修改操作
- ✅ 不访问受保护的资源
- ✅ 模拟正常用户浏览行为

## 🐛 故障排除

### 常见问题

**问题 1: 工作流无法运行**
```
解决步骤:
1. 检查 GitHub Secrets 是否正确设置
2. 确认工作流文件路径正确 (.github/workflows/wake_up_app.yml)
3. 检查仓库 Actions 设置是否启用
```

**问题 2: Selenium 访问失败**
```
解决步骤:
1. 检查应用 URL 是否可访问
2. 确认 Streamlit 应用正常运行
3. 查看详细错误日志
4. 考虑增加超时时间
```

**问题 3: 依赖安装失败**
```
解决步骤:
1. 检查网络连接
2. 确认 Python 版本兼容性
3. 查看 Actions 日志中的具体错误
```

### 获取帮助

如果遇到问题，请：
1. 查看 GitHub Actions 的详细日志
2. 检查 `.github/logs/wake_up.log` 文件
3. 确认所有配置步骤都已正确执行

## 📝 更新日志

### v1.0.0 (初始版本)
- ✅ 基本的定时唤醒功能
- ✅ Selenium WebDriver 集成
- ✅ 错误处理和重试机制
- ✅ 完整的日志记录
- ✅ GitHub Actions 工作流配置

---

## 🎉 结语

这个自动唤醒系统可以确保你的 Streamlit 应用 24/7 保持可用状态，用户随时访问都不会遇到休眠问题！

**开始使用**:
1. 按照部署步骤配置你的仓库
2. 推送代码并启用工作流
3. 享受自动化运维的便利！

有任何问题或建议，欢迎在 Issues 中提出。
