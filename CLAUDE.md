# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered video surveillance monitoring system that captures camera frames and analyzes them using vision models (Ollama or Zhipu GLM-4V) to detect suspicious activities or dangerous actions.

## Architecture

### Pipeline Architecture (v0.3.0)

Three-stage async pipeline with parallel execution:

```
Capture Worker (抓取) → Process Worker (处理) → Inference Worker (推理)
     ↓ 0.1s                ↓ 0.2s                    ↓ 3-5s
 frame_queue(2)      processed_queue(1)         alert_handler
```

**Key Components:**

| Module | Description |
|--------|-------------|
| `src/config.py` | Configuration management (environment variables + dataclasses) |
| `src/logger.py` | Structured logging with rotation (RotatingFileHandler) |
| `src/metrics.py` | Performance statistics (p50/p95/p99 latencies) |
| `src/alert.py` | Alert handling (Webhook + local images + Termux API) |
| `src/alert_types.py` | Alert data types (`AlertEvent`, `AlertSeverity`) |
| `src/retry.py` | Exponential backoff retry decorator |
| `src/circuit_breaker.py` | Circuit Breaker pattern for API protection |
| `src/termux_alert.py` | Termux-API integration (vibration, notification, toast) |
| `src/monitor.py` | Core pipeline (MonitorPipeline class) |
| `src/main.py` | Application entry point with signal handling |

## Dependencies

```toml
dependencies = [
    "httpx>=0.28.1",      # Async HTTP client
    "pillow>=12.1.1",     # Image processing
    "structlog>=24.0.0",  # Structured logging
    "aiofiles>=24.0.0",   # Async file operations
]
```

**Note**: Pydantic was removed for Termux compatibility (no Rust build required).

## Common Commands

```bash
# Install dependencies
uv sync

# Run with PM2 (production)
./pm2.sh start

# Run directly (development)
uv run -m src.main
# or
./run.sh

# Add a dependency
uv add <package>
```

## Configuration

All settings via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| **摄像头** |||
| `MONITOR_CAM_URL` | `http://127.0.0.1:8080/shot.jpg` | Camera endpoint |
| `MONITOR_CAM_TIMEOUT` | `10.0` | Camera connection timeout (seconds) |
| `MONITOR_CAM_RECONNECT_ENABLED` | `true` | Auto-reconnect on camera disconnect |
| `MONITOR_CAM_RECONNECT_DELAY` | `2.0` | Initial reconnect delay (seconds) |
| **动作检测** |||
| `MONITOR_MOTION_DETECTION_ENABLED` | `false` | Enable motion-triggered detection |
| `MONITOR_MOTION_CHECK_INTERVAL` | `0.5` | Motion sensor check interval (seconds) |
| **推理** |||
| `MONITOR_INFERENCE_PROVIDER` | `ollama` | Inference provider: `ollama` or `zhipu` |
| `MONITOR_INFERENCE_TIMEOUT` | `30.0` | Inference timeout (seconds) |
| `MONITOR_DETECTION_INTERVAL` | `2.0` | Inference interval (seconds) |
| `MONITOR_INFERENCE_PROMPT` | *(内置默认)* | 推理提示词（所有提供商共用） |
| **Ollama** |||
| `MONITOR_OLLAMA_API` | `http://10.167.1.223:11434/api/generate` | Ollama API (when provider=ollama) |
| `MONITOR_MODEL_NAME` | `qwen3-vl:4b-instruct-q4_K_M` | Vision model (Ollama) |
| **智谱** |||
| `MONITOR_ZHIPU_API_KEY` | - | Zhipu API Key (when provider=zhipu) |
| `MONITOR_ZHIPU_MODEL` | `glm-4v-flash` | Vision model (Zhipu) |
| **OpenAI 兼容** |||
| `MONITOR_OPENAI_API_KEY` | - | OpenAI API Key (optional for local) |
| `MONITOR_OPENAI_API_URL` | `http://localhost:8000/v1/chat/completions` | OpenAI API URL |
| `MONITOR_OPENAI_MODEL` | - | Vision model (required) |
| **告警** |||
| `MONITOR_WEBHOOK_URL` | - | Webhook URL for alerts |
| `MONITOR_ALERT_COOLDOWN` | `60` | Alert cooldown (seconds) |
| `MONITOR_ENABLE_TERMUX_ALERTS` | `true` | Enable Termux-API alerts |
| **性能/日志** |||
| `MONITOR_TARGET_WIDTH` | `640` | Image resize width |
| `MONITOR_LOG_MAX_BYTES` | `10485760` | Log rotation size (10MB) |
| `MONITOR_LOG_LEVEL` | `INFO` | Log level |

## Code Notes

- **Target Platform**: Termux/Android environment
- **Language**: All comments and UI strings in Chinese
- **Async-First**: Built on asyncio with concurrent pipeline stages
- **Fault Tolerance**: Retry, circuit breaker, auto-reconnect
- **Logging**: Structured with rotation, both console and file
- **Termux-Specific**: `/tmp` workaround in `run.sh` and `ecosystem.config.js`
- **Motion Detection**: Uses IP Webcam's `/sensors.json?sense=motion_active` endpoint; falls back to always-capture if sensor unavailable

## Project Structure

```
ai-monitor/
├── src/                    # Source code
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging with rotation
│   ├── metrics.py         # Performance metrics
│   ├── alert.py           # Alert handling
│   ├── alert_types.py     # Alert data types
│   ├── retry.py           # Retry decorator
│   ├── circuit_breaker.py # Circuit breaker
│   ├── termux_alert.py    # Termux-API alerts
│   ├── monitor.py         # Core pipeline
│   └── main.py            # Entry point
├── logs/                   # Application logs
├── alerts/                 # Alert images
├── ecosystem.config.js     # PM2 configuration
├── pm2.sh                  # PM2 management script
├── run.sh                  # Direct run script
├── .env.example            # Environment template
├── pyproject.toml          # Dependencies
├── README.md               # User documentation
├── CLAUDE.md               # This file
└── docs/
    └── plans/
        └── 2026-02-23-optimization-design.md  # Design document
```

## Key Features Implemented (v0.3.0)

1. **Pipeline Architecture**: Non-blocking inference, frame capture continues during processing
2. **Multi-Provider Inference**: Supports Ollama (local), Zhipu GLM-4V (cloud), and OpenAI-compatible APIs (vLLM, LocalAI, etc.)
3. **Motion Detection**: IP Webcam sensor integration - only triggers inference when motion detected (saves power/bandwidth)
4. **Alert System**: Webhook + local images + Termux-API (vibration, notification, toast)
5. **Circuit Breaker**: Protects against API failures with auto-recovery
6. **Auto-Reconnect**: Camera disconnect handling with exponential backoff
7. **Log Rotation**: Prevents disk space issues (10MB per file, 5 backups)
8. **PM2 Integration**: Process management for persistent operation
9. **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
