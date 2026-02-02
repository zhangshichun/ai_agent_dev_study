import os
import json
from dotenv import load_dotenv
from openai import OpenAI
# 引入 Pydantic 的核心组件
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEP_SEEK_API_KEY"), 
    base_url=os.getenv("DEEP_SEEK_API_URL")
)

# ==========================================
# 第一步：定义“模具” (Pydantic Model)
# ==========================================
class AccountItem(BaseModel):
    amount: float = Field(description="交易金额，必须是数字。如果未提及金额，默认为 0.0")
    # 在 description 中限制分类，AI 会非常听话地做选择题
    category: str = Field(description="交易分类，只能从以下选择：[餐饮, 交通, 购物, 娱乐, 居家, 医疗, 其他]")
    product: str = Field(description="具体的商品或服务名称，例如'牛肉面'、'滴滴打车'")
    sentiment: str = Field(description="消费时的情绪，例如：happy, sad, neutral, painful(心疼)")

# ==========================================
# 第二步：编写处理函数
# ==========================================
def smart_bookkeeping(user_input):
    # 1. 把 Pydantic 类转换成 AI 能读懂的 JSON Schema 描述
    # ensure_ascii=False 是为了让中文正常显示，不变成 \uXXXX
    schema_str = json.dumps(AccountItem.model_json_schema(), ensure_ascii=False)
    
    # 2. 构建 System Prompt (立规矩)
    system_prompt = f"""
    你是一个专业的记账助手。
    请分析用户的输入，提取关键信息。
    
    【重要规则】
    1. 根据常识自动推断分类（如：'咖啡' -> '餐饮'）。
    2. 严格按照以下 JSON Schema 格式输出 JSON 数据，禁止包含任何 markdown 标记或解释性文字：
    {schema_str}
    """

    print(f"🔄 正在分析账单: {user_input} ...")

    try:
        # 3. 调用大模型
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": system_prompt}, # 注入规则
                {"role": "user", "content": user_input}       # 注入数据
            ],
            # 【关键】强制模型进入 JSON 模式，防止它胡乱说话
            response_format={"type": "json_object"} 
        )

        # 4. 获取结果字符串
        json_str = response.choices[0].message.content
        
        # 5. 【验证】将 JSON 字符串倒回 Pydantic 模具
        # 如果格式不对，这一步会报错，保证了数据的安全性
        data = json.loads(json_str)
        item = AccountItem(**data)
        
        return item
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None

# ==========================================
# 第三步：测试运行
# ==========================================
if __name__ == "__main__":
    # 测试案例 1
    text1 = "刚才打车回家花了 35.5，心疼死了"
    result1 = smart_bookkeeping(text1)
    if result1:
        # 此时 result1 已经是一个标准的 Python 对象，可以点出属性
        print(f"✅ 记账成功：")
        print(f"   - 商品: {result1.product}")
        print(f"   - 金额: {result1.amount}")
        print(f"   - 分类: {result1.category}") # AI 会自动推断这是交通
        print(f"   - 心情: {result1.sentiment}")
    
    print("-" * 30)
    
    # 测试案例 2
    text2 = "周末和朋友去吃了顿海底捞，花了420"
    result2 = smart_bookkeeping(text2)
    if result2:
        print(f"✅ 记账成功：[{result2.category}] {result2.product} ￥{result2.amount}")