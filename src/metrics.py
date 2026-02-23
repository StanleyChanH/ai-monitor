"""性能统计模块 - 记录各阶段耗时统计."""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Final


@dataclass
class StageMetrics:
    """单个阶段的性能指标."""

    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    # 保留最近 100 次记录用于计算 p50/p95/p99
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))

    def record(self, duration: float) -> None:
        """记录一次耗时."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.recent_times.append(duration)

    @property
    def avg_time(self) -> float:
        """平均耗时."""
        return self.total_time / self.count if self.count > 0 else 0.0

    @property
    def p50_time(self) -> float:
        """中位数耗时."""
        if not self.recent_times:
            return 0.0
        sorted_times = sorted(self.recent_times)
        return sorted_times[len(sorted_times) // 2]

    @property
    def p95_time(self) -> float:
        """P95 耗时."""
        if not self.recent_times:
            return 0.0
        sorted_times = sorted(self.recent_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def p99_time(self) -> float:
        """P99 耗时."""
        if not self.recent_times:
            return 0.0
        sorted_times = sorted(self.recent_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def reset(self) -> None:
        """重置统计."""
        self.count = 0
        self.total_time = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0
        self.recent_times.clear()

    def as_dict(self) -> dict:
        """转换为字典."""
        return {
            "name": self.name,
            "count": self.count,
            "avg": f"{self.avg_time:.3f}s",
            "min": f"{self.min_time:.3f}s" if self.min_time != float("inf") else "N/A",
            "max": f"{self.max_time:.3f}s",
            "p50": f"{self.p50_time:.3f}s",
            "p95": f"{self.p95_time:.3f}s",
            "p99": f"{self.p99_time:.3f}s",
        }


class PipelineMetrics:
    """监控流水线性能指标."""

    STAGE_CAPTURE: Final = "capture"
    STAGE_PROCESS: Final = "process"
    STAGE_INFERENCE: Final = "inference"

    def __init__(self) -> None:
        """初始化性能指标."""
        self._stages: dict[str, StageMetrics] = {
            self.STAGE_CAPTURE: StageMetrics(self.STAGE_CAPTURE),
            self.STAGE_PROCESS: StageMetrics(self.STAGE_PROCESS),
            self.STAGE_INFERENCE: StageMetrics(self.STAGE_INFERENCE),
        }
        self.alert_count: int = 0
        self._start_time: float = time.time()

    def record(self, stage: str, duration: float) -> None:
        """记录阶段耗时."""
        if stage in self._stages:
            self._stages[stage].record(duration)

    def increment_alert(self) -> None:
        """增加告警计数."""
        self.alert_count += 1

    def get_stage(self, stage: str) -> StageMetrics | None:
        """获取阶段指标."""
        return self._stages.get(stage)

    @property
    def uptime(self) -> float:
        """运行时长（秒）."""
        return time.time() - self._start_time

    @property
    def capture(self) -> StageMetrics:
        """捕获阶段指标."""
        return self._stages[self.STAGE_CAPTURE]

    @property
    def process(self) -> StageMetrics:
        """处理阶段指标."""
        return self._stages[self.STAGE_PROCESS]

    @property
    def inference(self) -> StageMetrics:
        """推理阶段指标."""
        return self._stages[self.STAGE_INFERENCE]

    def summary(self) -> dict:
        """获取汇总统计."""
        return {
            "uptime": f"{self.uptime:.1f}s",
            "stages": {k: v.as_dict() for k, v in self._stages.items()},
            "alerts": self.alert_count,
        }

    def reset(self) -> None:
        """重置所有统计."""
        for stage in self._stages.values():
            stage.reset()
        self.alert_count = 0
        self._start_time = time.time()


class Timer:
    """计时器上下文管理器."""

    def __init__(self, metrics: PipelineMetrics, stage: str) -> None:
        """初始化计时器.

        Args:
            metrics: 性能指标对象
            stage: 阶段名称
        """
        self._metrics = metrics
        self._stage = stage
        self._start: float | None = None

    def __enter__(self) -> "Timer":
        """进入上下文."""
        self._start = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        """退出上下文."""
        if self._start is not None:
            duration = time.time() - self._start
            self._metrics.record(self._stage, duration)
