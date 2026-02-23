"""告警数据类型定义."""

import time
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    """告警严重程度."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertEvent:
    """告警事件."""

    message: str
    severity: AlertSeverity
    image_data: bytes | None = None
    analysis: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """初始化时间戳."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()
