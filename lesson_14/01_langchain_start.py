import os
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

def get_weather(city: str) -> str:
    """获取给定城市的天气情况"""
    return f"{city}未来10天很热，温度大概45°C"

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEP_SEEK_API_KEY"),
    base_url=os.getenv("DEEP_SEEK_API_URL"),
    temperature=0.7
)

agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="你是一个经验丰富的天气预测员",
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "杭州的天气怎么样？"}]}
)

print(response["messages"][-1].content)