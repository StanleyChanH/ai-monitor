<div align="center">

<img src="icon.png" alt="AI Monitor Logo" width="128" height="128">

# AI Monitor

**把旧手机变成智能安防监控终端**

基于视觉大模型的实时监控系统，运行在 Termux 环境中，
让你的 Android 手机具备 AI 识别能力。

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Termux](https://img.shields.io/badge/Platform-Termux-green.svg)](https://termux.com/)

</div>

---

## 为什么选择 AI Monitor？

> **旧手机别扔，让它守护你的安全**

传统安防方案要么价格昂贵，要么功能单一。AI Monitor 让你用一台闲置手机 + 免费的视觉模型，就能搭建一套智能监控系统：

| 对比项 | 传统摄像头 | 云监控服务 | **AI Monitor** |
|--------|-----------|-----------|----------------|
| 硬件成本 | ¥200-2000 | ¥100-500 | **¥0（旧手机）** |
| 月费 | 无 | ¥10-50/月 | **¥0** |
| AI 识别 | 无/额外付费 | 有限 | **有，可自定义** |
| 隐私保护 | ⚠️ 云存储 | ⚠️ 云处理 | **✅ 本地处理** |
| 告警方式 | App 推送 | App 推送 | **震动+通知+Webhook** |

---

## 使用场景

### 家庭安全
- 出门时监控门口是否有陌生人出现
- 检测家中是否有异常活动

### 宠物监护
- 监控宠物是否在捣乱（翻垃圾桶、挠沙发）
- 记录宠物的有趣瞬间

### 办公室/店铺
- 非工作时间检测异常入侵
- 监控重要区域的安全

### 老人/儿童看护
- 检测跌倒等危险动作
- 远程了解家中情况

---

## 架构亮点

```
┌─────────────────────────────────────────────────────────────────┐
│                        你的手机 (Termux)                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  IP Webcam  │───▶│  AI Monitor │───▶│   告警系统   │          │
│  │   (摄像头)   │    │   (推理)     │    │ (震动/通知)  │          │
│  └─────────────┘    └──────┬──────┘    └─────────────┘          │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Ollama 服务     │
                    │ (局域网/云服务器) │
                    │  视觉大模型推理   │
                    └─────────────────┘
```

**设计优势**：
- **手机端轻量运行**：只负责抓帧和告警，推理负载在服务器
- **非阻塞流水线**：推理 3-5 秒不影响帧抓取，不漏掉任何画面
- **完整容错机制**：熔断器 + 自动重连 + 优雅降级

---

## 功能特性

- **实时 AI 分析** - 使用 Ollama 视觉模型分析每一帧画面
- **多渠道告警** - 震动、通知、Toast、Webhook（支持飞书）
- **智能去重** - 告警冷却机制，避免刷屏
- **证据留存** - 自动保存告警截图
- **可调频率** - 控制推理间隔，省电省流量
- **熔断保护** - API 故障时自动熔断，防止级联失败
- **自动重连** - 摄像头断线自动恢复
- **PM2 守护** - 进程常驻，开机自启

---

## 快速开始

### 1. 准备工作

**手机端**：
1. 安装 [Termux](https://termux.com/)
2. 安装 [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam)（或其他能提供 HTTP 照片端点的 App）
3. 安装 [Termux:API](https://wiki.termux.com/wiki/Termux:API)（用于系统通知）

**服务端**（任意机器，甚至 NAS、树莓派）：
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载视觉模型（推荐 4B 参数的量化版本，平衡效果和速度）
ollama pull qwen3-vl:4b-instruct-q4_K_M
```

### 2. 安装 AI Monitor

```bash
# 在 Termux 中
pkg install python git

# 克隆项目
git clone https://github.com/your-repo/ai-monitor.git
cd ai-monitor

# 安装依赖（使用 uv，比 pip 快很多）
pip install uv
uv sync
```

### 3. 配置

```bash
cp .env.example .env
nano .env  # 或 vim .env
```

关键配置：
```bash
# 摄像头地址（IP Webcam 启动后显示的地址）
MONITOR_CAM_URL=http://192.168.1.100:8080/shot.jpg

# Ollama 服务地址
MONITOR_OLLAMA_API=http://192.168.1.200:11434/api/generate

# 推理间隔（秒），越大越省电
MONITOR_DETECTION_INTERVAL=2.0

# 告警冷却时间（秒），避免重复告警
MONITOR_ALERT_COOLDOWN=60
```

### 4. 运行

```bash
# 前台运行（调试用）
./run.sh

# 后台运行（推荐）
./pm2.sh start
./pm2.sh logs    # 查看日志
```

---

## 配置详解

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| **摄像头** |||
| `MONITOR_CAM_URL` | `http://127.0.0.1:8080/shot.jpg` | 摄像头 HTTP 照片端点 |
| `MONITOR_CAM_TIMEOUT` | `10.0` | 摄像头连接超时（秒） |
| `MONITOR_CAM_RECONNECT_ENABLED` | `true` | 启用自动重连 |
| **推理** |||
| `MONITOR_OLLAMA_API` | - | Ollama API 地址 |
| `MONITOR_MODEL_NAME` | `qwen3-vl:4b-instruct-q4_K_M` | 视觉模型名称 |
| `MONITOR_DETECTION_INTERVAL` | `2.0` | 推理间隔（秒） |
| `MONITOR_INFERENCE_TIMEOUT` | `30.0` | 推理超时（秒） |
| **告警** |||
| `MONITOR_WEBHOOK_URL` | - | Webhook 地址（支持飞书） |
| `MONITOR_ALERT_COOLDOWN` | `60` | 告警冷却时间（秒） |
| `MONITOR_ENABLE_TERMUX_ALERTS` | `true` | 启用手机震动/通知 |
| **日志** |||
| `MONITOR_LOG_LEVEL` | `INFO` | 日志级别 |
| `MONITOR_LOG_MAX_BYTES` | `10485760` | 单个日志文件最大大小 |

---

## 推荐的视觉模型

| 模型 | 参数量 | 量化 | 显存需求 | 推荐场景 |
|------|--------|------|----------|----------|
| `qwen3-vl:4b-instruct-q4_K_M` | 4B | Q4 | ~3GB | **默认推荐**，平衡效果和速度 |
| `llava:7b-v1.6-q4_K_M` | 7B | Q4 | ~5GB | 更准确，需要更多显存 |
| `minicpm-v:8b-q4_K_M` | 8B | Q4 | ~6GB | 效果最好，适合高端显卡 |

---

## 性能参考

在骁龙 888 手机 + RTX 3060 服务器环境下：

| 阶段 | 耗时 |
|------|------|
| 帧抓取 | ~10ms |
| 图像处理 | ~20ms |
| 模型推理 | ~3-5s |

**优化建议**：
- 降低 `MONITOR_TARGET_WIDTH` 减少传输数据
- 增大 `MONITOR_DETECTION_INTERVAL` 省电
- 使用更小的量化模型加快推理

---

## 故障处理

| 问题 | 现象 | 解决方案 |
|------|------|----------|
| 摄像头断开 | 持续报错 | 自动重连，指数退避（2s→60s） |
| Ollama 宕机 | 推理失败 | 熔断器保护，60s 后自动恢复 |
| 网络超时 | 请求卡住 | 自动超时，不影响其他任务 |
| 重复告警 | 刷屏 | 冷却时间内不重复触发 |

---

## 项目结构

```
ai-monitor/
├── src/
│   ├── main.py            # 入口，信号处理
│   ├── monitor.py         # 核心流水线
│   ├── alert.py           # 告警处理
│   ├── config.py          # 配置管理
│   ├── circuit_breaker.py # 熔断器
│   └── termux_alert.py    # 手机通知
├── logs/                   # 日志目录
├── alerts/                 # 告警截图
├── run.sh                  # 启动脚本
├── pm2.sh                  # PM2 管理
└── .env.example            # 配置模板
```

---

## 常见问题

<details>
<summary><b>Q: 为什么要用 Termux 而不是直接写个 Android App？</b></summary>

A: Termux 方案的优势：
1. **开发门槛低** - Python 比 Kotlin/Swift 简单
2. **部署方便** - git pull 就能更新
3. **灵活可控** - 可以随时修改提示词、调整参数
4. **兼容性好** - 不受 Android 版本限制

</details>

<details>
<summary><b>Q: 为什么要用局域网 Ollama 而不是云端 API？</b></summary>

A:
1. **免费** - 不用付 API 费用
2. **隐私** - 视频不离开你的网络
3. **稳定** - 不依赖外网，断网也能用
4. **可控** - 可以随时换模型、调参数

</details>

<details>
<summary><b>Q: 手机发热/耗电怎么办？</b></summary>

A:
1. 增大 `MONITOR_DETECTION_INTERVAL`（如 5.0）
2. 降低 `MONITOR_TARGET_WIDTH`（如 320）
3. 使用有线充电 + 省电模式
4. 考虑用树莓派/NAS 替代手机端运行

</details>

---

## 贡献

欢迎提交 Issue 和 PR！

---

## License

[MIT](LICENSE)
