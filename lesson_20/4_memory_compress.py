"""
LangChain 记忆实战 Demo - 带安全缓冲区的滑动滚动摘要 (Summary Buffer Memory)
"""
import os
import sys
import io
import tiktoken
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# ==================== 1. 构建压缩专属 Prompt ====================
COMPRESSION_PROMPT = """你是一个极其高效的记忆整理大师。
请根据【已有记忆摘要】和【需要被压缩的旧对话】，生成一份合并后的【最新记忆摘要】。

要求：
1. 提取讨论的核心背景、目标和关键信息。
2. 剔除废话和寒暄。
3. 如果已有摘要为空，直接总结旧对话即可。

【已有记忆摘要】:
{old_summary}

【需要被压缩的旧对话】:
{history_text}

请直接输出最新记忆摘要（纯文本）："""

prompt_template = ChatPromptTemplate.from_template(COMPRESSION_PROMPT)

# ==================== 2. 核心：带滑动缓冲区的记忆管理器 ====================
class SummaryBufferMemory:
    def __init__(self, llm, max_tokens=120, safe_tokens=60):
        """
        :param max_tokens: 触发压缩的安全水位线 (Demo设为120, 真实工程通常设为 4000-20000)
        :param safe_tokens: 触发压缩时，必须原样保留的最近对话Token数 (Demo设为60, 真实工程通常设为 1000-5000)
        """
        self.llm = llm
        self.max_tokens = max_tokens
        self.safe_tokens = safe_tokens
        
        self.current_summary = ""
        self.messages = []
        
        # 初始化 tiktoken 编码器 (cl100k_base 是主流模型通用的分词器)
        self.encoder = tiktoken.get_encoding("cl100k_base")
        # 压缩调用链
        self.compress_chain = prompt_template | self.llm

    def get_token_count(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def add_message(self, message):
        """添加新消息并检测是否需要触发压缩"""
        self.messages.append(message)
        self._check_and_compress()

    def _check_and_compress(self):
        # 1. 计算当前总 Token 数 (摘要 + 原始消息)
        summary_tokens = self.get_token_count(self.current_summary) if self.current_summary else 0
        messages_tokens = sum(self.get_token_count(msg.content) for msg in self.messages)
        total_tokens = summary_tokens + messages_tokens

        # 2. 如果未超限，安全退出
        if total_tokens <= self.max_tokens:
            return

        print(f"\n[系统拦截] ⚠️ 当前总 Token ({total_tokens}) 超过阈值 ({self.max_tokens})！触发头部(老数据)切割与压缩...")

        messages_to_compress = []

        # 3. 正确逻辑：从“最老的”开始挤牙膏
        # 只要总数超标，且缓冲里至少还有超过 1 条消息（必须给大模型留最后一句原话的上下文）
        while total_tokens > self.max_tokens and len(self.messages) > 1:
            # list.pop(0) 永远弹出数组里最老的那条消息！
            oldest_msg = self.messages.pop(0)
            messages_to_compress.append(oldest_msg)
            
            # 减去被拿走的消息 Token，更新总数
            total_tokens -= self.get_token_count(oldest_msg.content)

        # 4. 执行合并压缩
        if messages_to_compress:
            history_text = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}" for m in messages_to_compress])
            
            print(f"  -> 正在把最老的 {len(messages_to_compress)} 条消息进行压缩...")
            result = self.compress_chain.invoke({
                "old_summary": self.current_summary if self.current_summary else "（无）",
                "history_text": history_text
            })
            
            # 更新状态
            self.current_summary = result.content
            print("  -> ✅ 压缩完成！")

    def print_current_state(self):
        """打印大模型当下能看到的真实上下文"""
        print("\n" + "=" * 50)
        print("【当前发给大模型的真实 Context Window】")
        print(f"👉 1. 系统摘要: \n{self.current_summary if self.current_summary else '（空）'}")
        print("\n👉 2. 上下文消息原文:")
        for i, msg in enumerate(self.messages):
            role = "🧑 User" if isinstance(msg, HumanMessage) else "🤖 Agent"
            print(f"   [{i+1}] {role}: {msg.content}")
        print("=" * 50 + "\n")


# ==================== 3. 主函数实战演示 ====================
def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    load_dotenv()
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEP_SEEK_API_KEY"),
        base_url=os.getenv("DEEP_SEEK_API_URL", "https://api.deepseek.com/v1"),
        temperature=0.1
    )

    # 初始化记忆管理器 (阈值设得很低，方便演示)
    memory = SummaryBufferMemory(llm, max_tokens=150, safe_tokens=100)

    # 模拟真实的长对话过程
    dialogue_turns = [
        ("User", "梦姬，我准备开发一个公司的内部后台管理系统。"),
        ("Agent", "好的，主人！开发后台系统是个大工程，您打算前端用什么框架呢？"),
        ("User", "我在纠结选 Vue3 还是 React。团队里主要是后端开发，前端经验一般。"),
        ("Agent", "既然团队前端经验一般，强烈推荐 Vue3。它的学习曲线更平缓，而且官方文档对新手非常友好。"),
        ("User", "有道理。那 UI 组件库呢？有什么开箱即用的推荐吗？"),
        ("Agent", "配合 Vue3，目前国内生态最好的是 Element Plus。它提供了大量的现成组件，能帮您节省极大的画界面时间。")
    ]

    print("\n🟢 开始早期的需求沟通（此时 Token 在安全线内，不会压缩）：")
    for role, content in dialogue_turns:
        print(f"💬 [{role} 发送]: {content[:20]}...")
        msg = HumanMessage(content=content) if role == "User" else AIMessage(content=content)
        memory.add_message(msg)

    # 打印前 6 轮对话完好的状态
    memory.print_current_state()

if __name__ == "__main__":
    main()