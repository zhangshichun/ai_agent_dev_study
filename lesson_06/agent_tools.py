import os
import shutil
import json

# ==========================================
# 1. 配置区域
# ==========================================
# ⚠️ 注意：这里的名字必须和 generate_files.py 生成的文件夹一致
TARGET_DIR_NAME = "Agent测试文件库_最终版"

# 获取当前脚本所在目录的绝对路径，锁定操作范围
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TARGET_DIR_NAME)

# ==========================================
# 2. 工具函数定义 (修复版)
# ==========================================

def list_files(args=None):
    """
    获取目标文件夹下的所有文件名。
    返回: JSON 格式的字符串
    """
    # 安全检查
    if not os.path.exists(BASE_PATH):
        return json.dumps({
            "error": f"找不到目录 {TARGET_DIR_NAME}，请先运行 generate_files.py 生成测试文件。"
        }, ensure_ascii=False)
    
    files = []
    try:
        for f in os.listdir(BASE_PATH):
            f_path = os.path.join(BASE_PATH, f)
            # 过滤逻辑：只看文件，忽略隐藏文件(.开头)
            if os.path.isfile(f_path) and not f.startswith('.'):
                files.append(f)
        
        # 必须返回 JSON 字符串，而不是 Python 列表
        return json.dumps({"files": files}, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def move_file(args):
    """
    移动文件到指定分类文件夹。
    Args:
        args (dict): 包含 'filename' 和 'category' 的字典
    返回: JSON 格式的字符串
    """
    # 接收字典参数，手动提取，防止 TypeError
    filename = args.get("filename")
    category = args.get("category")
    
    if not filename or not category:
        return json.dumps({"error": "参数缺失: 需要 filename 和 category"}, ensure_ascii=False)

    source_file = os.path.join(BASE_PATH, filename)
    target_folder = os.path.join(BASE_PATH, category)
    target_file = os.path.join(target_folder, filename)

    try:
        # 检查源文件
        if not os.path.exists(source_file):
            return json.dumps({"error": f"文件不存在: {filename}"}, ensure_ascii=False)

        # 检查并创建目标目录
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        # 移动文件
        shutil.move(source_file, target_file)
        
        # 返回 JSON 字符串
        return json.dumps({
            "status": "success", 
            "moved_to": category,
            "filename": filename
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# ==========================================
# 3. 工具导出 (Mapping & Schema)
# ==========================================

# 函数映射表 (供主程序调用)
available_functions = {
    "list_files": list_files,
    "move_file": move_file
}

# 工具定义 (供 LLM 阅读)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "查看当前文件夹里有哪些文件待处理。",
            "parameters": {
                "type": "object", 
                "properties": {}
            }
        }
    },
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
                        "description": "源文件名 (必须是 list_files 返回列表中存在的名字)"
                    },
                    "category": {
                        "type": "string", 
                        "description": "目标文件夹名称 (例如 'Images', '合同文件', '简历')"
                    }
                },
                "required": ["filename", "category"]
            }
        }
    }
]