# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered video surveillance monitoring system that captures camera frames and analyzes them using vision models (Ollama or Zhipu GLM-4V) to detect suspicious activities or dangerous actions.

## Architecture

### Pipeline Architecture (v0.2.0)

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
| `MONITOR_CAM_URL` | `http://127.0.0.1:8080/shot.jpg` | Camera endpoint |
| `MONITOR_INFERENCE_PROVIDER` | `ollama` | Inference provider: `ollama` or `zhipu` |
| `MONITOR_OLLAMA_API` | `http://10.167.1.223:11434/api/generate` | Ollama API (when provider=ollama) |
| `MONITOR_MODEL_NAME` | `qwen3-vl:4b-instruct-q4_K_M` | Vision model (Ollama) |
| `MONITOR_ZHIPU_API_KEY` | - | Zhipu API Key (when provider=zhipu) |
| `MONITOR_ZHIPU_MODEL` | `glm-4v-flash` | Vision model (Zhipu) |
| `MONITOR_TARGET_WIDTH` | `640` | Image resize width |
| `MONITOR_CAM_RECONNECT_ENABLED` | `true` | Auto-reconnect on camera disconnect |
| `MONITOR_ENABLE_TERMUX_ALERTS` | `true` | Enable Termux-API alerts |
| `MONITOR_LOG_MAX_BYTES` | `10485760` | Log rotation size (10MB) |

## Code Notes

- **Target Platform**: Termux/Android environment
- **Language**: All comments and UI strings in Chinese
- **Async-First**: Built on asyncio with concurrent pipeline stages
- **Fault Tolerance**: Retry, circuit breaker, auto-reconnect
- **Logging**: Structured with rotation, both console and file
- **Termux-Specific**: `/tmp` workaround in `run.sh` and `ecosystem.config.js`

## Project Structure

```
ai-monitor/
├── src/                    # Source code
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging with rotation
│   ├── metrics.py         # Performance metrics
│   ├── alert.py           # Alert handling
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

## Key Features Implemented (v0.2.0)

1. **Pipeline Architecture**: Non-blocking inference, frame capture continues during processing
2. **Multi-Provider Inference**: Supports both Ollama (local) and Zhipu GLM-4V (cloud)
3. **Alert System**: Webhook + local images + Termux-API (vibration, notification, toast)
4. **Circuit Breaker**: Protects against API failures with auto-recovery
5. **Auto-Reconnect**: Camera disconnect handling with exponential backoff
6. **Log Rotation**: Prevents disk space issues (10MB per file, 5 backups)
7. **PM2 Integration**: Process management for persistent operation
8. **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
