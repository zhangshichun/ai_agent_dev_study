from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# 1. 模拟一篇真实的 Markdown 文档
markdown_text = """
# DeepSeek 使用指南

## 1. 简介
DeepSeek 是一家专注于大语言模型的初创公司。
它的特点是性价比极高，且模型能力在开源界名列前茅。

## 2. API 调用
### 2.1 准备工作
你需要先去官网注册账号，并获取一个 API Key。请妥善保管这个 Key。

### 2.2 Python 代码示例
这里是一段如何用 Python 发起请求的代码...（假设这里有一万字）
"""

# --- 第一步：按 Markdown 标题切分 ---
# 告诉程序，我们要识别哪些级别的标题，并给它们起个名字
headers_to_split_on = [
    ("#", "主标题"),       # 识别 # 
    ("##", "二级标题"),    # 识别 ##
    ("###", "三级标题"),   # 识别 ###
]

# 初始化 Markdown 切分器
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False  # 保留文本里的 # 号（如果你不想要可以设为 True）
)

# 执行第一步切分
md_header_splits = markdown_splitter.split_text(markdown_text)

# --- 第二步：按字符长度二次切分 ---
# 如果某个标题下的内容特别长（比如超过了 bge-small 的 512 限制），需要再切碎
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,     # 限制每块最大 400 字符
    chunk_overlap=50    # 重叠 50 字符防断句
)

# 执行第二步切分 (注意这里用的是 split_documents，因为它已经是结构化数据了)
final_splits = text_splitter.split_documents(md_header_splits)

# --- 查看结果 ---
print(f"一共切成了 {len(final_splits)} 块\n")

for i, doc in enumerate(final_splits):
    print(f"--- 第 {i+1} 块 ---")
    print(f"📝 内容: {doc.page_content.strip()}")
    # 除了切片，它还生成了非常关键的 metadata
    print(f"🏷️ 标签(Metadata): {doc.metadata}\n")