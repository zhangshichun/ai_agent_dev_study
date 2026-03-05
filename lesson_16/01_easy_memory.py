import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, MessagesState, END
# from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============== 1. 设置 LLM（可换成任意 ChatModel） ==============
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEP_SEEK_API_KEY"),
    base_url=os.getenv("DEEP_SEEK_API_URL"),
    temperature=0.7
)

# ============== 2. 定义系统提示（每次调用都 prepend，保证一致性） ==============
SYSTEM_PROMPT = SystemMessage(
    content="你是一个沉稳的 AI 助手，名叫 【春哥】。用户叫你什么你就记住什么，并用这个名字称呼他。"
)

# ============== 3. 定义聊天节点（核心逻辑） ==============
def chatbot(state: MessagesState):
    # 把系统提示 + 历史消息一起发给 LLM
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm.invoke(messages)
    # 返回的消息会自动通过 add_messages reducer 追加到 state
    return {"messages": [response]}

# ============== 4. 构建图 + 编译（带 Checkpointer） ==============
graph_builder = StateGraph(MessagesState)

# 添加节点和边（最简聊天流）
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)   # 每次调用只回复一次，适合交互循环

# 关键：注入 Checkpointer（这就是「记忆」来源）
# checkpointer = InMemorySaver()
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    
    graph = graph_builder.compile(checkpointer=checkpointer)

    # ============== 5. 交互循环演示（同一 thread_id 保持记忆） ==============
    print("【春哥聊天机器人】已启动（输入 'quit' 或 'exit' 退出）\n")

    thread_id = "demo-thread-001"   # ← 改成不同 ID 就是新会话
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("你: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 再见！")
            break
        
        # 构造输入（只传新的人类消息即可，历史自动从 checkpointer 加载）
        input_message = {"messages": [HumanMessage(content=user_input)]}
        
        # 调用图（支持 stream / astream / invoke）
        for chunk in graph.stream(input_message, config, stream_mode="values"):
            last_message = chunk["messages"][-1]
            if isinstance(last_message, AIMessage) and last_message.content.strip():
                print(f"【春哥】: {last_message.content}\n")