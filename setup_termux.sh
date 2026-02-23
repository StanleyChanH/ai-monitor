#!/bin/bash
# Termux 环境依赖安装脚本

set -e

echo "=== 安装构建依赖 ==="

# 更新包管理器
pkg update -y

# 安装 Rust 和构建工具
pkg install -y rust binutils cmake make python ncurses zlib

echo "=== 验证 Rust 安装 ==="
rustc --version || echo "Rust 未正确安装"
cargo --version || echo "Cargo 未正确安装"

echo "=== 重新同步 Python 依赖 ==="
cd "$(dirname "$0")"
uv sync

echo "=== 完成 ==="
