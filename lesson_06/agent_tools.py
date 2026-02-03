import os
import shutil

# === 1. 配置操作目录 ===
# 这里的文件夹名字必须和刚才 generate_files.py 生成的一致
TARGET_DIR = "Agent测试文件库_最终版"

# 确保脚本只操作这个子文件夹，避免误伤
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TARGET_DIR)

# === 2. 工具函数定义 ===

def list_files(args):
    """
    获取目标文件夹中所有待整理的文件列表。
    会忽略文件夹、隐藏文件和 Python 脚本。
    """
    if not os.path.exists(BASE_PATH):
        return f"错误：找不到目录 {BASE_PATH}，请先运行生成文件的脚本。"
    
    files = []
    for filename in os.listdir(BASE_PATH):
        file_path = os.path.join(BASE_PATH, filename)
        
        # 过滤条件：
        # 1. 必须是文件 (os.path.isfile) -> 不处理已经存在的文件夹
        # 2. 不处理 .py 结尾的脚本 -> 防止把 agent 代码自己移走了
        # 3. 不处理 . 开头的隐藏文件 -> 比如 .DS_Store
        if (os.path.isfile(file_path) and 
            not filename.endswith(".py") and 
            not filename.startswith(".")):
            
            files.append(filename)
            
    return files

def move_file(filename, category):
    """
    将文件移动到对应的分类文件夹中。
    如果分类文件夹不存在，会自动创建。
    
    :param filename: 文件名 (例如 "张伟简历.pdf")
    :param category: 分类名称 (例如 "简历", "图片", "财务")
    """
    source_path = os.path.join(BASE_PATH, filename)
    target_folder = os.path.join(BASE_PATH, category)
    target_path = os.path.join(target_folder, filename)

    try:
        # 1. 检查源文件是否存在
        if not os.path.exists(source_path):
            return f"错误：文件 {filename} 不存在。"

        # 2. 检查目标文件夹是否存在，不存在则创建
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        # 3. 移动文件
        shutil.move(source_path, target_path)
        return f"成功：已将 {filename} 移动到 {category} 文件夹。"

    except Exception as e:
        return f"异常：移动 {filename} 时发生错误: {str(e)}"

# === 3. 定义工具箱 (给 AI 看的说明书) ===

tools_schema = [
    # --- 工具 1: 眼睛 (查看文件) ---
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "获取当前待整理文件夹下的所有文件名列表。在开始整理前必须先调用此函数。",
            "parameters": {
                "type": "object",
                "properties": {}, # 没有参数
            }
        }
    },

    # --- 工具 2: 手 (移动文件) ---
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "将指定文件移动到目标文件夹中。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string", 
                        "description": "源文件名"
                    },
                    "category": {
                        "type": "string", 
                        "description": "目标文件夹名称"
                    }
                },
                "required": ["filename", "category"]
            }
        }
    }
]

# --- 4. 【关键】导出函数映射表 ---
# 这一步是为了让主程序可以通过字符串 "move_file" 找到函数对象 move_file
available_functions = {
    "list_files": list_files,
    "move_file": move_file
}