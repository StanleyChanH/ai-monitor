<div align="center">

<img src="icon.png" alt="AI Monitor Logo" width="128" height="128">

# AI Monitor

**把旧手机变成智能安防监控终端**

基于视觉大模型的实时监控系统，运行在 Termux 环境中，
让你的 Android 手机具备 AI 识别能力。

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Termux](https://img.shields.io/badge/Platform-Termux-green.svg)](https://termux.com/)
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25_Local-brightgreen.svg)]()

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
| 隐私保护 | ⚠️ 云存储 | ⚠️ 云处理 | **✅ 100% 本地** |
| 网络依赖 | 需联网 | 需联网 | **❌ 完全离线可用** |
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

### 方案一：完全本地（推荐，隐私最佳）

一台手机搞定所有，**无需网络、无需服务器、100% 隐私**：

```
┌─────────────────────────────────────────────────────────────┐
│                     你的手机 (Android)                       │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │  IP Webcam  │──▶│  AI Monitor │──▶│  MNN Chat   │       │
│  │   (摄像头)   │   │  (Termux)   │   │  (本地推理)  │       │
│  └─────────────┘   └──────┬──────┘   └─────────────┘       │
│                           │                                 │
│                           ▼                                 │
│                    ┌─────────────┐                          │
│                    │   告警系统   │                          │
│                    │ (震动/通知)  │                          │
│                    └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘

✅ 完全离线运行  ✅ 零网络延迟  ✅ 数据不出手机
```

### 方案二：局域网推理

手机负责采集，局域网服务器负责推理：

```
┌─────────────────────────────┐      ┌─────────────────────┐
│      你的手机 (Termux)       │      │   局域网服务器       │
│  ┌─────────┐  ┌──────────┐  │      │  ┌───────────────┐  │
│  │IP Webcam│─▶│AI Monitor│──│──▶WiFi──▶│    Ollama     │  │
│  └─────────┘  └──────────┘  │      │  │  vLLM/LocalAI │  │
│               ┌──────────┐  │      │  └───────────────┘  │
│               │  告警系统 │◀─│──◀WiFi───────────────────┘
│               └──────────┘  │      │                     │
└─────────────────────────────┘      └─────────────────────┘

✅ 无需公网  ✅ 本地处理  ✅ 多手机共享算力
```

### 方案三：云端推理

无本地算力时的备选方案：

```
手机 (Termux) ──互联网──▶ 智谱 GLM-4V / OpenAI
```

**设计优势**：
- **完全本地可选**：MNN Chat 让一台手机即可完成所有处理，隐私最大化
- **非阻塞流水线**：推理 3-5 秒不影响帧抓取，不漏掉任何画面
- **完整容错机制**：熔断器 + 自动重连 + 优雅降级
- **多种推理后端**：MNN Chat、Ollama、智谱 GLM-4V、vLLM/LocalAI

---

## 功能特性

- **🔒 100% 本地可选** - 支持 MNN Chat 纯本地推理，数据不出手机
- **🤖 实时 AI 分析** - 使用视觉模型分析每一帧画面
- **多种推理后端** - MNN Chat（手机本地）、Ollama（局域网）、智谱 GLM-4V（云端）、vLLM/LocalAI
- **自定义提示词** - 可根据场景定制监控逻辑（宠物监护、老人看护等）
- **动作触发检测** - 利用 IP Webcam 传感器，仅在检测到动作时触发推理，省电省流量
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

**手机端（必须）**：
1. 安装 [Termux](https://termux.com/)
2. 安装 [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam)（或其他能提供 HTTP 照片端点的 App）
3. 安装 [Termux:API](https://wiki.termux.com/wiki/Termux:API)（用于系统通知）

**推理后端（四选一）**：

<details>
<summary><b>⭐ 方案 A: MNN Chat（手机本地，强烈推荐）</b></summary>

**完全本地运行，无需网络，隐私最佳！**

1. 安装 [MNN Chat](https://github.com/alibaba/MNN)（阿里巴巴开源，支持 Android）
2. 在 MNN Chat 中下载视觉模型（如 Qwen2-VL、LLaVA）
3. 开启 OpenAI 兼容 API 服务（默认端口通常是 11434 或自定义）

**优势**：
- ✅ 完全离线运行，不需要任何网络
- ✅ 数据不出手机，隐私最大化
- ✅ 零延迟，响应速度快
- ✅ 一台手机搞定所有

**配置**：
```bash
MONITOR_INFERENCE_PROVIDER=openai
MONITOR_OPENAI_API_URL=http://127.0.0.1:11434/v1/chat/completions
MONITOR_OPENAI_MODEL=your-model-name
```

</details>

<details>
<summary><b>方案 B: Ollama（局域网服务器）</b></summary>

需要一台有 GPU 的机器（PC、NAS、树莓派）：
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载视觉模型（推荐 4B 参数的量化版本，平衡效果和速度）
ollama pull qwen3-vl:4b-instruct-q4_K_M
```

</details>

<details>
<summary><b>方案 C: vLLM / LocalAI（局域网服务器）</b></summary>

支持任何 OpenAI 兼容的视觉模型服务：

```bash
# vLLM 示例
vllm serve Qwen/Qwen2-VL-7B-Instruct --port 8000
```

**配置**：
```bash
MONITOR_INFERENCE_PROVIDER=openai
MONITOR_OPENAI_API_URL=http://192.168.1.100:8000/v1/chat/completions
MONITOR_OPENAI_MODEL=Qwen/Qwen2-VL-7B-Instruct
```

</details>

<details>
<summary><b>方案 D: 智谱 GLM-4V-Flash（云端）</b></summary>

无本地算力时的备选方案：
1. 注册 [智谱开放平台](https://open.bigmodel.cn/)
2. 获取 API Key
3. 使用云端免费额度

</details>

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

# 推理后端选择：openai、ollama 或 zhipu
# 推荐 openai，可配合 MNN Chat 实现完全本地运行
MONITOR_INFERENCE_PROVIDER=openai

# ========================================
# 方案 A: MNN Chat（手机本地，推荐）
# ========================================
# 在 MNN Chat 中开启 OpenAI 兼容 API 服务
MONITOR_OPENAI_API_URL=http://127.0.0.1:11434/v1/chat/completions
MONITOR_OPENAI_MODEL=Qwen2-VL-7B-Instruct
# 无需 API Key（本地服务）

# ========================================
# 方案 B: Ollama（局域网服务器）
# ========================================
# MONITOR_INFERENCE_PROVIDER=ollama
# MONITOR_OLLAMA_API=http://192.168.1.200:11434/api/generate
# MONITOR_MODEL_NAME=qwen3-vl:4b-instruct-q4_K_M

# ========================================
# 方案 C: vLLM/LocalAI（局域网服务器）
# ========================================
# MONITOR_INFERENCE_PROVIDER=openai
# MONITOR_OPENAI_API_URL=http://192.168.1.100:8000/v1/chat/completions
# MONITOR_OPENAI_MODEL=Qwen/Qwen2-VL-7B-Instruct

# ========================================
# 方案 D: 智谱云端（无本地算力时）
# ========================================
# MONITOR_INFERENCE_PROVIDER=zhipu
# MONITOR_ZHIPU_API_KEY=your_api_key_here
# MONITOR_ZHIPU_MODEL=glm-4v-flash

# ========================================
# 通用配置
# ========================================
# 自定义提示词（可选，默认为安防监控）
# MONITOR_INFERENCE_PROMPT=你是一名宠物监控专家...

# 动作检测（可选，省电省流量）
# MONITOR_MOTION_DETECTION_ENABLED=true
# MONITOR_MOTION_CHECK_INTERVAL=0.5

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
| **动作检测** |||
| `MONITOR_MOTION_DETECTION_ENABLED` | `false` | 启用动作触发检测 |
| `MONITOR_MOTION_CHECK_INTERVAL` | `0.5` | 动作传感器检查间隔（秒） |
| **推理** |||
| `MONITOR_INFERENCE_PROVIDER` | `ollama` | 推理后端：`ollama`、`zhipu` 或 `openai` |
| `MONITOR_INFERENCE_TIMEOUT` | `30.0` | 推理超时（秒） |
| `MONITOR_DETECTION_INTERVAL` | `2.0` | 推理间隔（秒） |
| `MONITOR_INFERENCE_PROMPT` | *(内置默认)* | 自定义提示词（所有提供商共用） |
| **Ollama（provider=ollama）** |||
| `MONITOR_OLLAMA_API` | - | Ollama API 地址 |
| `MONITOR_MODEL_NAME` | `qwen3-vl:4b-instruct-q4_K_M` | 视觉模型名称 |
| **智谱（provider=zhipu）** |||
| `MONITOR_ZHIPU_API_KEY` | - | 智谱 API Key（必填） |
| `MONITOR_ZHIPU_API_URL` | 智谱 API 地址 | 一般无需修改 |
| `MONITOR_ZHIPU_MODEL` | `glm-4v-flash` | 视觉模型名称 |
| **OpenAI 兼容（provider=openai）** |||
| `MONITOR_OPENAI_API_KEY` | - | API Key（本地部署可留空） |
| `MONITOR_OPENAI_API_URL` | `http://localhost:8000/v1/chat/completions` | OpenAI 兼容 API 地址 |
| `MONITOR_OPENAI_MODEL` | - | 视觉模型名称（必填） |
| **告警** |||
| `MONITOR_WEBHOOK_URL` | - | Webhook 地址（支持飞书） |
| `MONITOR_ALERT_COOLDOWN` | `60` | 告警冷却时间（秒） |
| `MONITOR_ENABLE_TERMUX_ALERTS` | `true` | 启用手机震动/通知 |
| **日志** |||
| `MONITOR_LOG_LEVEL` | `INFO` | 日志级别 |
| `MONITOR_LOG_MAX_BYTES` | `10485760` | 单个日志文件最大大小 |

---

## 推荐的视觉模型

### 手机本地运行（MNN Chat）

| 模型 | 参数量 | 手机内存需求 | 推荐场景 |
|------|--------|-------------|----------|
| Qwen2-VL-2B | 2B | ~4GB | **手机首选**，速度快 |
| Qwen2-VL-7B | 7B | ~8GB | 效果更好，需高端手机 |
| LLaVA-v1.6 | 7B | ~8GB | 通用视觉模型 |

### 局域网服务器（Ollama/vLLM）

| 模型 | 参数量 | 量化 | 显存需求 | 推荐场景 |
|------|--------|------|----------|----------|
| `qwen3-vl:4b-instruct-q4_K_M` | 4B | Q4 | ~3GB | **默认推荐**，平衡效果和速度 |
| `llava:7b-v1.6-q4_K_M` | 7B | Q4 | ~5GB | 更准确，需要更多显存 |
| `minicpm-v:8b-q4_K_M` | 8B | Q4 | ~6GB | 效果最好，适合高端显卡 |

---

## 性能参考

### 完全本地（MNN Chat + Termux 同一手机）

在骁龙 8 Gen 2 手机环境下：

| 阶段 | 耗时 |
|------|------|
| 帧抓取 | ~10ms |
| 图像处理 | ~20ms |
| 模型推理（2B） | ~2-4s |
| 模型推理（7B） | ~5-10s |

### 局域网推理（手机 + 服务器）

在骁龙 888 手机 + RTX 3060 服务器环境下：

| 阶段 | 耗时 |
|------|------|
| 帧抓取 | ~10ms |
| 图像处理 | ~20ms |
| 模型推理 | ~3-5s |

**优化建议**：
- 完全本地：使用 2B 模型，开启动作检测
- 局域网：降低 `MONITOR_TARGET_WIDTH` 减少传输数据
- 通用：增大 `MONITOR_DETECTION_INTERVAL` 省电

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
<summary><b>Q: 推理后端怎么选？</b></summary>

A:
| 对比项 | MNN Chat ⭐ | Ollama | 智谱 GLM-4V | vLLM |
|--------|------------|--------|-------------|------|
| 运行位置 | **手机本地** | 局域网服务器 | 云端 | 局域网服务器 |
| 硬件需求 | **无（手机即可）** | 需要 GPU | 无需 | 需要 GPU |
| 网络依赖 | **完全离线** | 局域网 | 需要互联网 | 局域网 |
| 隐私保护 | **最高** | 高 | 低 | 高 |
| 费用 | **免费** | 免费 | 免费额度 | 免费 |
| 推荐场景 | **隐私优先/无服务器** | 有闲置 GPU | 无 GPU、快速体验 | 高性能部署 |

**推荐**：如果追求隐私和便携性，首选 **MNN Chat**，一台手机搞定所有！

</details>

<details>
<summary><b>Q: MNN Chat 如何配置？</b></summary>

A: MNN Chat 是阿里巴巴开源的移动端推理引擎，支持在手机上运行视觉模型：

1. **安装 MNN Chat**：从 [GitHub Releases](https://github.com/alibaba/MNN/releases) 下载 Android 版本
2. **下载模型**：在 App 内下载视觉模型（如 Qwen2-VL-2B）
3. **开启 API 服务**：在设置中开启 OpenAI 兼容 API，记下端口号
4. **配置 AI Monitor**：
   ```bash
   MONITOR_INFERENCE_PROVIDER=openai
   MONITOR_OPENAI_API_URL=http://127.0.0.1:端口号/v1/chat/completions
   MONITOR_OPENAI_MODEL=模型名称
   ```

</details>

<details>
<summary><b>Q: 如何自定义监控场景（如宠物监护）？</b></summary>

A: 通过 `MONITOR_INFERENCE_PROMPT` 环境变量自定义提示词：

```bash
# 宠物监护场景
MONITOR_INFERENCE_PROMPT=你是一名宠物监控专家。请观察图片，识别宠物是否在捣乱（翻垃圾桶、挠沙发、咬电线）。回答 ALERT 或 SAFE，并简述理由。

# 老人看护场景
MONITOR_INFERENCE_PROMPT=你是一名老人看护专家。请观察图片，识别老人是否有跌倒、长时间不动、或需要帮助的情况。回答 ALERT 或 SAFE，并简述理由。
```

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
