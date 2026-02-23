#!/bin/bash
# Git 提交脚本 - AI Monitor

set -e

echo "=== 清理临时文件 ==="
# 删除测试文件
rm -f test_imports.py test_pipeline.py

# 删除 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "=== 配置 Git 用户信息 ==="
git config user.name "StanleyChanH"
git config user.email "stanleychanh@users.noreply.github.com"

echo "=== 初始化 Git 仓库 ==="
if [ ! -d .git ]; then
    git init
    echo "Git 仓库已初始化"
fi

echo "=== 添加远程仓库 ==="
if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin https://github.com/StanleyChanH/ai-monitor.git
else
    git remote add origin https://github.com/StanleyChanH/ai-monitor.git
fi

echo "=== 添加所有文件 ==="
git add .

echo "=== 创建提交 ==="
git commit -m "feat: AI Monitor v0.2.0 - 基于 Ollama 视觉模型的智能监控系统

## 功能特性
- 三阶段异步流水线（抓取、处理、推理）
- 飞书 Webhook 告警 + Termux 系统通知（震动/通知/Toast）
- 摄像头自动重连（指数退避策略）
- Circuit Breaker 熔断保护
- 日志文件自动轮转
- PM2 进程守护支持

## 架构
- 纯 Python 实现（无 Pydantic 依赖，Termux 兼容）
- structlog 结构化日志
- asyncio 异步处理
- 环境变量配置

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" || echo "没有新的更改需要提交"

echo "=== 推送到 GitHub ==="
git branch -M main
git push -u origin main

echo ""
echo "✅ 提交完成！"
echo "仓库地址: https://github.com/StanleyChanH/ai-monitor"
