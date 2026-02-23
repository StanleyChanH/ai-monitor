import asyncio
import httpx
import base64
import time
import io
from PIL import Image

# --- 配置区 ---
CAM_URL = "http://127.0.0.1:8080/shot.jpg"
OLLAMA_API = "http://10.167.1.223:11434/api/generate"
MODEL_NAME = "qwen3-vl:4b-instruct-q4_K_M"

# 图像优化配置
TARGET_WIDTH = 640  # 缩放后的宽度
DETECTION_INTERVAL = 2.0  # 检测间隔（秒）

async def process_and_encode_image(raw_bytes):
    """异步处理图像：等比缩放并转为 Base64"""
    loop = asyncio.get_event_loop()
    
    def transform():
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # 计算缩放比例
            w, h = img.size
            scale = TARGET_WIDTH / float(w)
            target_height = int(float(h) * scale)
            
            # 等比缩放 (LANCZOS 保证图像质量)
            img = img.resize((TARGET_WIDTH, target_height), Image.LANCZOS)
            
            # 转为 JPEG 字节流以压缩带宽
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode('utf-8')

    return await loop.run_in_executor(None, transform)

async def fetch_vision_analysis(client, img_b64):
    """发送异步 POST 请求到远程 Ollama"""
    prompt = "图中是否有异常人员或危险动作？请回答 'ALERT' 或 'SAFE' 并简述理由。"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }

    try:
        response = await client.post(OLLAMA_API, json=payload, timeout=30.0)
        if response.status_code == 200:
            return response.json().get('response', '')
    except Exception as e:
        return f"Request Error: {e}"
    return "No Response"

async def monitor_loop():
    print(f"🚀 启动异步监控 | 模型: {MODEL_NAME}")
    
    # 使用限制连接池大小的异步客户端
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits) as client:
        while True:
            start_tick = time.time()
            
            try:
                # 1. 抓取原始图像
                resp = await client.get(CAM_URL)
                if resp.status_code != 200:
                    print("⚠️ 无法获取摄像头画面，重试中...")
                    await asyncio.sleep(1)
                    continue

                # 2. 图像优化（缩放与编码）
                img_b64 = await process_and_encode_image(resp.content)
                
                # 3. 异步提交推理任务 (不阻塞下一帧的抓取准备)
                # 在这里我们可以直接 await，或者使用 asyncio.create_task 实现更高级的并发
                analysis = await fetch_vision_analysis(client, img_b64)
                
                # 4. 逻辑响应
                elapsed = time.time() - start_tick
                print(f"[{time.strftime('%H:%M:%S')}] 耗时: {elapsed:.2f}s | 结果: {analysis.strip()}")
                
                if "ALERT" in analysis.upper():
                    print("🚨 检测到异常状态！")
                    # 此处可扩展串口下发指令

            except Exception as e:
                print(f"🛑 循环异常: {e}")

            # 动态调整休眠时间，确保检测频率稳定
            sleep_time = max(0.1, DETECTION_INTERVAL - (time.time() - start_tick))
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
