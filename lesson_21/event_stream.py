"""
LangChain 实战 Demo - Agent 底层事件流 (Event Stream) 自动捕获
适配 LangChain 1.x 版本
"""
import os
import sys
import io
import uuid
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent

# ==========================================
# 1. 定义底层事件的数据结构
# ==========================================
class Event:
    def __init__(self, actor: str, action_type: str, payload: str):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.actor = actor
        self.action_type = action_type
        self.payload = payload

# ==========================================
# 2. 核心：编写 LangChain 回调拦截器 
# ==========================================
class EventStreamRecorder(BaseCallbackHandler):
    def __init__(self):
        self.event_queue: List[Event] = []

    # 拦截：大模型开始处理消息
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any
    ) -> None:
        # 获取用户最新的输入
        if messages and messages[0]:
            latest_user_msg = messages[0][-1].content
            self._record(actor="user", action_type="USER_INPUT", payload=latest_user_msg)

    # 拦截：大模型决定调用工具
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        self._record(actor="agent", action_type="TOOL_CALL", payload=f"尝试调用 [{tool_name}]，入参: {input_str}")

    # 拦截：工具执行成功
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        self._record(actor="system", action_type="TOOL_RESULT", payload=f"执行成功，返回: {output}")

    # 拦截：工具执行失败/抛出异常
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        self._record(actor="system", action_type="SYSTEM_ERROR", payload=f"拦截到底层报错: {str(error)}")

    def _record(self, actor: str, action_type: str, payload: str):
        new_event = Event(actor=actor, action_type=action_type, payload=payload)
        self.event_queue.append(new_event)
        # 实时打印到控制台
        print(f"  [监控录像] {new_event.timestamp.strftime('%H:%M:%S')} | {actor.upper()} -> {action_type}: {payload}")

    def get_stream_text(self) -> str:
        """导出当前的事件流水账，供后续生成情景摘要使用"""
        return "\n".join([f"[{e.timestamp.strftime('%H:%M:%S')}] {e.action_type}: {e.payload}" for e in self.event_queue])


# ==========================================
# 3. 模拟业务工具 (包含正常和报错两种情况)
# ==========================================
@tool
def install_package(package_name: str) -> str:
    """用于在本地环境中安装Python依赖包"""
    # 我们故意埋一个坑：模拟安装 numpy 时发生网络超时报错
    if package_name.lower() == "numpy":
        raise TimeoutError("ReadTimeoutError: HTTPSConnectionPool(host='pypi.org', port=443): Read timed out.")
    return f"Successfully installed {package_name}"


# ==========================================
# 4. 主函数演示
# ==========================================
def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    load_dotenv()

    # 初始化 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.1
    )

    # 准备工具
    tools = [install_package]

    # 创建 Agent (LangChain 1.x 新 API)
    agent = create_agent(
        llm,
        tools,
        system_prompt="你是一个得力的开发助手。如果遇到工具报错，请把报错原因直接告诉用户。"
    )

    # 实例化
    recorder = EventStreamRecorder()

    print("=" * 60)
    print("Agent 开始运行，注意观察 [监控录像] 的底层捕获过程：\n")

    user_input = "帮我用 pip 安装一下 requests，然后再装一下 numpy。"

    # 【核心挂载点】：在调用 agent 时，把 recorder 塞进 callbacks 里
    # LangChain 1.x 使用 messages 格式
    # 注意：LangGraph 1.x 中工具抛出的异常会向上传播，需要用 try-except 捕获
    response = None
    final_output = ""
    try:
        response = agent.invoke(
            {"messages": [("user", user_input)]},
            config={"callbacks": [recorder]}
        )
        # 获取最后一条 AI 消息
        messages = response.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai":
                final_output = msg.content
                break
            elif hasattr(msg, "content") and hasattr(msg, "type"):
                final_output = msg.content
                break
            elif isinstance(msg, tuple) and msg[0] == "ai":
                final_output = msg[1]
                break
    except Exception as e:
        # 工具报错被抛出时，基于已收集的事件流生成最终回复
        final_output = f"工具执行过程中出现错误: {str(e)}"

    print("\n" + "=" * 60)
    print("Agent 最终回复给用户的文本：")
    print(final_output)

    print("\n" + "=" * 60)
    print("任务结束，导出本次收集到的完整【事件流原始日志】：")
    print(recorder.get_stream_text())


if __name__ == "__main__":
    main()
