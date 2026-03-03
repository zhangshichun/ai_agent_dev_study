import os
import random
import json
import operator
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==========================================
# 1. 定义全局共享状态 (黑板)
# ==========================================
class AgentState(TypedDict):
    input_text: str
    # 使用 Annotated 和 operator.add，这意味着每次返回 messages 时，是“追加”而不是“覆盖”
    messages: Annotated[list[BaseMessage], operator.add]
    result: dict
    status: str  # 专门留给 Edge 读取的标杆："success" 或 "error"

# ==========================================
# 2. 定义 Nodes (打工人：只负责干活并更新黑板)
# ==========================================

def node_a_input(state: AgentState):
    """节点A：负责接收初始输入"""
    text = "张三18岁。"
    print(f"\n▶ [Node A] 初始化输入: {text}")
    
    # 将初始数据写到状态黑板上
    return {"input_text": text}

def node_b_llm(state: AgentState):
    """节点B：调用 LLM，并模拟 50% 的报错概率"""
    print("\n▶ [Node B] 开始处理数据...")
    
    # 1. 模拟 50% 概率的报错
    if random.random() < 0.5:
        print("  [!] 糟糕！触发了 50% 的模拟错误。")
        error_result = {"message": "出错了"}
        error_msg = AIMessage(content=json.dumps(error_result))
        
        # 更新状态：把错误消息追加到 messages，并把 status 设为 error
        return {
            "messages": [error_msg], 
            "result": error_result,
            "status": "error" 
        }
    
    # 2. 正常调用大模型 (剩下 50% 的概率)
    print("  [*] 运气不错，正在请求大模型提取 JSON...")
    llm = ChatOpenAI(
      model="deepseek-chat",
      api_key=os.getenv("DEEP_SEEK_API_KEY"),
      base_url=os.getenv("DEEP_SEEK_API_URL"),
      temperature=0.7
    )
    
    # 强制让大模型输出 JSON 格式
    llm_with_json = llm.bind(response_format={"type": "json_object"})
    
    prompt = f"请提取以下文本中的信息，并返回JSON格式，必须包含 name 和 age 字段。\n文本：{state['input_text']}"
    message = HumanMessage(content=prompt)
    
    response = llm_with_json.invoke([message])
    parsed_json = json.loads(response.content)
    
    # 更新状态：将成功的 JSON 写回黑板，状态标为 success
    return {
        "messages": [response],
        "result": parsed_json,
        "status": "success"
    }

def node_c_print(state: AgentState):
    """节点C：纯粹负责打印最终正确结果"""
    print("\n▶ [Node C] 接收到最终结果，准备打印：")
    print(json.dumps(state["result"], ensure_ascii=False, indent=2))
    return {} # 不需要更新状态了

# ==========================================
# 3. 定义 Edge (主管/裁判：只负责看黑板，决定下一步去哪)
# ==========================================

def router_edge(state: AgentState):
    """条件边：读取 status 字段决定去向"""
    if state["status"] == "error":
        print("  ↳ [Edge 路由] 发现错误状态，打回 Node B 重试！")
        return "retry"
    else:
        print("  ↳ [Edge 路由] 状态成功，放行到 Node C。")
        return "continue"

# ==========================================
# 4. 组装图 (构建状态机)
# ==========================================

workflow = StateGraph(AgentState)

# 添加所有节点
workflow.add_node("node_a", node_a_input)
workflow.add_node("node_b", node_b_llm)
workflow.add_node("node_c", node_c_print)

# 定义流转规则
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")

# 添加条件边：离开 node_b 时，用 router_edge 进行判断
workflow.add_conditional_edges(
    "node_b",
    router_edge,
    {
        "retry": "node_b",     # 如果 router_edge 返回 "retry"，跳回 node_b
        "continue": "node_c"   # 如果 router_edge 返回 "continue"，跳到 node_c
    }
)

workflow.add_edge("node_c", END)

# 编译成可执行的图
app = workflow.compile()

# ==========================================
# 5. 运行图
# ==========================================
if __name__ == "__main__":
    print("================ 开始运行 Agent ================")
    # 传入一个空字典作为初始状态启动图
    final_state = app.invoke({})
    print("\n================ 运行结束 ================")
    print(f"总计产生了 {len(final_state['messages'])} 条 LLM 消息（包含报错与重试）")