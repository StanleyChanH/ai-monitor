# AI Monitor 优化设计文档

**日期**: 2026-02-23
**状态**: ✅ 已完成
**环境**: Android Termux

---

## 实施结果

### 完成状态

| 阶段 | 内容 | 优先级 | 状态 |
|------|------|--------|------|
| Phase 1 | 核心重构：生产者消费者流水线 | 高 | ✅ 完成 |
| Phase 2 | 告警系统：Webhook + 本地日志 | 高 | ✅ 完成 |
| Phase 3 | 可观测性：结构化日志 + 性能指标 | 中 | ✅ 完成 |
| Phase 4 | 容错增强：重试 + 熔断 | 中 | ✅ 完成 |

### 额外实施功能

| 功能 | 状态 |
|------|------|
| Termux-API 集成（震动、通知、Toast） | ✅ 完成 |
| 日志文件轮转（RotatingFileHandler） | ✅ 完成 |
| 摄像头自动重连（指数退避） | ✅ 完成 |
| PM2 进程守护配置 | ✅ 完成 |
| 信号处理优化（优雅关闭） | ✅ 完成 |

### 变更说明

1. **配置管理**：移除 Pydantic，改用 dataclasses + 环境变量（Termux 兼容）
2. **依赖简化**：仅保留 httpx、pillow、structlog、aiofiles
3. **告警任务追踪**：修复告警任务丢失问题
4. **信号处理**：修复 SIGINT/SIGTERM 无法停止流水线的问题

---

## 原设计文档

## 1. 概述

本文档描述 AI Monitor 项目的优化设计方案，主要解决推理延迟导致卡顿和缺少实际告警动作两个核心问题。

### 当前问题
- **推理延迟阻塞**: Ollama API 响应时间较长（数秒），导致整个监控循环阻塞
- **缺少告警机制**: 仅打印输出，无实际通知或记录
- **可观测性不足**: 无性能统计和结构化日志

### 优化目标
- 解耦抓取、处理、推理三个阶段，实现流水线并行
- 添加 Webhook 推送和本地日志告警
- 引入结构化日志和性能指标统计
- 增强容错能力（重试、熔断）

---

## 2. 架构设计

### 2.1 整体架构

```
                    ┌──────────────────────────────────────┐
                    │           Main Event Loop             │
                    └──────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │  Capture Task │       │ Process Task  │       │ Inference Task│
    │   (抓取帧)     │───▶   │  (缩放+编码)   │───▶   │  (Ollama API) │
    │               │       │               │       │               │
    │ ~0.1s         │       │ ~0.2s         │       │ ~3-5s         │
    └───────────────┘       └───────────────┘       └───────────────┘
            │                         │                         │
            ▼                         ▼                         ▼
     frame_queue(2)           processed_queue(1)          alert_handler
     (有界队列，丢弃旧帧)       (单帧缓冲)
```

### 2.2 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 队列深度 | frame_queue=2, processed_queue=1 | 平衡实时性与资源占用 |
| 旧帧处理 | 丢弃覆盖 | 保证分析的是最新画面 |
| 并发模型 | asyncio | 异步 I/O 密集型任务最佳选择 |
| 配置管理 | dataclasses + 环境变量 | Termux 兼容性 |

---

## 3. 组件设计

### 3.1 文件结构

```
ai-monitor/
├── pyproject.toml          # 依赖配置
├── .env.example            # 环境变量示例
├── README.md
├── CLAUDE.md
│
├── src/
│   ├── __init__.py
│   ├── config.py           # 配置管理 (dataclasses)
│   ├── logger.py           # 日志设置 (structlog)
│   ├── metrics.py          # 性能统计
│   ├── retry.py            # 重试机制
│   ├── circuit_breaker.py  # 熔断器
│   ├── alert.py            # 告警处理
│   ├── monitor.py          # 核心监控逻辑
│   └── main.py             # 入口
│
├── logs/                   # 日志目录
├── alerts/                 # 告警截图
└── tests/                  # 测试
```

### 3.2 配置管理 (config.py)

使用 dataclasses 实现配置管理：

```python
@dataclass
class Settings:
    cam_url: str = field(default_factory=lambda: os.getenv("MONITOR_CAM_URL", "..."))
    ollama_api: str = field(default_factory=lambda: os.getenv("MONITOR_OLLAMA_API", "..."))
    # ...
```

### 3.3 日志系统 (logger.py)

使用 structlog 实现结构化日志：
- 开发环境：彩色控制台输出
- 生产环境：文件轮转 + JSON 格式

### 3.4 性能统计 (metrics.py)

记录各阶段耗时统计：
- 捕获阶段平均/最小/最大耗时
- 处理阶段平均/最小/最大耗时
- 推理阶段平均/最小/最大耗时
- 告警总数

### 3.5 告警系统 (alert.py)

功能：
- 告警去重（冷却时间内相同类型不重复告警）
- Webhook 推送
- 告警图片本地保存（时间戳命名）
- 告警日志记录

### 3.6 核心监控 (monitor.py)

MonitorPipeline 类管理整个监控流程：

```python
class MonitorPipeline:
    async def start(self):
        # 启动三个并发 worker
        self._tasks = [
            asyncio.create_task(self._capture_worker()),
            asyncio.create_task(self._process_worker()),
            asyncio.create_task(self._inference_worker()),
        ]
```

---

## 4. 容错设计

### 4.1 重试机制

指数退避重试装饰器：
- 最大尝试次数：3
- 基础延迟：1s
- 最大延迟：10s
- 退避倍数：2x

### 4.2 熔断器

Circuit Breaker 模式：
- 失败阈值：5 次
- 恢复阈值：2 次连续成功
- 超时时间：60s
- 三种状态：CLOSED → OPEN → HALF_OPEN → CLOSED

### 4.3 优雅关闭

响应 SIGTERM/SIGINT 信号：
1. 停止接受新任务
2. 等待当前任务完成
3. 关闭 HTTP 连接
4. 输出最终统计信息

---

## 5. 实际收益

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 推理延迟阻塞 | 完全阻塞流水线 | 不阻塞抓取 |
| 实际帧率 | 受推理时间限制 | 稳定在配置值 |
| 告警通知 | 仅打印 | Webhook + 日志 + 图片 |
| 可观测性 | 无 | 结构化日志 + p50/p95/p99 |
| 稳定性 | 单点失败 | 重试 + 熔断 |

---

## 6. Termux 特定配置

### 6.1 PM2 配置（生产环境）

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'ai-monitor',
    script: 'uv',
    args: 'run -m src.main',
    autorestart: true,
    max_restarts: 20,
    min_uptime: '10s',
    max_memory_restart: '500M',
    env: {
      TMPDIR: '$HOME/tmp',
      MONITOR_LOG_LEVEL: 'INFO',
      MONITOR_ENABLE_TERMUX_ALERTS: 'true',
      MONITOR_CAM_RECONNECT_ENABLED: 'true',
    },
  }],
};
```

### 6.2 run.sh 启动脚本

```bash
#!/bin/bash
# 设置临时目录环境变量
export TMPDIR="$HOME/tmp"
export TEMP="$HOME/tmp"
export TMP="$HOME/tmp"
export GIT_TMPDIR="$HOME/tmp"
mkdir -p "$HOME/tmp"

# 启动监控
cd "$(dirname "$0")"
uv run -m src.main "$@"
```

### 6.3 Termux 注意事项

1. 确保有项目目录的写权限
2. 在 Termux 设置中禁用电池优化（避免后台网络限制）
3. 安装 termux-api：`pkg install termux-api`
4. PM2 开机自启：`pm2 startup` → 按提示执行 → `pm2 save`
