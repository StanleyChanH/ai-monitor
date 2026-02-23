#!/bin/bash
# PM2 管理脚本

set -e

# 设置临时目录环境变量
export TMPDIR="$HOME/tmp"
export TEMP="$HOME/tmp"
export TMP="$HOME/tmp"
export GIT_TMPDIR="$HOME/tmp"

# 创建必要目录
mkdir -p "$HOME/tmp"
mkdir -p logs/pm2
mkdir -p alerts

# 进入项目目录
cd "$(dirname "$0")"

case "${1:-start}" in
  start)
    echo "🚀 启动 AI Monitor..."
    pm2 start ecosystem.config.js
    pm2 save
    pm2 list
    ;;
  stop)
    echo "⏹️  停止 AI Monitor..."
    pm2 stop ai-monitor
    ;;
  restart)
    echo "🔄 重启 AI Monitor..."
    pm2 restart ai-monitor
    ;;
  delete|remove)
    echo "🗑️  删除 AI Monitor..."
    pm2 delete ai-monitor
    pm2 save
    ;;
  reload)
    echo "♻️  平滑重启 AI Monitor..."
    pm2 reload ai-monitor
    ;;
  logs)
    echo "📋 查看日志..."
    pm2 logs ai-monitor
    ;;
  status)
    echo "📊 查看状态..."
    pm2 show ai-monitor
    ;;
  monit)
    echo "📈 实时监控..."
    pm2 monit
    ;;
  flush)
    echo "🧹 清空日志..."
    pm2 flush
    ;;
  update)
    echo "🔄 更新 PM2 并重启..."
    pm2 update
    ;;
  *)
    echo "用法: $0 {start|stop|restart|delete|reload|logs|status|monit|flush|update}"
    echo ""
    echo "命令说明:"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  delete   - 删除服务"
    echo "  reload   - 平滑重启（0秒 downtime）"
    echo "  logs     - 查看日志"
    echo "  status   - 查看详细状态"
    echo "  monit    - 实时监控面板"
    echo "  flush    - 清空日志"
    echo "  update   - 更新 PM2 并重启"
    exit 1
    ;;
esac
