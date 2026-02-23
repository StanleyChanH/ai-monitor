# AI Monitor

基于 Ollama 视觉模型的 AI 视频监控系统，用于检测异常人员或危险动作。

## 功能特性

- **流水线架构**：三阶段异步处理（抓取、处理、推理），推理不阻塞帧抓取
- **智能告警**：Webhook 推送 + 本地告警图片保存 + Termux 系统通知
- **熔断保护**：Circuit Breaker 模式防止 API 级联故障
- **自动重连**：摄像头断线自动重连，指数退避策略
- **日志轮转**：按大小自动轮转，防止磁盘占满
- **PM2 守护**：支持 PM2 进程管理和开机自启

## 架构

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
     (有界队列，丢弃旧帧)       (单帧缓冲)         (Webhook+Termux通知)
```

## 环境要求

- Python 3.12+
- Ollama 服务（运行 `qwen3-vl:4b-instruct-q4_K_M` 模型）
- IP 摄像头或视频流
- PM2（可选，用于进程守护）

## Termux 环境配置

由于 Termux 默认没有 `/tmp` 目录，需要设置环境变量：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export TMPDIR=$HOME/tmp
export TEMP=$HOME/tmp
export TMP=$HOME/tmp
export GIT_TMPDIR=$HOME/tmp
mkdir -p $HOME/tmp
```

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd ai-monitor

# 安装依赖
uv sync
```

## 配置

复制环境变量示例文件并编辑：

```bash
cp .env.example .env
vim .env
```

主要配置项：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MONITOR_CAM_URL` | `http://127.0.0.1:8080/shot.jpg` | 摄像头地址 |
| `MONITOR_OLLAMA_API` | `http://10.167.1.223:11434/api/generate` | Ollama API |
| `MONITOR_MODEL_NAME` | `qwen3-vl:4b-instruct-q4_K_M` | 模型名称 |
| `MONITOR_TARGET_WIDTH` | `640` | 图像缩放宽度 |
| `MONITOR_CAM_RECONNECT_ENABLED` | `true` | 启用自动重连 |
| `MONITOR_ENABLE_TERMUX_ALERTS` | `true` | 启用系统通知 |
| `MONITOR_LOG_MAX_BYTES` | `10485760` | 日志轮转大小 |
| `MONITOR_ALERT_COOLDOWN` | `60` | 告警冷却时间（秒） |

## 运行

### 方式一：PM2 进程守护（推荐用于生产环境）

```bash
# 使用管理脚本
chmod +x pm2.sh
./pm2.sh start    # 启动
./pm2.sh status   # 查看状态
./pm2.sh logs     # 查看日志
./pm2.sh restart  # 重启
./pm2.sh stop     # 停止
```

或直接使用 PM2 命令：

```bash
pm2 start ecosystem.config.js
pm2 logs ai-monitor
pm2 save  # 保存进程列表
```

开机自启动：

```bash
pm2 startup  # 生成启动命令，按提示执行
pm2 save    # 保存当前进程列表
```

### 方式二：使用启动脚本（开发调试）

```bash
chmod +x run.sh
./run.sh
```

### 方式三：直接运行

```bash
uv run -m src.main
```

按 `Ctrl+C` 优雅停止监控。

## 输出

### 日志

日志输出到 `logs/` 目录：

```
logs/
├── pm2/              # PM2 日志
│   ├── combined.log
│   ├── out.log
│   └── error.log
└── monitor.log       # 应用日志（自动轮转）
```

### 告警图片

检测到异常时，图片保存到 `alerts/` 目录：

```
alerts/
├── alert_20260223_144709.jpg
├── alert_20260223_151234.jpg
└── ...
```

## 项目结构

```
ai-monitor/
├── src/                    # 源代码
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志系统（支持轮转）
│   ├── metrics.py         # 性能统计
│   ├── alert.py           # 告警处理
│   ├── retry.py           # 重试机制
│   ├── circuit_breaker.py # 熔断器
│   ├── termux_alert.py    # Termux-API 集成
│   ├── monitor.py         # 核心流水线
│   └── main.py            # 入口
├── logs/                   # 日志目录
├── alerts/                 # 告警图片
├── ecosystem.config.js     # PM2 配置
├── pm2.sh                  # PM2 管理脚本
├── run.sh                  # 启动脚本
├── .env.example            # 环境变量示例
├── pyproject.toml          # 依赖配置
├── README.md               # 项目文档
└── docs/                   # 设计文档
    └── plans/
        └── 2026-02-23-optimization-design.md
```

## 性能指标

运行时输出各阶段性能统计：

| 阶段 | 平均 | P50 | P95 | P99 |
|------|------|-----|-----|-----|
| Capture | 0.010s | 0.011s | 0.011s | 0.011s |
| Process | 0.022s | 0.021s | 0.024s | 0.024s |
| Inference | 0.051s | 0.052s | 0.052s | 0.052s |

## 故障处理

| 场景 | 处理方式 |
|------|---------|
| 摄像头断开 | 自动重连，指数退避（2s → 60s） |
| Ollama API 失败 | 熔断器保护，60s 后尝试恢复 |
| 网络超时 | 自动重试，最多 3 次 |
| 异常告警 | 冷却时间内不重复触发 |

## License

MIT
