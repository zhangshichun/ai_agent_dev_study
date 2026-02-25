import os
import chromadb
import ollama
from dotenv import load_dotenv
from openai import OpenAI

# ==========================================
# 1. 基础配置
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_rag_db")
COLLECTION_NAME = "company_knowledge"
MODEL_NAME = "quentinz/bge-small-zh-v1.5"

load_dotenv()
api_key = os.getenv("DEEP_SEEK_API_KEY")
base_url = os.getenv("DEEP_SEEK_API_URL")

llm_client = OpenAI(api_key=api_key, base_url=base_url)

# ==========================================
# 2. 准备向量数据库的连接 (带终极防弹补丁)
# ==========================================
class OllamaEmbeddingFunction:
    def __init__(self, model_name):
        self.model_name = model_name

    def __call__(self, input):
        response = ollama.embed(model=self.model_name, input=input)
        return response['embeddings']
        
    def name(self): 
        return self.model_name

    def embed_query(self, input):
        return self.__call__(input)
        
    def embed_documents(self, input):
        return self.__call__(input)

db_client = chromadb.PersistentClient(path=DB_PATH)
embedding_func = OllamaEmbeddingFunction(model_name=MODEL_NAME)

try:
    collection = db_client.get_collection(
        name=COLLECTION_NAME, 
        embedding_function=embedding_func
    )
except Exception as e:
    print("❌ 找不到集合，请确保你已经成功运行了入库脚本！")
    exit()

print("🎉 知识库加载成功！《不正经有限公司》 管理助手已就绪。")
print("==========================================")

# ==========================================
# 3. 开启命令行交互循环
# ==========================================
while True:
    # 获取用户终端输入
    user_question = input("\n🙋 请输入你的问题 (输入 'q' 或 'exit' 退出): ").strip()
    
    # 判断是否退出
    if user_question.lower() in ['q', 'exit', 'quit']:
        print("👋 拜拜！下次再聊！")
        break
        
    # 如果用户直接按了回车没打字，就跳过这次循环
    if not user_question:
        continue

    print(f"\n🔍 正在知识库中检索...")

    # A：检索 (Retrieval)
    results = collection.query(
        query_texts=[user_question],
        n_results=3  # 提取最相关的 3 个片段
    )

    retrieved_context = ""
    distances = results['distances'][0]
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]

    for i in range(len(documents)):
        source = metadatas[i].get('source', '未知来源')
        retrieved_context += f"--- 来源文档: {source} (差异度: {distances[i]:.4f}) ---\n"
        retrieved_context += f"{documents[i]}\n\n"

    # B：增强生成 (Augmented Generation)
    print("🧠 DeepSeek 正在思考...")

    system_prompt = f"""
    你是一个专业的内部知识库问答助手。
    请**严格根据**以下<参考资料>中的信息来回答用户的问题。
    如果参考资料中没有明确提及该问题的答案，请如实回答“根据现有资料无法得出结论”，绝对不要编造！

    <参考资料>
    {retrieved_context}
    </参考资料>
    """

    try:
        response = llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question},
            ],
            temperature=0.1 
        )
        
        print("\n🤖 助手回答：")
        print(response.choices[0].message.content)
        print("\n" + "="*40) # 打印一条分割线，方便看下一次提问

    except Exception as e:
        print(f"\n❌ 调用 DeepSeek 失败: {e}")