import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. 加载环境变量
load_dotenv()

# 2. 从环境读取配置
api_key = os.getenv("DEEP_SEEK_API_KEY")
base_url = os.getenv("DEEP_SEEK_API_URL")

print("正在检查环境配置...")

if not api_key:
    print("❌ 错误：未找到 API KEY，请检查 .env 文件")
else:
    # 为了安全，只打印前几位和后几位
    print(f"✅ API Key 读取成功: {api_key[:6]}******{api_key[-4:]}")

# 3. 尝试发起一次真实的对话请求
try:
    # DeepSeek 兼容 OpenAI SDK，只需替换 base_url
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    response = client.chat.completions.create(
        model="deepseek-chat",  # DeepSeek 的模型名称
        messages=[
            {"role": "system", "content": "你是一个有用的AI助手"},
            {"role": "user", "content": "今日几月几日？"},
        ]
    )
    print("\n🎉 连接成功！大模型回复：")
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"\n❌ 连接失败: {e}")