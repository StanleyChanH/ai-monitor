"""简化日志模块 - 标准库实现（无 structlog 依赖），支持日志轮转."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any


# 日志轮转默认配置
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5  # 保留 5 个备份


class ColorFormatter(logging.Formatter):
    """彩色控制台格式化器."""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    log_dir: Path,
    log_level: str = "INFO",
    development: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> None:
    """配置日志系统，支持日志轮转.

    Args:
        log_dir: 日志目录
        log_level: 日志级别
        development: 是否为开发环境（开发环境使用彩色控制台输出）
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers.clear()

    # 抑制 httpx 的 HTTP 请求日志（太多了）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if development:
        console_formatter = ColorFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        console_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（使用 RotatingFileHandler 实现轮转）
    log_file = log_dir / "monitor.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)


class BoundLogger:
    """绑定的日志记录器（兼容 structlog 风格）."""

    def __init__(self, name: str, logger: logging.Logger):
        """初始化日志记录器."""
        self._name = name
        self._logger = logger
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """绑定上下文."""
        new_logger = BoundLogger(self._name, self._logger)
        new_logger._context = self._context.copy()
        new_logger._context.update(kwargs)
        return new_logger

    def _format_message(self, msg: str, **kwargs: Any) -> str:
        """格式化消息."""
        context = {**self._context, **kwargs}
        if context:
            parts = [f"{k}={v}" for k, v in context.items()]
            return f"{msg} | {', '.join(parts)}"
        return msg

    def debug(self, msg: str, **kwargs: Any) -> None:
        """调试日志."""
        self._logger.debug(self._format_message(msg, **kwargs))

    def info(self, msg: str, **kwargs: Any) -> None:
        """信息日志."""
        self._logger.info(self._format_message(msg, **kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        """警告日志."""
        self._logger.warning(self._format_message(msg, **kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        """错误日志."""
        self._logger.error(self._format_message(msg, **kwargs))

    def critical(self, msg: str, **kwargs: Any) -> None:
        """严重错误日志."""
        self._logger.critical(self._format_message(msg, **kwargs))


# 日志记录器缓存
_logger_cache: dict[str, BoundLogger] = {}


def get_logger(name: str | None = None) -> BoundLogger:
    """获取日志记录器.

    Args:
        name: 日志名称

    Returns:
        日志记录器
    """
    if name is None:
        name = "__main__"

    if name not in _logger_cache:
        _logger_cache[name] = BoundLogger(name, logging.getLogger(name))

    return _logger_cache[name]
