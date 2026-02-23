"""告警系统模块 - Webhook 推送、告警图片保存、告警去重、Termux API."""

import asyncio
import time
from enum import Enum
from pathlib import Path
from typing import Any, Final

import aiofiles
import httpx

from .alert_types import AlertEvent, AlertSeverity
from .logger import get_logger
from .metrics import PipelineMetrics
from .termux_alert import get_termux_alert_handler

logger = get_logger(__name__)


class WebhookType(Enum):
    """Webhook 类型."""

    GENERIC = "generic"  # 通用格式
    FEISHU = "feishu"    # 飞书


def detect_webhook_type(url: str) -> WebhookType:
    """根据 URL 检测 Webhook 类型.

    Args:
        url: Webhook URL

    Returns:
        Webhook 类型
    """
    if "feishu.cn" in url or "feishu" in url.lower():
        return WebhookType.FEISHU
    return WebhookType.GENERIC


class AlertHandler:
    """告警处理器."""

    def __init__(
        self,
        webhook_url: str,
        webhook_timeout: float,
        cooldown_seconds: int,
        alert_image_dir: Path,
        save_alert_images: bool = True,
        enable_termux: bool = True,
    ) -> None:
        """初始化告警处理器.

        Args:
            webhook_url: Webhook 推送地址
            webhook_timeout: Webhook 超时时间（秒）
            cooldown_seconds: 告警冷却时间（秒）
            alert_image_dir: 告警图片保存目录
            save_alert_images: 是否保存告警图片
            enable_termux: 是否启用 Termux API 告警
        """
        self._webhook_url = webhook_url
        self._webhook_timeout = webhook_timeout
        self._cooldown_seconds = cooldown_seconds
        self._alert_image_dir = alert_image_dir
        self._save_alert_images = save_alert_images
        self._enable_termux = enable_termux
        self._webhook_type = detect_webhook_type(webhook_url)

        # 确保目录存在
        if save_alert_images:
            self._alert_image_dir.mkdir(parents=True, exist_ok=True)

        # 告警冷却记录
        self._last_alert_time: float = 0.0
        self._last_alert_message: str = ""

        # Termux 告警处理器
        self._termux_handler = None
        if enable_termux:
            self._termux_handler = get_termux_alert_handler()
            if self._termux_handler:
                logger.info("termux_alert_enabled")

        logger.info(
            "alert_handler_initialized",
            webhook_type=self._webhook_type.value,
            webhook_url=webhook_url[:50] + "..." if webhook_url else "",
        )

    async def handle_alert(
        self,
        event: AlertEvent,
        metrics: PipelineMetrics | None = None,
    ) -> None:
        """处理告警事件.

        Args:
            event: 告警事件
            metrics: 性能指标对象
        """
        current_time = time.time()

        # 检查告警冷却
        time_since_last = current_time - self._last_alert_time
        if time_since_last < self._cooldown_seconds:
            logger.debug(
                "alert_in_cooldown",
                message=event.message,
                remaining=self._cooldown_seconds - time_since_last,
            )
            return

        # 记录告警
        if metrics:
            metrics.increment_alert()

        logger.warning(
            "alert_triggered",
            message=event.message,
            severity=event.severity.value,
            analysis=event.analysis,
        )

        # 保存告警图片
        if self._save_alert_images and event.image_data:
            await self._save_alert_image(event)

        # 发送 Webhook
        if self._webhook_url:
            await self._send_webhook(event)

        # Termux 系统告警（通知、震动、Toast）
        if self._termux_handler:
            await self._termux_handler.handle_alert(event)

        # 更新冷却状态
        self._last_alert_time = current_time
        self._last_alert_message = event.message

    async def _save_alert_image(self, event: AlertEvent) -> None:
        """保存告警图片.

        Args:
            event: 告警事件
        """
        if not event.image_data:
            return

        try:
            timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(event.timestamp))
            filename = f"alert_{timestamp_str}.jpg"
            filepath = self._alert_image_dir / filename

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(event.image_data)

            logger.info(
                "alert_image_saved",
                filepath=str(filepath),
                size=len(event.image_data),
            )
        except Exception as e:
            logger.error(
                "alert_image_save_failed",
                error=str(e),
            )

    async def _send_webhook(self, event: AlertEvent) -> None:
        """发送 Webhook 推送.

        Args:
            event: 告警事件
        """
        if not self._webhook_url:
            return

        # 根据 Webhook 类型构造 payload
        if self._webhook_type == WebhookType.FEISHU:
            payload = self._build_feishu_payload(event)
        else:
            payload = self._build_generic_payload(event)

        try:
            async with httpx.AsyncClient(timeout=self._webhook_timeout) as client:
                response = await client.post(self._webhook_url, json=payload)
                response.raise_for_status()

                logger.info(
                    "webhook_sent",
                    type=self._webhook_type.value,
                    status=response.status_code,
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                "webhook_http_error",
                status=e.response.status_code,
                response=e.response.text,
            )
        except Exception as e:
            logger.error(
                "webhook_failed",
                error=str(e),
            )

    def _build_generic_payload(self, event: AlertEvent) -> dict:
        """构造通用 Webhook payload.

        Args:
            event: 告警事件

        Returns:
            payload 字典
        """
        return {
            "message": event.message,
            "severity": event.severity.value,
            "analysis": event.analysis,
            "timestamp": event.timestamp,
            "has_image": event.image_data is not None,
        }

    def _build_feishu_payload(self, event: AlertEvent) -> dict:
        """构造飞书 Webhook payload.

        Args:
            event: 告警事件

        Returns:
            payload 字典
        """
        # 根据严重程度选择颜色
        color_map = {
            AlertSeverity.INFO: "blue",
            AlertSeverity.WARNING: "yellow",
            AlertSeverity.ERROR: "red",
            AlertSeverity.CRITICAL: "red",
        }
        color = color_map.get(event.severity, "red")

        # 格式化时间
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp))

        # 构造飞书卡片消息
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 AI 监控告警 - {event.severity.value.upper()}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**告警内容**\n{event.message}\n\n**分析结果**\n{event.analysis[:500]}",
                        },
                    },
                    {
                        "tag": "hr",
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": f"时间: {timestamp_str}",
                        },
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": f"是否有图片: {'是' if event.image_data else '否'}",
                        },
                    },
                ],
            },
        }

    def reset_cooldown(self) -> None:
        """重置告警冷却."""
        self._last_alert_time = 0.0
        self._last_alert_message = ""
        logger.debug("alert_cooldown_reset")
