import os
import uuid
import chromadb
import ollama
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# ==========================================
# 核心配置区 (动态绝对路径版)
# ==========================================
# 获取当前运行的 Python 脚本所在的绝对目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_PATH = os.path.join(BASE_DIR, "company_rules.md")      
DB_PATH = os.path.join(BASE_DIR, "my_rag_db")                 

SOURCE_NAME = "company_rules.md"            
COLLECTION_NAME = "company_knowledge"       
MODEL_NAME = "quentinz/bge-small-zh-v1.5"

# ==========================================
# 定义 Ollama 嵌入函数 (连接大模型)
# ==========================================
class OllamaEmbeddingFunction:
    def __init__(self, model_name):
        self.model_name = model_name

    def __call__(self, input):
        # 自动调用本地 Ollama 计算句向量
        response = ollama.embed(model=self.model_name, input=input)
        return response['embeddings']
    def name(self):
        return self.model_name

def main():
    # 检查文件是否存在
    if not os.path.exists(FILE_PATH):
        print(f"❌ 找不到文件：{FILE_PATH}，请确保文件存在！")
        return

    # ==========================================
    # 3. 读取并切分 Markdown 文件
    # ==========================================
    print(f"📄 正在读取文件: {FILE_PATH} ...")
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 第一刀：按 Markdown 标题切分 (保留结构化语义)
    headers_to_split_on = [
        ("#", "一级标题"),
        ("##", "二级标题"),
        ("###", "三级标题"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(md_text)

    # 第二刀：按字符长度细切 (适配 bge-small 的 Token 限制)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,     # 限制每块最大 400 字符
        chunk_overlap=50    # 重叠 50 字符，防止一句话被生生劈断
    )
    final_splits = text_splitter.split_documents(md_header_splits)
    
    print(f"✂️ 文本切分完毕，共切出 {len(final_splits)} 个数据块。")

    # ==========================================
    # 4. 初始化 ChromaDB 并清理旧数据 (先删)
    # ==========================================
    print("\n🔌 正在连接 ChromaDB 向量数据库...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 获取或创建集合
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddingFunction(model_name=MODEL_NAME)
    )

    # 🚨 核心逻辑：清理门户！
    print(f"🧹 正在清理数据库中旧的 [{SOURCE_NAME}] 数据...")
    try:
        collection.delete(where={"source": SOURCE_NAME})
        print("✨ 旧数据清理完毕 (或原本就没有旧数据)！")
    except Exception as e:
        print(f"⚠️ 清理时发生异常 (通常是因为集合是空的): {e}")

    # ==========================================
    # 5. 数据格式转换与入库 (后插)
    # ==========================================
    docs_texts = []
    docs_metadatas = []
    docs_ids = []

    for doc in final_splits:
        # 提取纯文本
        docs_texts.append(doc.page_content)
        
        # 提取并完善 Metadata
        metadata = doc.metadata if doc.metadata else {}
        metadata["source"] = SOURCE_NAME  # 戴上“电子脚镣”，方便下次精准删除
        docs_metadatas.append(metadata)
        
        # 生成基于 UUID 的唯一标识符
        docs_ids.append(str(uuid.uuid4()))

    if not docs_texts:
        print("⚠️ 警告：没有解析到任何文本内容，入库终止。")
        return

    print(f"\n🚀 开始将 {len(docs_texts)} 条数据写入数据库 (会自动调用 Ollama 算向量，请耐心等待)...")
    
    # 执行写入 (因为前面已经删干净了，这里直接用 add 即可)
    collection.add(
        documents=docs_texts,
        metadatas=docs_metadatas,
        ids=docs_ids
    )

    print("🎉 入库大功告成！你的 RAG 专属知识库已经准备就绪！")

if __name__ == "__main__":
    main()