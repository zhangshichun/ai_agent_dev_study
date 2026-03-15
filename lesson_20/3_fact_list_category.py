"""
LangChain + LangGraph 信息提取 Demo - 分类事实提取与短期目标路由
"""
import json
import os
import sys
import io
import operator
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

# 引入 LangGraph 核心组件
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


SYSTEM_PROMPT = """你是一个专业的信息提取专家，擅长从多轮对话的"言外之意"中，精准捕捉目标人物的隐性特征。
# [重要提示]：仅根据用户的信息生成事实内容，切勿包含助手或系统消息中的信息。

我们需要你将提取的事实进行分类（category），可选的分类标签如下：
1. preference (个人偏好、喜好习惯)
2. short_term_goal (短期目标、当前具体的任务或项目)
3. tech_stack (技术与工具栈、技能)
4. fact (客观背景事实)

请必须以严格的 JSON 格式输出，包含一个 `facts` 数组，每个元素包含 `content` (事实内容) 和 `category` (分类标签)。

示例：
用户：我想做一个后台管理系统，用Java。
输出：{{"facts": [{{"content": "想要开发后台管理系统", "category": "short_term_goal"}}, {{"content": "希望使用Java开发", "category": "tech_stack"}}]}}

- 仅提取用户消息内容，忽略助手/系统消息
- 若无相关事实，则返回 {{"facts": []}}
"""

USER_PROMPT_TEMPLATE = """以下为对话内容：
{conversation}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", USER_PROMPT_TEMPLATE)
])


# ==================== 2. 定义 LangGraph 状态 (State) ====================
class AgentState(TypedDict):
    # 对话消息队列，短期目标会作为 Message 推入这里留存，但不入库
    messages: Annotated[list[BaseMessage], add_messages]
    # 长期记忆事实队列（如偏好、技术栈），模拟后续存入 ChromaDB 或 关系型数据库
    long_term_facts: Annotated[list[dict], operator.add]


# ==================== 主函数 ====================
def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    load_dotenv()
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
        # 强制开启 JSON 输出模式
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    # 提取链
    chain = prompt | llm

    # ==================== 3. 定义图谱处理节点 (Node) ====================
    def process_memory(state: AgentState):
        """核心路由逻辑：调用模型，并将提取的结果分别送往 短期消息队列 或 长期记忆清单"""
        
        # 1. 取出当前对话内容喂给模型
        conversation_text = state["messages"][-1].content
        result = chain.invoke({"conversation": conversation_text})
        
        try:
            parsed_data = json.loads(result.content)
            facts = parsed_data.get("facts", [])
        except json.JSONDecodeError:
            facts = []

        new_messages = []
        new_long_term = []

        # 2. 遍历事实，进行分流路由
        for fact in facts:
            if fact.get("category") == "short_term_goal":
                # 【核心】：短期目标转化为 SystemMessage，推入 State 的 messages 队列
                # 这样它会留存在当前 Session 的上下文中，直到会话结束释放
                new_messages.append(SystemMessage(content=f"[当前短期目标上下文]: {fact['content']}"))
            else:
                # 其他特征（偏好、技术栈等）推入 long_term_facts 数组
                new_long_term.append(fact)

        return {"messages": new_messages, "long_term_facts": new_long_term}

    # ==================== 构建并运行图谱 ====================
    workflow = StateGraph(AgentState)
    workflow.add_node("memory_extractor", process_memory)
    workflow.add_edge(START, "memory_extractor")
    workflow.add_edge("memory_extractor", END)
    app = workflow.compile()

    # 模拟用户输入
    conversation = """- User：梦姬，我想做一个后台管理系统
- Assistant: 好的主人！您是否有偏好的技术栈？
- User: 我擅长Nodejs和Vue，但这个项目我想使用Java和React"""

    print("=" * 50)
    print("触发对话：\n", conversation)
    print("=" * 50)

    # 初始化状态，把对话作为第一条人类消息放入队列
    initial_state = {
        "messages": [HumanMessage(content=conversation)],
        "long_term_facts": []
    }

    # 运行图谱
    final_state = app.invoke(initial_state)

    print("\n【状态机(State)流转完毕，最终结果展示】")
    print("-" * 40)
    
    print("\n1. 消息队列 (Messages) - 包含用户的原始对话 + 留存在此的短期目标：")
    for msg in final_state["messages"]:
        if isinstance(msg, HumanMessage):
            print(f"  🧑 原始输入 -> {msg.content}")
        elif isinstance(msg, SystemMessage):
            print(f"  ⚙️  系统自动追加上下文 -> {msg.content}")

    print("\n2. 长期记忆 (Long Term Facts) - 准备打入数据库的分类清单：")
    print(json.dumps(final_state["long_term_facts"], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()