"""日志系统模块 - 使用 structlog 实现结构化日志，支持日志轮转."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.typing import EventDict, Processor


# 日志轮转默认配置
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5  # 保留 5 个备份


def setup_logging(
    log_dir: Path,
    log_level: str = "INFO",
    development: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> None:
    """配置结构化日志，支持日志轮转.

    Args:
        log_dir: 日志目录
        log_level: 日志级别
        development: 是否为开发环境（开发环境使用彩色控制台输出）
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 共享的处理器
    shared_processors: list[Processor] = [
        # 添加日志级别
        structlog.stdlib.add_log_level,
        # 添加日志名称
        structlog.stdlib.add_logger_name,
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加调用位置
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        # 处理异常信息
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if development:
        # 开发环境：彩色控制台输出
        processors: list[Processor] = [
            *shared_processors,
            # 格式化为易读的格式
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    else:
        # 生产环境：JSON 格式
        processors = [
            *shared_processors,
            # 格式化为 JSON
            structlog.processors.JSONRenderer(),
        ]

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging（用于底层库）
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(console_handler)

    # 文件处理器（使用 RotatingFileHandler 实现轮转）
    log_file = log_dir / "monitor.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)

    # 使用 structlog 记录配置信息
    structlog.get_logger().info(
        "logging_configured",
        log_file=str(log_file),
        max_bytes=max_bytes,
        backup_count=backup_count,
        development=development,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取日志记录器.

    Args:
        name: 日志名称，默认使用调用模块名

    Returns:
        配置好的日志记录器
    """
    return structlog.get_logger(name)


class RotatingFileSizeFilter(logging.Filter):
    """按文件大小轮转的过滤器（备用实现）."""

    def __init__(self, max_bytes: int):
        """初始化过滤器.

        Args:
            max_bytes: 单个日志文件最大大小
        """
        super().__init__()
        self.max_bytes = max_bytes
        self.current_size = 0
        self.file_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录."""
        # 估算日志大小（粗略估计）
        log_size = len(record.getMessage()) + 50  # 加上元数据的大致大小

        if self.current_size + log_size > self.max_bytes:
            # 触发轮转
            self.current_size = 0
            self.file_count += 1

            # 通知处理器轮转文件
            for handler in record.logger.handlers:
                if hasattr(handler, "doRollover"):
                    handler.doRollover()

        self.current_size += log_size
        return True
