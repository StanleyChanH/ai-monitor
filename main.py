"""AI Monitor - 入口模块

此模块保留作为项目的备用入口点，主要功能在 monitor.py 中实现。
"""

from monitor import monitor_loop
import asyncio

def main():
    """启动 AI 监控系统"""
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\n👋 监控已停止")


if __name__ == "__main__":
    main()
