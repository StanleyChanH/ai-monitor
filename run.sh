#!/bin/bash
# Termux 启动脚本 - AI Monitor

# 设置临时目录环境变量
export TMPDIR="$HOME/tmp"
export TEMP="$HOME/tmp"
export TMP="$HOME/tmp"
export GIT_TMPDIR="$HOME/tmp"

# uv 包管理器配置（Termux 不支持硬链接）
export UV_LINK_MODE=copy

# 创建临时目录
mkdir -p "$HOME/tmp"

# 进入项目目录
cd "$(dirname "$0")"

# 启动监控
uv run -m src.main "$@"
