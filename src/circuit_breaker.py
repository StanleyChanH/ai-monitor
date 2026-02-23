"""熔断器模块 - Circuit Breaker 模式实现."""

import asyncio
import time
from enum import Enum
from typing import Any, Final

from .logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """熔断器状态."""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态（拒绝请求）
    HALF_OPEN = "half_open"  # 半开状态（尝试恢复）


class CircuitBreakerError(Exception):
    """熔断器异常."""

    pass


class CircuitBreaker:
    """熔断器实现.

    状态转换：
        CLOSED → OPEN（失败次数达到阈值）
        OPEN → HALF_OPEN（超时后尝试恢复）
        HALF_OPEN → CLOSED（连续成功达到阈值）
        HALF_OPEN → OPEN（再次失败）
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        name: str = "circuit_breaker",
    ) -> None:
        """初始化熔断器.

        Args:
            failure_threshold: 失败阈值（达到后熔断）
            success_threshold: 恢复阈值（连续成功次数）
            timeout: 熔断超时时间（秒）后尝试恢复
            name: 熔断器名称（用于日志）
        """
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout
        self._name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        """获取当前状态."""
        return self._state

    @property
    def failure_count(self) -> int:
        """获取失败计数."""
        return self._failure_count

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置."""
        return time.time() - self._opened_at >= self._timeout

    def record_success(self) -> None:
        """记录成功."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            if self._success_count >= self._success_threshold:
                logger.info(
                    "circuit_breaker_closed",
                    name=self._name,
                    success_count=self._success_count,
                )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        else:
            # CLOSED 状态下的成功重置失败计数
            if self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self) -> None:
        """记录失败."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # HALF_OPEN 状态下的失败立即熔断
            logger.warning(
                "circuit_breaker_reopened",
                name=self._name,
                failure_count=self._failure_count,
            )
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
            self._success_count = 0
        elif self._failure_count >= self._failure_threshold:
            # 达到失败阈值，熔断
            logger.warning(
                "circuit_breaker_opened",
                name=self._name,
                failure_count=self._failure_count,
                threshold=self._failure_threshold,
            )
            self._state = CircuitState.OPEN
            self._opened_at = time.time()

    def call(self, *args: Any, **kwargs: Any) -> Any:
        """同步调用保护.

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerError: 熔断器开启时
        """
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    "circuit_breaker_half_open",
                    name=self._name,
                )
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self._name}' is OPEN. "
                    f"Rejecting request."
                )

        return args[0](**kwargs) if args else None

    async def call_async(self, func, *args: Any, **kwargs: Any) -> Any:
        """异步调用保护.

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerError: 熔断器开启时
        """
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    "circuit_breaker_half_open",
                    name=self._name,
                )
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self._name}' is OPEN. "
                    f"Rejecting request."
                )

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def reset(self) -> None:
        """重置熔断器."""
        logger.info(
            "circuit_breaker_reset",
            name=self._name,
        )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._opened_at = 0.0

    def __repr__(self) -> str:
        """字符串表示."""
        return (
            f"CircuitBreaker(name={self._name!r}, "
            f"state={self._state.value}, "
            f"failures={self._failure_count}/{self._failure_threshold})"
        )
