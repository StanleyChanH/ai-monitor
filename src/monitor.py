"""核心监控模块 - 流水线架构实现."""

import asyncio
import base64
import io
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

import httpx
from PIL import Image

from .alert import AlertHandler
from .alert_types import AlertEvent, AlertSeverity
from .circuit_breaker import CircuitBreaker, CircuitBreakerError
from .config import Settings
from .logger import get_logger
from .metrics import PipelineMetrics, Timer

logger = get_logger(__name__)


class PipelineState(Enum):
    """流水线状态."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class ProcessedFrame:
    """处理后的帧数据."""

    image_b64: str  # Base64 编码的图像
    raw_bytes: bytes  # 原始图像字节（用于告警保存）
    timestamp: float  # 时间戳
    frame_id: int  # 帧序号


class MonitorPipeline:
    """监控流水线.

    实现三个阶段的异步流水线：
    1. Capture Worker - 抓取摄像头帧
    2. Process Worker - 缩放和编码
    3. Inference Worker - Ollama 推理和告警
    """

    # 帧抓取间隔
    CAPTURE_INTERVAL: Final = 0.1  # 10 FPS

    def __init__(self, settings: Settings) -> None:
        """初始化监控流水线.

        Args:
            settings: 配置对象
        """
        self._settings = settings
        self._state = PipelineState.STARTING

        # 队列
        self._frame_queue: asyncio.Queue[bytes] = asyncio.Queue(
            maxsize=settings.frame_queue_size
        )
        self._processed_queue: asyncio.Queue[ProcessedFrame] = asyncio.Queue(
            maxsize=settings.processed_queue_size
        )

        # 组件
        self._metrics = PipelineMetrics()
        self._alert_handler = AlertHandler(
            webhook_url=settings.webhook_url,
            webhook_timeout=settings.webhook_timeout,
            cooldown_seconds=settings.alert_cooldown,
            alert_image_dir=settings.alert_image_dir,
            save_alert_images=settings.save_alert_images,
            enable_termux=settings.enable_termux_alerts,
        )
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=settings.circuit_breaker_success_threshold,
            timeout=settings.circuit_breaker_timeout,
            name="ollama_api",
        )

        # HTTP 客户端（延迟初始化）
        self._http_client: httpx.AsyncClient | None = None

        # 任务控制
        self._tasks: list[asyncio.Task] = []
        self._alert_tasks: list[asyncio.Task] = []  # 追踪告警任务
        self._frame_counter: int = 0
        self._shutdown_event = asyncio.Event()
        self._alert_lock = asyncio.Lock()  # 保护告警任务列表

        # 摄像头重连状态
        self._cam_consecutive_errors: int = 0
        self._cam_last_error_time: float = 0.0
        self._cam_reconnect_delay: float = self._settings.cam_reconnect_delay

        # 推理间隔控制
        self._last_inference_time: float = 0.0

    async def start(self) -> None:
        """启动流水线."""
        logger.info(
            "pipeline_starting",
            cam_url=self._settings.cam_url,
            ollama_api=self._settings.ollama_api,
            model=self._settings.model_name,
        )

        # 初始化 HTTP 客户端
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        self._http_client = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(self._settings.inference_timeout),
        )

        # 启动三个 worker
        self._tasks = [
            asyncio.create_task(self._capture_worker(), name="capture"),
            asyncio.create_task(self._process_worker(), name="process"),
            asyncio.create_task(self._inference_worker(), name="inference"),
        ]

        self._state = PipelineState.RUNNING
        logger.info("pipeline_started", workers=len(self._tasks))

        # 等待关闭信号
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        """停止流水线."""
        if self._state != PipelineState.RUNNING:
            return

        logger.info("pipeline_stopping")
        self._state = PipelineState.STOPPING

        # 设置关闭事件
        self._shutdown_event.set()

        # 取消所有 worker 任务
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # 等待 worker 任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # 等待告警任务完成（最多等待 5 秒）
        async with self._alert_lock:
            if self._alert_tasks:
                logger.info(
                    "waiting_alert_tasks",
                    count=len(self._alert_tasks),
                )
                done, pending = await asyncio.wait(
                    self._alert_tasks,
                    timeout=5.0,
                )
                # 取消未完成的告警任务
                for task in pending:
                    task.cancel()
                logger.info(
                    "alert_tasks_completed",
                    done=len(done),
                    cancelled=len(pending),
                )

        # 关闭 HTTP 客户端
        if self._http_client:
            await self._http_client.aclose()

        self._state = PipelineState.STOPPED
        logger.info("pipeline_stopped", metrics=self._metrics.summary())

    async def _capture_worker(self) -> None:
        """捕获 worker - 持续抓取摄像头帧，支持自动重连."""
        logger.info("capture_worker_started", cam_url=self._settings.cam_url)

        while not self._shutdown_event.is_set():
            try:
                with Timer(self._metrics, PipelineMetrics.STAGE_CAPTURE):
                    response = await self._http_client.get(
                        self._settings.cam_url,
                        timeout=self._settings.cam_timeout,
                    )
                    response.raise_for_status()
                    frame_data = response.content

                # 连接成功，重置重连状态
                if self._cam_consecutive_errors > 0:
                    logger.info(
                        "camera_reconnected",
                        previous_errors=self._cam_consecutive_errors,
                    )
                    self._cam_consecutive_errors = 0
                    self._cam_reconnect_delay = self._settings.cam_reconnect_delay

                # 队列满时丢弃旧帧
                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass

                await self._frame_queue.put(frame_data)
                self._frame_counter += 1

            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                self._cam_consecutive_errors += 1
                self._cam_last_error_time = time.time()

                # 判断是否需要重连
                if self._settings.cam_reconnect_enabled:
                    logger.warning(
                        "camera_error",
                        error=str(e),
                        consecutive_errors=self._cam_consecutive_errors,
                        reconnect_delay=f"{self._cam_reconnect_delay:.1f}s",
                    )

                    # 等待后重试
                    await asyncio.sleep(self._cam_reconnect_delay)

                    # 指数退避，但不超过最大延迟
                    self._cam_reconnect_delay = min(
                        self._cam_reconnect_delay * 2,
                        self._settings.cam_reconnect_max_delay,
                    )
                else:
                    # 不重连，直接退出
                    logger.error("camera_error_no_reconnect", error=str(e))
                    break

            except Exception as e:
                # 其他未知错误
                logger.error(
                    "capture_unexpected_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await asyncio.sleep(self.CAPTURE_INTERVAL)

    async def _process_worker(self) -> None:
        """处理 worker - 缩放和编码图像."""
        logger.info("process_worker_started")

        while not self._shutdown_event.is_set():
            try:
                # 获取原始帧
                raw_bytes = await self._frame_queue.get()

                with Timer(self._metrics, PipelineMetrics.STAGE_PROCESS):
                    # 在线程池中执行图像处理
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        self._process_image,
                        raw_bytes,
                    )

                # 队列满时丢弃旧帧
                if self._processed_queue.full():
                    try:
                        self._processed_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass

                processed_frame = ProcessedFrame(
                    image_b64=result["image_b64"],
                    raw_bytes=raw_bytes,
                    timestamp=time.time(),
                    frame_id=self._frame_counter,
                )
                await self._processed_queue.put(processed_frame)

            except Exception as e:
                logger.error("process_error", error=str(e))

    async def _inference_worker(self) -> None:
        """推理 worker - 调用 Ollama API 并处理告警."""
        logger.info(
            "inference_worker_started",
            detection_interval=self._settings.detection_interval,
        )

        while not self._shutdown_event.is_set():
            try:
                processed_frame = await self._processed_queue.get()

                # 检测间隔控制：跳过未到间隔的帧
                current_time = time.time()
                elapsed = current_time - self._last_inference_time
                if elapsed < self._settings.detection_interval:
                    # 跳过此帧，不进行推理
                    continue

                self._last_inference_time = current_time

                with Timer(self._metrics, PipelineMetrics.STAGE_INFERENCE):
                    await self._run_inference(processed_frame)

            except Exception as e:
                logger.error("inference_error", error=str(e))

    def _process_image(self, raw_bytes: bytes) -> dict:
        """处理图像：缩放和 Base64 编码.

        Args:
            raw_bytes: 原始图像字节

        Returns:
            处理结果字典
        """
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # 计算缩放比例
            w, h = img.size
            scale = self._settings.target_width / float(w)
            target_height = int(float(h) * scale)

            # 等比缩放
            img = img.resize(
                (self._settings.target_width, target_height),
                Image.Resampling.LANCZOS,
            )

            # 转为 JPEG 字节流
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            return {
                "image_b64": image_b64,
                "original_size": (w, h),
                "resized_size": (self._settings.target_width, target_height),
            }

    async def _run_inference(self, frame: ProcessedFrame) -> None:
        """运行 Ollama 推理.

        Args:
            frame: 处理后的帧
        """
        prompt = """
            你是一名专业的安防监控专家。请仔细观察图片，识别是否存在以下情况：
            - 陌生人未经授权进入、徘徊或试图遮挡镜头；
            - 暴力行为、摔倒、求救手势或持械等危险动作；
            - 烟雾、火光或室内物品异常倾倒。
            - 人类有攻击性动作。
            - 等等
            必须回答 'ALERT'（存在上述任一风险）或 'SAFE'（环境正常安全），并简述理由。
        """

        payload = {
            "model": self._settings.model_name,
            "prompt": prompt,
            "images": [frame.image_b64],
            "stream": False,
        }

        try:
            # 通过熔断器保护
            response = await self._circuit_breaker.call_async(
                self._http_client.post,
                self._settings.ollama_api,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json().get("response", "")
                self._handle_inference_result(frame, result)
            else:
                logger.warning(
                    "inference_http_error",
                    status=response.status_code,
                )

        except CircuitBreakerError:
            logger.warning("inference_circuit_breaker_open")
        except Exception as e:
            logger.error("inference_request_error", error=str(e))

    def _handle_inference_result(self, frame: ProcessedFrame, result: str) -> None:
        """处理推理结果.

        Args:
            frame: 处理后的帧
            result: 推理结果文本
        """
        result_stripped = result.strip()
        is_alert = "ALERT" in result_stripped.upper()

        logger.info(
            "inference_result",
            frame_id=frame.frame_id,
            is_alert=is_alert,
            result=result_stripped[:200],  # 限制长度
        )

        if is_alert:
            event = AlertEvent(
                message=f"检测到异常状态！帧 ID: {frame.frame_id}",
                severity=AlertSeverity.WARNING,
                image_data=frame.raw_bytes if self._settings.save_alert_images else None,
                analysis=result_stripped,
                timestamp=frame.timestamp,
            )
            # 创建并追踪告警任务
            alert_task = asyncio.create_task(
                self._run_alert_with_cleanup(event)
            )

            # 添加到追踪列表
            asyncio.create_task(self._add_alert_task(alert_task))

    async def _run_alert_with_cleanup(self, event: AlertEvent) -> None:
        """运行告警处理并记录异常.

        Args:
            event: 告警事件
        """
        try:
            await self._alert_handler.handle_alert(event, self._metrics)
        except Exception as e:
            logger.error("alert_task_error", error=str(e))

    async def _add_alert_task(self, task: asyncio.Task) -> None:
        """添加告警任务到追踪列表.

        Args:
            task: 告警任务
        """
        async with self._alert_lock:
            self._alert_tasks.append(task)

        # 等待任务完成，然后从列表中移除
        try:
            await task
        finally:
            async with self._alert_lock:
                if task in self._alert_tasks:
                    self._alert_tasks.remove(task)

    @property
    def metrics(self) -> PipelineMetrics:
        """获取性能指标."""
        return self._metrics

    @property
    def state(self) -> PipelineState:
        """获取流水线状态."""
        return self._state
