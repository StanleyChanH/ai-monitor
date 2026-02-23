"""Termux-API 告警模块 - 系统通知和震动."""

import asyncio
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .alert_types import AlertEvent, AlertSeverity
from .logger import get_logger

logger = get_logger(__name__)


class VibrationPattern(Enum):
    """震动模式."""

    SHORT = "short"  # 短震动
    LONG = "long"  # 长震动
    ALERT = "alert"  # 告警震动（重复）


@dataclass
class TermuxAlertConfig:
    """Termux 告警配置."""

    enable_vibration: bool = True
    enable_notification: bool = True
    enable_toast: bool = True
    notification_channel: str = "ai_monitor"
    notification_sound: bool = True


class TermuxAlertHandler:
    """Termux API 告警处理器."""

    def __init__(self, config: TermuxAlertConfig | None = None) -> None:
        """初始化 Termux 告警处理器.

        Args:
            config: 告警配置
        """
        self._config = config or TermuxAlertConfig()
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """检查 termux-api 是否可用."""
        try:
            result = subprocess.run(
                ["termux-vibration", "-h"],
                capture_output=True,
                timeout=2,
            )
            available = result.returncode == 0
            logger.info(
                "termux_api_check",
                available=available,
            )
            return available
        except Exception as e:
            logger.warning(
                "termux_api_not_available",
                error=str(e),
            )
            return False

    async def handle_alert(self, event: AlertEvent) -> None:
        """处理告警事件.

        Args:
            event: 告警事件
        """
        if not self._available:
            logger.debug("termux_api_unavailable", message=event.message)
            return

        # 根据严重程度选择震动模式
        vibration = self._get_vibration_pattern(event.severity)

        tasks = []

        if self._config.enable_vibration:
            tasks.append(self._vibrate(vibration))

        if self._config.enable_notification:
            tasks.append(self._show_notification(event))

        if self._config.enable_toast:
            tasks.append(self._show_toast(event))

        # 并发执行所有告警
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _get_vibration_pattern(self, severity: AlertSeverity) -> VibrationPattern:
        """根据严重程度获取震动模式.

        Args:
            severity: 告警严重程度

        Returns:
            震动模式
        """
        if severity in (AlertSeverity.ERROR, AlertSeverity.CRITICAL):
            return VibrationPattern.ALERT
        return VibrationPattern.SHORT

    async def _vibrate(self, pattern: VibrationPattern) -> None:
        """震动设备.

        Args:
            pattern: 震动模式
        """
        try:
            match pattern:
                case VibrationPattern.SHORT:
                    duration_ms = 200
                case VibrationPattern.LONG:
                    duration_ms = 500
                case VibrationPattern.ALERT:
                    duration_ms = 1000

            proc = await asyncio.create_subprocess_exec(
                "termux-vibration",
                "-d",
                str(duration_ms),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                logger.debug(
                    "vibration_sent",
                    pattern=pattern.value,
                    duration=duration_ms,
                )
            else:
                logger.warning(
                    "vibration_failed",
                    stderr=stderr.decode(),
                )
        except Exception as e:
            logger.error("vibration_error", error=str(e))

    async def _show_notification(self, event: AlertEvent) -> None:
        """显示系统通知.

        Args:
            event: 告警事件
        """
        try:
            title = f"AI 监控: {event.severity.value.upper()}"
            content = event.message

            sound_flag = "-s" if self._config.notification_sound else ""

            proc = await asyncio.create_subprocess_exec(
                "termux-notification",
                "-t",
                title,
                "-c",
                content,
                sound_flag,
                "--id",
                "ai_monitor_alert",
                "--channel",
                self._config.notification_channel,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                logger.debug(
                    "notification_sent",
                    title=title,
                    content=content,
                )
            else:
                logger.warning(
                    "notification_failed",
                    stderr=stderr.decode(),
                )
        except Exception as e:
            logger.error("notification_error", error=str(e))

    async def _show_toast(self, event: AlertEvent) -> None:
        """显示 Toast 提示.

        Args:
            event: 告警事件
        """
        try:
            # Toast 只支持短消息
            message = event.message[:50] + "..." if len(event.message) > 50 else event.message

            proc = await asyncio.create_subprocess_exec(
                "termux-toast",
                "-b",
                "#ff4444",  # 背景色（红色）
                "-g",
                "bottom",  # 位置
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                logger.debug("toast_sent", message=message)
            else:
                logger.warning("toast_failed", stderr=stderr.decode())
        except Exception as e:
            logger.error("toast_error", error=str(e))


# 单例实例
_termux_alert_handler: TermuxAlertHandler | None = None


def get_termux_alert_handler() -> TermuxAlertHandler | None:
    """获取 Termux 告警处理器单例.

    Returns:
        TermuxAlertHandler 实例，如果不可用则返回 None
    """
    global _termux_alert_handler

    if _termux_alert_handler is None:
        _termux_alert_handler = TermuxAlertHandler()
        if not _termux_alert_handler._available:
            return None

    return _termux_alert_handler
