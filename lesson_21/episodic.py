"""
LangChain 记忆实战 - 将【底层事件流】蒸馏为【情景摘要】(Episodic Summary)
"""
import os
import sys
import io
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. 构建蒸馏器 Prompt (强约束目标 JSON 结构)
# ==========================================
EPISODE_PROMPT = """你是一个长期记忆管理者，负责维护一套包含语义记忆、程序性记忆和情景记忆的核心存储库。这些记忆为终身学习AI代理的核心预测模型提供了支持。
请阅读以下由系统底层捕获的【原始事件流】（包含用户的指令、工具的调用、以及系统的报错）。
你的任务是：滤除冗余的重试过程，洞察事件的根本因果，并输出一个标准化的【情景摘要】。

1. **提取与上下文关联**
- 确定关键事实、关系、偏好、推理流程及背景信息
- 对不确定或假设性信息进行标注，并附上置信度等级及推理说明
- 必要时引用支持性信息
2. **比较与更新**
- 处理与现有记忆和预期不符的新信息。
- 整合并压缩冗余记忆，以保持信息密度；根据可靠性和时效性进行强化；通过避免冗余词汇来最大化信噪比。
- 移除错误或冗余的记忆，同时保持内部一致性。
3. **综合与推理**
- 通过演绎、归纳和溯因推理，您能对用户、代理（“我”）或环境得出什么结论？
- 关于最佳响应会出现哪些模式、关系和原则？
- 您能做出哪些概括？
- 请用概率性的可信度和合理性来限定您的结论。

<StandardForImportanceScore>
评分标准 (importance_score)
- 1-3分：日常闲聊、简单的查询
- 4-7分：普通的配置修改、顺利的代码编写
- 8-10分：遇到阻碍的排错、重大的架构变更、未解决的严重Bug
</StandardForImportanceScore>

<OutPutFormat>
请严格以 JSON 格式输出，必须且只能包含以下键：
{{
  "memory_type": "episodic_memory",
  "timestamp": "这里填入当前ISO时间",
  "narrative": "详细内容：包含了起因、经过（尝试了什么）、结果（成功/失败/挂起）",
  "importance_score": 8,
  "action_items": ["推导出的下一步计划1", "推导出的下一步计划2"],
  "metadata": {{"topic": "技术主题"}}
}}
</OutPutFormat>

<Input>
【原始事件流】:
{event_stream}
</Input>



请直接输出 JSON："""

prompt_template = ChatPromptTemplate.from_template(EPISODE_PROMPT)

# ==========================================
# 2. 主函数演示
# ==========================================
def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    load_dotenv()
    
    # 初始化 LLM，开启强制 JSON 模式确保输出稳定性
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.1,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    distill_chain = prompt_template | llm

    # 模拟由上一节的“行车记录仪”自动捕获的底层事件流
    # 场景：开发带有自动战斗机制的肉鸽游戏时，调试 A* 寻路网格
    raw_event_stream = """
    [15:00:01] USER_INPUT: 帮我写一段 AStarGrid2D 的寻路代码，自动战斗用的。
    [15:00:05] TOOL_CALL: 尝试调用 [write_code]，入参: {"target": "AStarGrid2D", "language": "GDScript"}
    [15:00:08] TOOL_RESULT: 代码生成成功并写入 main.gd。
    [15:00:15] USER_INPUT: 运行了一下，角色寻路的路径怎么全歪了？偏离了地图的 TileMap 差不多半个格子的距离。
    [15:00:18] TOOL_CALL: 尝试调用 [search_docs]，入参: {"query": "Godot AStarGrid2D offset TileMap"}
    [15:00:22] TOOL_RESULT: 文档提示：AStarGrid2D 的 cell_size 必须与 TileMap 的 tile_set.tile_size 完全一致，且默认的原点可能需要 half-offset。
    [15:00:25] USER_INPUT: 明白了，我的 TileMap 是 32x32，但我代码里 AStar 的 cell_size 写的是默认的 16x16。我先去改参数，今天太晚了，明天再调避障逻辑。
    """

    print("=" * 60)
    print("🎥 接收到原始事件流（底层监控录像）：")
    print(raw_event_stream.strip())
    print("=" * 60)

    print("\n⏳ 正在启动大模型，执行高维语义蒸馏...\n")
    
    # 注入当前时间，方便 LLM 填充 timestamp
    current_time = datetime.now().isoformat()
    
    # 执行提炼
    result = distill_chain.invoke({
        "event_stream": raw_event_stream
    })
    
    try:
        parsed_data = json.loads(result.content)
        # 强制用系统时间覆盖大模型可能瞎编的时间，保证工程严谨性
        parsed_data["timestamp"] = current_time 
        
        print("✅ 提炼成功！生成的【情景摘要】数据结构如下：")
        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
        
    except json.JSONDecodeError:
        print("❌ JSON 解析失败，原始输出：\n", result.content)

if __name__ == "__main__":
    main()