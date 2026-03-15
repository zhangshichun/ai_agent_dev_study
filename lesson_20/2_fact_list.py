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
# [重要提示]：仅根据用户的信息生成事实内容，切勿包含助手或系统消息中的信息。
需要记住的信息类型：1.个人偏好 2.重要个人信息 3. 行程规划 4. 职业信息 5.其他与用户相关的信息
几个示例：
用户：嗨。
输出：{{"facts":[]}}
用户：嗨，我想在武汉找一家餐厅。
输出：{{"facts":["正在寻找旧金山的餐厅"]}}
用户：昨天下午 3 点，我与尤雨溪进行了会面。我们讨论了新项目。
输出：{{"facts":["在昨天下午 3 点与尤雨溪会面，并讨论了新项目"]}}

- 仅提取用户消息内容，忽略助手/系统消息
- 若无相关事实，则返回空列表
- 请以JSON格式输出结果
"""
USER_PROMPT_TEMPLATE = """以下为对话内容：
{conversation}
"""

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
        extra_body={"response_format": {"type": "json_object"}}
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
