"""
LangChain 信息提取 Demo - 从对话"言外之意"提取用户隐性特征
"""
import json
import os
import sys
import io
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# ==================== 构建Prompt（不依赖运行时初始化） ====================
SYSTEM_PROMPT = """你是一个专业的信息提取专家，擅长从多轮对话的"言外之意"中，精准捕捉目标人物的隐性特征。
"""
USER_PROMPT_TEMPLATE = """以下为对话内容：
{conversation}
"""
# ============================================

# 请严格按照JSON格式输出，字段如下：
# - dietary_restrictions: 饮食限制列表
# - flavor_preference: 口味偏好
# - personality_traits: 性格特征列表
# - dining_context: 用餐场景
# - emotional_state: 情绪状态
# - other_insights: 其他洞察列表"""

# 请提取关于User的隐性特征，输出JSON：

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", USER_PROMPT_TEMPLATE)
])


# ==================== 主函数 ====================
def main():
    # 解决 Windows 控制台编码问题
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 加载环境变量
    load_dotenv()

    # 配置
    deepseek_api_key = os.getenv("DEEP_SEEK_API_KEY")
    deepseek_base_url = os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1")

    if not deepseek_api_key:
        print("错误: 未设置 DEEP_SEEK_API_KEY 环境变量")
        return

    # 初始化 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=deepseek_api_key,
        base_url=deepseek_base_url,
        temperature=0.1,
        # extra_body={"response_format": {"type": "json_object"}}
    )

    # 构建chain
    chain = prompt | llm

    # 对话内容
    conversation = """- User：晚上想吃点好吃的，推荐下
- Assistant: 好的主人！我查到楼下的四川火锅在做活动，您可以去试试。
- User: 你认真的吗？它家没有清汤锅，那我岂不是就只能吃点酥肉了.."""

    print("=" * 50)
    print("对话内容：")
    print(conversation)
    print("=" * 50)
    result = chain.invoke({"conversation": conversation})
    print("\n【提取结果】")
    print("-" * 40)
    print(result.content)



if __name__ == "__main__":
    main()
