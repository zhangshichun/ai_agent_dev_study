# -*- coding: utf-8 -*-
"""
Skills 渐进式披露系统 - 主入口

运行方式:
1. 激活 conda 环境: conda activate ai_agent
2. 运行交互式: python main.py
3. 运行测试: python test_skills.py
"""
import os
import sys

# 设置 UTF-8 编码
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from agent import chat


def main():
    """主函数 - 交互式对话"""
    print("=" * 60)
    print("Skills 渐进式披露系统")
    print("=" * 60)
    print("\n你可以问以下问题：")
    print("  - 有哪些可用的技能？")
    print("  - 帮我读取文件")
    print("  - 我想提交代码")
    print("  - 今天天气怎么样（不需要 skill）")
    print("\n输入 'quit' 或 'exit' 退出\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("再见！")
                break

            if not user_input:
                continue

            response = chat(user_input)
            print(f"\nAssistant: {response}\n")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
