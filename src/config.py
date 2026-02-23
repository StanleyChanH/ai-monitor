"""配置管理模块 - 使用环境变量和默认值."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _get_bool_env(key: str, default: bool = False) -> bool:
    """从环境变量获取布尔值."""
    value = os.getenv(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def _get_int_env(key: str, default: int) -> int:
    """从环境变量获取整数值."""
    value = os.getenv(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


def _get_float_env(key: str, default: float) -> float:
    """从环境变量获取浮点数值."""
    value = os.getenv(key)
    if value is not None:
        try:
            return float(value)
        except ValueError:
            pass
    return default


def _get_path_env(key: str, default: str) -> Path:
    """从环境变量获取路径值."""
    return Path(os.getenv(key, default))


@dataclass
class Settings:
    """监控配置."""

    # 摄像头
    cam_url: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_CAM_URL", "http://127.0.0.1:8080/shot.jpg"
        )
    )
    cam_timeout: float = field(
        default_factory=lambda: _get_float_env("MONITOR_CAM_TIMEOUT", 10.0)
    )
    cam_reconnect_enabled: bool = field(
        default_factory=lambda: _get_bool_env("MONITOR_CAM_RECONNECT_ENABLED", True)
    )
    cam_reconnect_delay: float = field(
        default_factory=lambda: _get_float_env("MONITOR_CAM_RECONNECT_DELAY", 2.0)
    )
    cam_reconnect_max_delay: float = field(
        default_factory=lambda: _get_float_env("MONITOR_CAM_RECONNECT_MAX_DELAY", 60.0)
    )

    # Ollama
    ollama_api: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_OLLAMA_API", "http://10.167.1.223:11434/api/generate"
        )
    )
    model_name: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_MODEL_NAME", "qwen3-vl:4b-instruct-q4_K_M"
        )
    )
    inference_timeout: float = field(
        default_factory=lambda: _get_float_env("MONITOR_INFERENCE_TIMEOUT", 30.0)
    )

    # 性能
    target_width: int = field(
        default_factory=lambda: _get_int_env("MONITOR_TARGET_WIDTH", 640)
    )
    detection_interval: float = field(
        default_factory=lambda: _get_float_env("MONITOR_DETECTION_INTERVAL", 2.0)
    )
    frame_queue_size: int = field(
        default_factory=lambda: _get_int_env("MONITOR_FRAME_QUEUE_SIZE", 2)
    )
    processed_queue_size: int = field(
        default_factory=lambda: _get_int_env("MONITOR_PROCESSED_QUEUE_SIZE", 1)
    )

    # 告警
    webhook_url: str = field(
        default_factory=lambda: os.getenv("MONITOR_WEBHOOK_URL", "")
    )
    webhook_timeout: float = field(
        default_factory=lambda: _get_float_env("MONITOR_WEBHOOK_TIMEOUT", 5.0)
    )
    alert_cooldown: int = field(
        default_factory=lambda: _get_int_env("MONITOR_ALERT_COOLDOWN", 60)
    )
    enable_termux_alerts: bool = field(
        default_factory=lambda: _get_bool_env("MONITOR_ENABLE_TERMUX_ALERTS", True)
    )

    # 日志
    log_dir: Path = field(
        default_factory=lambda: _get_path_env("MONITOR_LOG_DIR", "./logs")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("MONITOR_LOG_LEVEL", "INFO").upper()
    )
    log_max_bytes: int = field(
        default_factory=lambda: _get_int_env("MONITOR_LOG_MAX_BYTES", 10 * 1024 * 1024)  # 10 MB
    )
    log_backup_count: int = field(
        default_factory=lambda: _get_int_env("MONITOR_LOG_BACKUP_COUNT", 5)
    )

    # 告警图片
    alert_image_dir: Path = field(
        default_factory=lambda: _get_path_env("MONITOR_ALERT_IMAGE_DIR", "./alerts")
    )
    save_alert_images: bool = field(
        default_factory=lambda: _get_bool_env("MONITOR_SAVE_ALERT_IMAGES", True)
    )

    # 重试配置
    max_retries: int = field(
        default_factory=lambda: _get_int_env("MONITOR_MAX_RETRIES", 3)
    )
    retry_base_delay: float = field(
        default_factory=lambda: _get_float_env("MONITOR_RETRY_BASE_DELAY", 1.0)
    )
    retry_max_delay: float = field(
        default_factory=lambda: _get_float_env("MONITOR_RETRY_MAX_DELAY", 10.0)
    )

    # 熔断器配置
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: _get_int_env(
            "MONITOR_CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5
        )
    )
    circuit_breaker_success_threshold: int = field(
        default_factory=lambda: _get_int_env(
            "MONITOR_CIRCUIT_BREAKER_SUCCESS_THRESHOLD", 2
        )
    )
    circuit_breaker_timeout: float = field(
        default_factory=lambda: _get_float_env("MONITOR_CIRCUIT_BREAKER_TIMEOUT", 60.0)
    )

    def __post_init__(self):
        """配置验证."""
        # 验证日志级别
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got {self.log_level}"
            )
        self.log_level = self.log_level.upper()

        # 验证 Webhook URL
        if self.webhook_url and not (
            self.webhook_url.startswith("http://")
            or self.webhook_url.startswith("https://")
        ):
            raise ValueError(
                "webhook_url must start with http:// or https://, "
                f"got {self.webhook_url}"
            )

        # 确保路径是 Path 对象
        if not isinstance(self.log_dir, Path):
            self.log_dir = Path(self.log_dir)
        if not isinstance(self.alert_image_dir, Path):
            self.alert_image_dir = Path(self.alert_image_dir)

    def display(self) -> str:
        """显示配置信息."""
        lines = [
            "=== AI Monitor 配置 ===",
            f"摄像头: {self.cam_url}",
            f"Ollama API: {self.ollama_api}",
            f"模型: {self.model_name}",
            f"目标宽度: {self.target_width}",
            f"检测间隔: {self.detection_interval}s",
            f"告警冷却: {self.alert_cooldown}s",
            f"日志级别: {self.log_level}",
            f"日志目录: {self.log_dir}",
            f"告警目录: {self.alert_image_dir}",
            "========================",
        ]
        return "\n".join(lines)
