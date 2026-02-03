import os
import json
import shutil
from openai import OpenAI
from dotenv import load_dotenv
from agent_tools import tools_schema, available_functions
# 加载环境变量
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEP_SEEK_API_KEY"), 
    base_url=os.getenv("DEEP_SEEK_API_URL")
)
# 必须和 generate_files.py 生成的文件夹名字完全一致
TARGET_DIR_NAME = "Agent测试文件库_最终版"

# ==========================================
# 2. 定义工具函数 (Agent 的双手)
# ==========================================

# 获取脚本所在目录的绝对路径，确保不跑偏
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TARGET_DIR_NAME)

def list_files(args=None):
    """获取目标文件夹下的所有文件名"""
    if not os.path.exists(BASE_PATH):
        return json.dumps({"error": f"找不到目录 {TARGET_DIR_NAME}，请先运行生成脚本。"})
    
    files = []
    # 遍历目录
    for f in os.listdir(BASE_PATH):
        f_path = os.path.join(BASE_PATH, f)
        # 只看文件，忽略隐藏文件和Python脚本
        if os.path.isfile(f_path) and not f.startswith('.'):
            files.append(f)
            
    return json.dumps({"files": files}, ensure_ascii=False)

def move_file(args):
    """移动文件到指定分类文件夹"""
    filename = args.get("filename")
    category = args.get("category")
    
    if not filename or not category:
        return json.dumps({"error": "参数缺失"})

    source_file = os.path.join(BASE_PATH, filename)
    target_folder = os.path.join(BASE_PATH, category)
    target_file = os.path.join(target_folder, filename)

    try:
        if not os.path.exists(source_file):
            return json.dumps({"error": f"文件 {filename} 不存在"})
            
        if not os.path.exists(target_folder):
            os.makedirs(target_folder) # 自动创建分类文件夹
            
        shutil.move(source_file, target_file)
        return json.dumps({"status": "success", "moved_to": category})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ==========================================
# Agent 主程序 (大脑与循环)
# ==========================================
def run_agent():

    # --- System Prompt: 赋予它灵魂 ---
    system_prompt = """
        你是一个专业的文件整理智能助手。你的目标是将杂乱的文件夹整理得井井有条。

        【执行流程】
        1. 首先调用 `list_files` 获取所有文件。
        2. 针对每个文件，分析其文件名和后缀，决定其归属。
        3. 调用 `move_file` 执行移动。

        【核心规则 - 优先级最高】
        如果文件名中包含明确的中文语义，请无视后缀，优先建立中文语义文件夹：
        - 包含“发票”、“报销” -> 移动到 "财务发票"
        - 包含“合同”、“协议” -> 移动到 "合同文件"
        - 包含“简历” -> 移动到 "候选人简历"
        
        【次要策略】(次要优先级)
        请根据文件类型建立文件夹，规则如下：
        - 图片: 图片文件 (.jpg, .png, .gif, .svg 等)
        - 文档: 文档文件 (.pdf, .docx, .txt, .md 等)
        - 数据: 数据表格 (.xlsx, .csv, .json)
        - 代码: 代码脚本 (.py, .js, .html, .css)
        - 压缩包: 压缩包 (.zip, .rar, .7z)



        【注意事项】
        - 可以并行调用工具以提高效率。
        - 遇到无法识别的文件，归类到 "Misc"。
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请帮我整理一下文件夹里的文件，现在的太乱了。"}
    ]

    print(f"🤖 Agent 启动! 正在监管目录: {TARGET_DIR_NAME}")
    print("-" * 50)

    # 循环限制，防止死循环
    MAX_TURNS = 60
    
    for turn in range(MAX_TURNS):
        print(f"🔄 第 {turn + 1} 轮思考中...")
        
        # 1. 呼叫大模型
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools_schema,
        )
        
        ai_message = response.choices[0].message
        messages.append(ai_message) # 必须把 AI 的回复加入历史

        # 2. 检查是否有工具调用
        if ai_message.tool_calls:
            print(f"⚡ 触发了 {len(ai_message.tool_calls)} 个操作请求!")
            
            # 3. 遍历并执行所有工具调用 (Parallel Function Calling)
            for tool_call in ai_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 打印日志
                if function_name == "move_file":
                    print(f"   📂 移动: {function_args['filename']} -> [{function_args['category']}]")
                else:
                    print(f"   👀 执行: {function_name}")

                # 真正的执行环节
                function_to_call = available_functions[function_name]
                function_response = function_to_call(function_args)

                # 4. 将结果反馈给 AI
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response,
                })
        else:
            # 如果没有工具调用，说明任务结束，AI 给出了总结
            print("-" * 50)
            print("✅ 任务完成! AI 总结:")
            print(ai_message.content)
            break

if __name__ == "__main__":
    run_agent()