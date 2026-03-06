"""配置管理模块 - 使用环境变量和默认值."""

import os
from dataclasses import dataclass, field
from pathlib import Path


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

    # 动作检测（IP Webcam 传感器）
    motion_detection_enabled: bool = field(
        default_factory=lambda: _get_bool_env("MONITOR_MOTION_DETECTION_ENABLED", False)
    )
    motion_check_interval: float = field(
        default_factory=lambda: _get_float_env("MONITOR_MOTION_CHECK_INTERVAL", 0.5)
    )

    # 推理配置
    inference_provider: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_INFERENCE_PROVIDER", "ollama"
        ).lower()
    )
    inference_timeout: float = field(
        default_factory=lambda: _get_float_env("MONITOR_INFERENCE_TIMEOUT", 30.0)
    )

    # Ollama（当 provider=ollama 时使用）
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

    # Zhipu 智谱 AI（当 provider=zhipu 时使用）
    zhipu_api_key: str = field(
        default_factory=lambda: os.getenv("MONITOR_ZHIPU_API_KEY", "")
    )
    zhipu_api_url: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_ZHIPU_API_URL",
            "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        )
    )
    zhipu_model: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_ZHIPU_MODEL", "glm-4v-flash"
        )
    )

    # OpenAI 兼容（当 provider=openai 时使用）
    # 支持：OpenAI GPT-4V、vLLM、LocalAI 等兼容服务
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("MONITOR_OPENAI_API_KEY", "")
    )
    openai_api_url: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_OPENAI_API_URL",
            "http://localhost:8000/v1/chat/completions"  # 默认 vLLM 地址
        )
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("MONITOR_OPENAI_MODEL", "")
    )

    # 推理提示词（所有提供商共用）
    inference_prompt: str = field(
        default_factory=lambda: os.getenv(
            "MONITOR_INFERENCE_PROMPT",
            """你是一名专业的安防监控专家。请仔细观察图片，识别是否存在以下情况：
- 陌生人未经授权进入、徘徊或试图遮挡镜头；
- 暴力行为、摔倒、求救手势或持械等危险动作；
- 烟雾、火光或室内物品异常倾倒。
- 人类有攻击性动作。
- 等等
必须回答 'ALERT'（存在上述任一风险）或 'SAFE'（环境正常安全），并简述理由。"""
        )
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
        # 验证推理提供商
        valid_providers = {"ollama", "zhipu", "openai"}
        if self.inference_provider not in valid_providers:
            raise ValueError(
                f"inference_provider must be one of {valid_providers}, "
                f"got {self.inference_provider}"
            )

        # 验证 Zhipu API Key（如果使用 zhipu）
        if self.inference_provider == "zhipu" and not self.zhipu_api_key:
            raise ValueError(
                "zhipu_api_key is required when inference_provider is 'zhipu'"
            )

        # 验证 OpenAI Model（如果使用 openai）
        if self.inference_provider == "openai" and not self.openai_model:
            raise ValueError(
                "openai_model is required when inference_provider is 'openai'"
            )

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

        # 计算动作传感器 URL（从 cam_url 推导）
        self._motion_sensor_url: str | None = None
        if self.motion_detection_enabled:
            # 从 http://host:port/shot.jpg 提取 http://host:port
            base_url = self.cam_url.rsplit("/", 1)[0]
            self._motion_sensor_url = f"{base_url}/sensors.json?sense=motion_active"

    def display(self) -> str:
        """显示配置信息."""
        lines = [
            "=== AI Monitor 配置 ===",
            f"摄像头: {self.cam_url}",
            f"推理提供商: {self.inference_provider}",
        ]

        # 根据提供商显示不同的配置
        if self.inference_provider == "ollama":
            lines.append(f"Ollama API: {self.ollama_api}")
            lines.append(f"模型: {self.model_name}")
        elif self.inference_provider == "zhipu":
            lines.append(f"智谱 API: {self.zhipu_api_url}")
            lines.append(f"模型: {self.zhipu_model}")
        else:  # openai
            lines.append(f"OpenAI API: {self.openai_api_url}")
            lines.append(f"模型: {self.openai_model}")

        lines.extend([
            f"目标宽度: {self.target_width}",
            f"检测间隔: {self.detection_interval}s",
            f"动作检测: {'启用' if self.motion_detection_enabled else '禁用'}",
            f"告警冷却: {self.alert_cooldown}s",
            f"日志级别: {self.log_level}",
            f"日志目录: {self.log_dir}",
            f"告警目录: {self.alert_image_dir}",
            "========================",
        ])
        return "\n".join(lines)

    @property
    def motion_sensor_url(self) -> str | None:
        """获取动作传感器 URL."""
        return self._motion_sensor_url
