"""
原生 ChromaDB + Ollama + LangChain 混合架构
RAG 记忆碎片异步聚合 (Fact Consolidation)
"""
import os
import sys
import io
import uuid
import chromadb
import ollama  # 直接使用原生 ollama 库
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==================== 1. 构建聚合专属 Prompt ====================
CONSOLIDATION_PROMPT = """你是一个专业的记忆碎片整理大师。
你的任务是将长期积累的、存在冗余甚至冲突的【同类记忆碎片】，聚合成一条逻辑严密、反映最新状态的【高密度事实】。

【处理原则】：
1. 提取核心技术栈及最新偏好。
2. 识别并解决冲突（例如：如果过去喜欢A，现在喜欢B，请以时间线靠后的最新状态为准）。
3. 剔除无意义的日期流水账。

【待聚合的记忆碎片】:
{fragments}

请直接输出聚合后的新事实文本（纯文本，不加任何解释）："""

prompt_template = ChatPromptTemplate.from_template(CONSOLIDATION_PROMPT)

# ==================== 2. 核心：记忆聚合器 ====================
class RAGMemoryCompressor:
    def __init__(self, llm, collection):
        self.llm = llm
        self.collection = collection  # 直接接收原生的 Chroma Collection 对象
        self.compress_chain = prompt_template | self.llm
        self.embed_model = "quentinz/bge-small-zh-v1.5" # 指定 Ollama 模型

    def get_embedding(self, text: str):
        """调用原生 ollama 接口获取高维向量"""
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response["embedding"]

    def run_nightly_consolidation(self, target_category: str):
        print(f"\n🌙 [夜间任务] 正在扫描原生 ChromaDB 中 '{target_category}' 的碎片...")

        # 1. 使用原生 Chroma API 进行 Metadata 过滤查询
        collection_data = self.collection.get(
            where={"category": target_category}
        )
        
        ids = collection_data["ids"]
        documents = collection_data["documents"]

        if len(ids) <= 1:
            print("  -> 碎片数量不足 2 条，无需聚合。")
            return

        print(f"  -> 发现 {len(ids)} 条碎片数据，准备执行聚合合并...")
        
        # 2. 拼接碎片文本
        fragments_text = "\n".join([f"碎片 {i+1}: {doc}" for i, doc in enumerate(documents)])

        print("\n【LangChain 大模型正在执行逻辑聚合...】")
        # 3. 呼叫大模型进行逻辑重组
        result = self.compress_chain.invoke({"fragments": fragments_text})
        consolidated_fact = result.content
        print(f"✅ 聚合结果: \n{consolidated_fact}")

        # 4. 【核心物理操作】：原生 API 删除旧碎片
        print(f"\n🗑️ 正在物理删除 {len(ids)} 条旧的高维噪音向量...")
        self.collection.delete(ids=ids)

        # 5. 生成新向量并插入
        new_id = str(uuid.uuid4())
        print(f"💾 正在请求 Ollama 生成新向量并插入 ChromaDB...")
        new_embedding = self.get_embedding(consolidated_fact)
        
        self.collection.add(
            ids=[new_id],
            documents=[consolidated_fact],
            embeddings=[new_embedding],
            metadatas=[{"category": target_category, "consolidated": True}]
        )
        print("🌙 [夜间任务结束] 记忆清洗完成！\n")


# ==================== 3. 场景实战 ====================
def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    load_dotenv()
    
    # --- 1. 初始化各类原生组件 ---
    # 大模型逻辑大脑 (保持使用 LangChain，方便管理 Prompt)
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.1
    )

    # 原生 ChromaDB 客户端
    chroma_client = chromadb.Client()
    # 每次运行先清理旧集合，方便重复测试
    if "rag_memory" in [c.name for c in chroma_client.list_collections()]:
        chroma_client.delete_collection("rag_memory")
        
    collection = chroma_client.create_collection(name="rag_memory")
    embed_model = "quentinz/bge-small-zh-v1.5"

    # --- 2. 模拟早期日常流转：散落的记忆存入 RAG ---
    print("=" * 60)
    print("🌅 [日常流转] 提取用户的隐性事实，调用 Ollama 向量化并原生写入 ChromaDB...")
    
    raw_texts = [
        "1月1日：用户打算学习Vue。",
        "1月4日：用户正在看vue3源码",
        "1月5日：用户在使用Vue 3和TypeScript开发项目。",
        "1月6日：用户夸赞了Vue，称其为伟大的框架。",
        "1月10日：用户觉得React的设计比Vue更优秀。"
    ]
    raw_metadatas = [{"category": "tech_stack"}] * len(raw_texts)
    raw_ids = [str(uuid.uuid4()) for _ in range(len(raw_texts))]
    
    # 批量调用原生 Ollama 获取 Embeddings
    print("   -> 正在连接本地 Ollama 计算 Embeddings...")
    raw_embeddings = [ollama.embeddings(model=embed_model, prompt=text)["embedding"] for text in raw_texts]
    
    # 原生写入 Chroma
    collection.add(
        ids=raw_ids,
        documents=raw_texts,
        embeddings=raw_embeddings,
        metadatas=raw_metadatas
    )
    print(f"✅ 成功写入 {len(raw_texts)} 条独立特征。")
    print("=" * 60)

    # --- 3. 触发异步聚合 ---
    compressor = RAGMemoryCompressor(llm, collection)
    compressor.run_nightly_consolidation(target_category="tech_stack")

    # --- 4. 验收结果 ---
    print("=" * 60)
    print("🔍 [验收查询] 用户提问：“根据我的情况，推荐个图表库？”")
    
    query_text = "前端框架技术栈"
    # 原生计算 query 的向量
    query_embedding = ollama.embeddings(model=embed_model, prompt=query_text)["embedding"]
    
    # 原生 Chroma 相似度检索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        where={"category": "tech_stack"}
    )
    
    # Chroma 原生查询返回的是字典列表结构
    for i, doc in enumerate(results["documents"][0]):
        print(f"🎯 召回记忆 {i+1}: {doc}")
        print(f"   (元数据: {results['metadatas'][0][i]})")
    print("=" * 60)

if __name__ == "__main__":
    main()