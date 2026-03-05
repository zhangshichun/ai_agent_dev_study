from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 1. 定义状态 (黑板)
class AgentState(TypedDict):
    transfer_amount: int
    recipient: str
    status: str

# 2. 定义节点 (打工人)
def prepare_transfer_node(state: AgentState):
    print("▶ [Node 1: 准备] 正在核对转账信息...")
    # 模拟经过一番复杂计算，确认了要转给谁、转多少钱
    return {"transfer_amount": 1000, "recipient": "张三", "status": "pending_approval"}

def execute_transfer_node(state: AgentState):
    print(f"▶ [Node 2: 执行] 正在向 {state['recipient']} 的账户打款 {state['transfer_amount']} 元！")
    return {"status": "completed"}

# 3. 构建图
workflow = StateGraph(AgentState)
workflow.add_node("prepare", prepare_transfer_node)
workflow.add_node("execute", execute_transfer_node)

workflow.add_edge(START, "prepare")
workflow.add_edge("prepare", "execute")
workflow.add_edge("execute", END)

# ==========================================
# 4. 引入 Checkpointer (必须有存档，才能暂停！)
# ==========================================
memory = MemorySaver()

# 重点 1：在编译时，指定在执行 "execute" 节点之前暂停！
app = workflow.compile(
    checkpointer=memory, 
    interrupt_before=["execute"]  # 遇到 execute 节点，立刻阻断
)

# ==========================================
# 5. 运行图与人类审批
# ==========================================
if __name__ == "__main__":
    # 指定存档的 Thread ID
    config = {"configurable": {"thread_id": "transfer_task_001"}}

    print("\n--- 第一阶段：Agent 开始准备 ---")
    # 传入初始状态启动
    app.invoke({"transfer_amount": 0, "recipient": ""}, config=config)
    
    # 此时图会自动暂停！
    print("\n[系统提示] 图的执行已挂起。")
    
    # 我们可以随时查看当前“黑板”上的状态
    current_state = app.get_state(config)
    print(">>> 拦截到的当前状态:", current_state.values)
    print(">>> 下一步准备执行的 Node:", current_state.next) # 会显示 ('execute',)

    # 模拟人类审批过程
    print("\n--- 第二阶段：人类介入审查 ---")
    human_input = input(f"警告：AI 准备向 {current_state.values['recipient']} 转账 {current_state.values['transfer_amount']} 元。是否同意？(y/n): ")
    
    if human_input.lower() == 'y':
        print("\n--- 第三阶段：人类同意，恢复执行 ---")
        # 重点 2：传入 None 继续执行当前 thread 的后续流程
        app.invoke(None, config=config)
        print("\n[系统提示] 任务全部完成！")
    else:
        print("\n--- 人类拒绝，操作取消！---")
        # 实际开发中，这里你可以改变状态或结束流程