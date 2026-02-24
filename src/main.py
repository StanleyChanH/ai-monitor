"""主入口文件."""

import asyncio
import os
import signal
from pathlib import Path

from src.config import Settings
from src.logger import get_logger, setup_logging
from src.monitor import MonitorPipeline

logger = get_logger(__name__)


def load_env_file() -> None:
    """加载 .env 文件到环境变量."""
    # 查找 .env 文件（当前目录或项目根目录）
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith("#"):
                        continue
                    # 解析 KEY=VALUE
                    if "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip()
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # 只设置未定义的环境变量
                        if key and key not in os.environ:
                            os.environ[key] = value
            return


class Application:
    """应用程序主类."""

    def __init__(self) -> None:
        """初始化应用程序."""
        self._settings = Settings()
        self._pipeline: MonitorPipeline | None = None
        self._shutdown_event = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def run(self) -> None:
        """运行应用程序."""
        # 配置日志（启用日志轮转）
        setup_logging(
            log_dir=self._settings.log_dir,
            log_level=self._settings.log_level,
            development=True,  # Termux 环境建议使用开发模式
            max_bytes=self._settings.log_max_bytes,
            backup_count=self._settings.log_backup_count,
        )

        logger.info(
            "application_starting",
            version="0.3.0",
            provider=self._settings.inference_provider,
            cam_url=self._settings.cam_url,
        )

        # 创建流水线
        self._pipeline = MonitorPipeline(self._settings)
        self._loop = asyncio.get_running_loop()

        # 设置信号处理
        self._setup_signal_handlers()

        try:
            # 启动流水线任务（非阻塞）
            pipeline_task = asyncio.create_task(self._pipeline.start())

            # 等待关闭信号
            await self._shutdown_event.wait()

            logger.info("shutdown_signal_received")

            # 停止流水线
            await self._pipeline.stop()

            # 等待流水线任务完成
            await pipeline_task

        except Exception as e:
            logger.error("application_error", error=str(e))
        finally:
            await self._shutdown()

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器."""

        def handle_signal(signum, frame):
            """处理信号."""
            logger.info("signal_received", signal=signum)
            # 在事件循环中调度关闭
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._shutdown_event.set)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

    async def _shutdown(self) -> None:
        """关闭应用程序."""
        logger.info("application_shutting_down")

        if self._pipeline:
            await self._pipeline.stop()

        logger.info("application_stopped")


async def main() -> None:
    """主入口函数."""
    app = Application()
    await app.run()


def entry_point() -> None:
    """命令行入口点."""
    # 加载 .env 文件（在导入 Settings 之前）
    load_env_file()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    entry_point()
