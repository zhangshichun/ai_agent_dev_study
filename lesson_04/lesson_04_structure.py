import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv()

# 检查 API Key 是否存在，避免运行时才报错
api_key = os.getenv("DEEP_SEEK_API_KEY")
if not api_key:
    print("❌ 错误: 未找到 DEEP_SEEK_API_KEY 环境变量，请检查 .env 文件")
    sys.exit(1)

client = OpenAI(
    api_key=api_key, 
    base_url=os.getenv("DEEP_SEEK_API_URL")
)

# ==========================================
# 第一步：定义“模具” (增加情感反馈字段)
# ==========================================
class AccountItem(BaseModel):
    amount: float = Field(description="交易金额，必须是数字。如果未提及金额，默认为 0.0")
    category: str = Field(description="交易分类，只能从以下选择：[餐饮, 交通, 购物, 娱乐, 居家, 医疗, 学习, 其他]")
    product: str = Field(description="具体的商品或服务名称")
    sentiment: str = Field(description="消费时的情绪，例如：开心, 后悔, 心疼, 期待, 平淡 等等，可以自行总结")
    # 🔥 新增字段：AI 的情感反馈
    ai_comment: str = Field(description="根据用户的消费内容和情绪，给出一句简短的反馈。如果是乱花钱可以幽默吐槽，如果是必要消费给予肯定，如果是心情不好则给予安慰。")

# ==========================================
# 第二步：处理函数
# ==========================================
def smart_bookkeeping(user_input):
    schema_str = json.dumps(AccountItem.model_json_schema(), ensure_ascii=False)
    
    system_prompt = f"""
    你是一个不仅会记账，还很懂心理学的贴心助手。
    请分析用户的输入，提取关键信息，并给出情感反馈。
    
    【重要规则】
    1. 根据常识自动推断分类。
    2. 严格按照以下 JSON Schema 格式输出 JSON 数据，禁止包含 markdown：
    {schema_str}
    """

    print("🤖 正在思考中...", end="", flush=True) # 简单的加载动效

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"} 
        )

        json_str = response.choices[0].message.content
        data = json.loads(json_str)
        item = AccountItem(**data)
        print("\r", end="") # 清除"正在思考中"
        return item
        
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")
        return None

# ==========================================
# 第三步：交互式 CLI (命令行界面)
# ==========================================
if __name__ == "__main__":
    print("=" * 40)
    print("💰 智能记账助手 CLI 版 (输入 q 或 exit 退出)")
    print("=" * 40)

    while True:
        try:
            # 获取用户输入
            user_input = input("\n📝 请输入账单描述: ").strip()
            
            # 退出条件
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print("👋 下次再见！")
                break
            
            if not user_input:
                continue

            # 调用 AI
            result = smart_bookkeeping(user_input)
            
            # 格式化输出结果
            if result:
                print(f"\n✅ 记账成功！")
                print(f"   ---------------------------")
                print(f"   🏷️  分类: {result.category}")
                print(f"   🛒 商品: {result.product}")
                print(f"   💰 金额: {result.amount:.2f}")
                print(f"   💭 心情: {result.sentiment}")
                print(f"   🤖 AI说: \033[96m{result.ai_comment}\033[0m") # 使用青色高亮显示 AI 回复
                print(f"   ---------------------------")

        except KeyboardInterrupt:
            # 允许用户通过 Ctrl+C 优雅退出
            print("\n👋 用户强制退出")
            break