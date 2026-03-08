# -*- coding: utf-8 -*-
"""
LangGraph Agent - 基于 langchain + langgraph 实现 skills 渐进式披露
使用 DeepSeek 模型
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from skill_loader import skill_loader
from skill_tools import tools
from prompt_builder import build_system_prompt

# 加载环境变量
load_dotenv()


def create_skill_agent(model: str = "deepseek-chat", temperature: float = 0):
    """
    创建 Skill Agent

    Args:
        model: 使用的模型 (默认 deepseek-chat)
        temperature: 温度参数
    """
    # 加载 skill 索引
    skill_indexes = skill_loader.load_skill_index()

    # 构建 system prompt
    system_prompt = build_system_prompt(skill_indexes)

    # 获取 DeepSeek 配置
    api_key = os.getenv("DEEP_SEEK_API_KEY")
    base_url = os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1")

    print(f"[Info] Using model: {model}")
    print(f"[Info] API URL: {base_url}")

    # 初始化 LLM (DeepSeek 兼容 OpenAI SDK)
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url
    )

    # 创建 Agent (新版本 langgraph 使用 prompt 参数)
    agent = create_react_agent(llm, tools, prompt=system_prompt)

    return agent


def run_agent(agent, user_message: str) -> str:
    """
    运行 Agent 处理用户请求

    Args:
        agent: 创建的 agent 实例
        user_message: 用户消息
    """
    result = agent.invoke({
        "messages": [("user", user_message)]
    })

    # 返回最终回复
    return result["messages"][-1].content


# 全局 agent 实例
_agent = None


def get_agent():
    """获取全局 agent 实例"""
    global _agent
    if _agent is None:
        _agent = create_skill_agent()
    return _agent


def chat(user_message: str) -> str:
    """简单的对话接口"""
    agent = get_agent()
    return run_agent(agent, user_message)


if __name__ == "__main__":
    # 测试
    print("=== Skills 渐进式披露系统 Demo ===\n")

    # 测试1: 列出所有 skills
    print("测试1: 列出所有 skills")
    print("-" * 40)
    response = chat("list all skills")
    print(f"回复: {response}\n")

    # 测试2: 使用 file-helper skill
    print("测试2: 使用 file-helper skill")
    print("-" * 40)
    response = chat("帮我读取一下当前目录下的某个文件")
    print(f"回复: {response}\n")

    # 测试3: 使用 git-helper skill
    print("测试3: 使用 git-helper skill")
    print("-" * 40)
    response = chat("我想提交代码，应该怎么做？")
    print(f"回复: {response}\n")
