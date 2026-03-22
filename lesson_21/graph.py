"""
Kùzu GraphRAG 破局 Demo - 动态 Text-to-Cypher + 记忆写入架构
场景：彻底抛弃硬编码，让 LLM 动态生成 Cypher 语句进行图谱检索，同时支持对话中自动提取并写入记忆
"""
import os
import sys
import io
import shutil
import kuzu
from dotenv import load_dotenv
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent

# 解决 Windows 控制台输出乱码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 全局共享数据库路径
_db_path = "./n8n_dynamic_scenario_db"


# ==========================================
# 1. 图谱 Schema 定义 (Pydantic 结构 - 动态扩展版本)
# ==========================================

# 预定义的基础类型（可扩展）
ENTITY_TYPES = ["Person", "Tool", "Language", "Project", "Company", "Framework", "Concept"]
RELATION_TYPES = ["KNOWS", "USES", "SUPPORTS", "WORKS_AT", "INTERESTED_IN", "LEARNS", "BUILDS_WITH"]

class DynamicEntity(BaseModel):
    """动态实体模型 - 支持任意类型和属性"""
    name: str = Field(description="实体的具体名称")
    entity_type: str = Field(description="实体类型，如 Person、Tool、Language 等")
    properties: dict = Field(default_factory=dict, description="实体的额外属性")

class DynamicRelation(BaseModel):
    """动态关系模型 - 支持任意关系类型"""
    source_name: str = Field(description="起始节点的名称")
    source_type: str = Field(description="起始节点的类型")
    target_name: str = Field(description="目标节点的名称")
    target_type: str = Field(description="目标节点的类型")
    relation_type: str = Field(description="关系类型，如 KNOWS、USES、SUPPORTS 等")
    properties: dict = Field(default_factory=dict, description="关系的额外属性")

class DynamicKGExtraction(BaseModel):
    """从用户对话中提取的图谱信息 - 动态扩展版本"""
    entities: List[DynamicEntity] = Field(description="提取出的所有独立实体")
    relations: List[DynamicRelation] = Field(description="实体之间的关系连线")


# ==========================================
# 2. 图谱初始化
# ==========================================
def setup_and_seed_graph():
    """初始化 Kuzu 图谱，并打入初始事实"""
    global _db_path
    if os.path.exists(_db_path):
        if os.path.isdir(_db_path):
            shutil.rmtree(_db_path)
        else:
            os.remove(_db_path)

    db = kuzu.Database(_db_path)
    conn = kuzu.Connection(db)

    print("📦 正在创建图谱 Schema...")

    # 使用通用的 Entity 表存储所有类型的实体
    conn.execute("CREATE NODE TABLE Entity (name STRING, entity_type STRING, properties STRING, PRIMARY KEY (name))")

    # 使用多个关系表，每种关系类型一个
    # 这些关系表通过 relation_type 属性来区分具体关系
    for rel_type in ["KNOWS", "USES", "SUPPORTS", "WORKS_AT", "INTERESTED_IN", "LEARNS", "BUILDS_WITH"]:
        conn.execute(f"CREATE REL TABLE {rel_type} (FROM Entity TO Entity)")

    print("🔨 正在写入初始图谱事实...")

    # 写入初始数据
    initial_facts = [
        ("小李", "Person", "Python", "Language", "KNOWS"),
        ("小李", "Person", "n8n", "Tool", "USES"),
        ("n8n", "Tool", "JavaScript", "Language", "SUPPORTS"),
        ("n8n", "Tool", "Python", "Language", "SUPPORTS"),
    ]

    for s_name, s_type, t_name, t_type, rel_type in initial_facts:
        cypher = f"""
            MERGE (s:Entity {{name: $s_name}})
            SET s.entity_type = $s_type
            MERGE (t:Entity {{name: $t_name}})
            SET t.entity_type = $t_type
            MERGE (s)-[:{rel_type}]->(t)
        """
        conn.execute(cypher, parameters={"s_name": s_name, "s_type": s_type, "t_name": t_name, "t_type": t_type})

    conn.close()
    db.close()
    return True


# ==========================================
# 3. 记忆写入模块
# ==========================================
def extract_and_store_memory(user_input: str):
    """
    从用户输入中提取图谱信息并写入数据库
    """
    print(f"\n🧠 [记忆写入模块] 监听到用户输入：'{user_input}'")
    print("   -> 正在呼叫大模型进行高维结构化抽取...")

    # 初始化 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.0
    )

    prompt = ChatPromptTemplate.from_template("""
    你是一个极其精准的知识图谱数据抽取引擎。
    请从用户的对话中，提取出实体（人、工具、编程语言、项目、公司等）以及它们之间的明确关系。
    注意，消息输入方为Person：小李。

    【实体类型定义】
    - Person: 人，如小李、张三
    - Tool: 工具/平台，如 n8n、Cursor、VSCode
    - Language: 编程语言，如 Python、Rust、JavaScript
    - Project: 项目，如某个开源项目
    - Company: 公司/组织
    - Framework: 框架，如 React、Vue
    - Concept: 概念/理念

    【关系类型定义】
    - KNOWS: 人 掌握 语言
    - USES: 人/公司 使用 工具
    - SUPPORTS: 工具/框架 支持 语言
    - WORKS_AT: 人 在 公司 工作
    - INTERESTED_IN: 人 对 概念/技术 感兴趣
    - LEARNS: 人 正在学习 语言/框架
    - BUILDS_WITH: 人 使用 工具/框架 构建 项目
    - PART_OF: 项目 是 更大项目 的部分

    【用户输入】：
    {input}

    【重要规则】
    1. 编程语言首字母大写：python -> Python, rust -> Rust
    2. 实体类型尽量精确，但也可使用其他合适的类型
    3. 只提取明确表述的关系，不做推测
    4. 如果没有明确的图谱信息，返回空列表

    【输出格式】
    请直接返回 JSON 格式，示例：
    {{"entities": [{{"name": "Rust", "entity_type": "Language"}}, {{"name": "小李", "entity_type": "Person", "properties": {{"level": "beginner"}}}}], "relations": [{{"source_name": "小李", "source_type": "Person", "target_name": "Rust", "target_type": "Language", "relation_type": "LEARNS"}}]}}
    """)

    # 执行抽取
    response = (prompt | llm).invoke({"input": user_input})

    # 解析 JSON
    import json
    import re

    content = response.content.strip()
    # 去掉可能的 markdown 代码块
    content = re.sub(r'```json', '', content)
    content = re.sub(r'```', '', content)
    content = content.strip()

    try:
        extracted = json.loads(content)
        entities = [DynamicEntity(**e) for e in extracted.get("entities", [])]
        relations = [DynamicRelation(**r) for r in extracted.get("relations", [])]
    except Exception as e:
        print(f"   -> ⚠️ JSON 解析失败: {e}，原始内容: {content[:100]}...")
        print("   -> ℹ️ 未提取到有价值的图谱记忆。")
        return

    if not entities and not relations:
        print("   -> ℹ️ 未提取到有价值的图谱记忆。")
        return

    print(f"   -> ✅ 提取成功！发现 {len(entities)} 个实体，{len(relations)} 条关系。")

    # 入库
    db = kuzu.Database(_db_path)
    conn = kuzu.Connection(db)

    print("   -> 🛠️ 正在生成并执行 MERGE 语句防重入库...")

    import json as json_module

    try:
        # 入库实体
        for entity in entities:
            props_str = json_module.dumps(entity.properties) if entity.properties else "{}"
            cypher_node = """
                MERGE (n:Entity {name: $name, entity_type: $entity_type})
                SET n.properties = $properties
            """
            conn.execute(cypher_node, parameters={
                "name": entity.name,
                "entity_type": entity.entity_type,
                "properties": props_str
            })
            print(f"      [节点 Upsert] ({entity.entity_type}) {entity.name}")

        # 入库关系
        for rel in relations:
            cypher_rel = f"""
                MATCH (source:Entity {{name: $s_name}})
                MATCH (target:Entity {{name: $t_name}})
                MERGE (source)-[:{rel.relation_type}]->(target)
            """
            conn.execute(cypher_rel, parameters={
                "s_name": rel.source_name,
                "t_name": rel.target_name
            })
            print(f"      [关系 Upsert] ({rel.source_name}) -[{rel.relation_type}]-> ({rel.target_name})")

        print("   -> 🎉 记忆成功写入 Kùzu 图谱！")
    except Exception as e:
        print(f"   -> ❌ 入库失败: {e}")
    finally:
        conn.close()
        db.close()


# ==========================================
# 4. 图谱检索工具
# ==========================================
@tool
def dynamic_graph_query_tool(user_query: str) -> str:
    """
    高级图谱查询工具：当需要了解技术栈匹配、实体关系、工具支持情况时调用。
    只需传入用户的原始需求，工具会自动生成图查询语言寻找答案。
    """
    print(f"\n🕸️ [图谱检索器被触发] 正在分析原始需求：'{user_query}'")

    cypher_llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.0
    )

    graph_schema = """
    节点(Node)表: Entity
    - 属性: name STRING, entity_type STRING, properties STRING (JSON格式)
    - 主键: name

    关系(Relationship)表: 每种关系类型一张表
    - KNOWS (FROM Entity TO Entity): 人 掌握 语言
    - USES (FROM Entity TO Entity): 人/公司 使用 工具
    - SUPPORTS (FROM Entity TO Entity): 工具/框架 支持 语言
    - LEARNS (FROM Entity TO Entity): 人 正在学习
    - WORKS_AT (FROM Entity TO Entity): 人 在 公司 工作
    - INTERESTED_IN (FROM Entity TO Entity): 人 感兴趣
    - BUILDS_WITH (FROM Entity TO Entity): 组合关系

    注意: 所有节点都在 Entity 表中，通过 entity_type 属性区分具体类型。
    """

    cypher_prompt = ChatPromptTemplate.from_template("""
    你是一个 Kùzu 图数据库的 Cypher 语句专家。
    请根据以下的图谱 Schema 和用户的原始需求，编写一段 Cypher 语句来查询答案。

    【图谱 Schema】
    {schema}

    【用户需求】
    {query}

    【Kùzu 重要语法规则 - 必须严格遵守！】
    1. 你只能返回纯文本的 Cypher 语句，绝不能包含 ```cypher 这样的 markdown 标签！
    2. 节点存储在 Entity 表中，查询时用 Entity {{name: $name}} 匹配
    3. **每种关系类型是独立的表**，如 MATCH (a)-[:KNOWS]->(b) 或 MATCH (a)-[:USES]->(b)
    4. **不存在 r.relation_type 这样的属性**，关系类型由表名决定！
    5. 不要在关系上使用 . 访问属性
    6. 返回尽可能详细的上下文
    7. Kùzu 使用 $param 语法传参
    """)

    chain = cypher_prompt | cypher_llm

    print("   -> 正在呼叫内层大模型生成 Cypher...")
    raw_response = chain.invoke({"schema": graph_schema, "query": user_query})

    generated_cypher = raw_response.content.replace("```cypher", "").replace("```", "").strip()
    print(f"   -> ✍️ [动态生成的 Cypher 语句]:\n      {generated_cypher}")

    db = kuzu.Database(_db_path)
    conn = kuzu.Connection(db)

    try:
        results = conn.execute(generated_cypher)
        output_lines = []
        while results.has_next():
            output_lines.append(str(results.get_next()))

        final_result = "\n".join(output_lines) if output_lines else "未查询到相关连线结果。"
    except Exception as e:
        final_result = f"Cypher 执行失败，报错信息: {str(e)}"
    finally:
        conn.close()
        db.close()

    print(f"   -> 🎯 [数据库返回结果]: {final_result}")

    return f"【图谱真实查询结果】\n{final_result}\n(请根据上述结果回答用户)"


# ==========================================
# 5. 记忆抽取工具（供 Agent 调用）
# ==========================================
@tool
def memory_extraction_tool(user_input: str) -> str:
    """
    记忆写入工具：当用户提到学新技术、用新工具时，调用此工具提取并写入图谱。
    """
    extract_and_store_memory(user_input)
    return "记忆已写入图谱"


# ==========================================
# 6. 主流程
# ==========================================
def main():
    load_dotenv()
    setup_and_seed_graph()

    # 演示：先写入几条记忆
    print("\n" + "=" * 60)
    print("📝 【记忆预写入演示】模拟用户随口说的几句话")
    print("=" * 60)

    chat_history = [
        "其实我昨天刚花了一晚上时间，把 Rust 语言的基础语法学完了。",
        "听说有个叫 Cursor 的工具写代码很猛，我正在尝试用它来办公。",
        "Cursor 对 Rust 的代码补全支持得太完美了！"
    ]

    for sentence in chat_history:
        extract_and_store_memory(sentence)
        print("-" * 60)

    print("\n" + "=" * 60)
    print("🔍 【图谱检索演示】基于新写入的记忆进行查询")
    print("=" * 60)

    # 外层 Agent LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.1
    )

    tools = [dynamic_graph_query_tool, memory_extraction_tool]

    system_prompt = """你是一个资深架构师助理。

你有以下工具可用：
1. dynamic_graph_query_tool: 当用户需求涉及技术选型、工具使用、代码实现时，调用此工具查询图谱
2. memory_extraction_tool: 当用户提到学了新技术、用了新工具时，调用此工具写入记忆

【重要规则】
- 先调用图谱查询工具了解用户技术栈，再回答
- 如果用户提到学了什么新技术或开始用什么新工具，必须调用记忆写入工具

用户当前信息：
- 用户名：小李
"""

    agent = create_agent(llm, tools, system_prompt=system_prompt)

    user_query = "小李要在 n8n 里写一个脚本抓取网页，应该怎么弄？"

    print(f"\n🗣️ 用户提问：'{user_query}'")
    print("=" * 60)

    print("\n🤖 Agent 思考中...")
    response = agent.invoke({"messages": [("user", user_query)]})

    print("\n" + "=" * 60)
    print("🤖 Agent 回复：")
    for message in response["messages"]:
        if hasattr(message, "content") and message.content:
            print(message.content)
    print("=" * 60)


if __name__ == "__main__":
    main()
