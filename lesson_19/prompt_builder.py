# -*- coding: utf-8 -*-
"""
Prompt 构建器 - 构建包含 skill 索引的 system prompt
"""
from typing import List
from skill_loader import SkillIndex


def build_skills_prompt(skill_indexes: List[SkillIndex]) -> str:
    """
    构建 skills 相关的 system prompt 部分

    核心思想：渐进式披露
    - 初始只注入 skill 的索引（name + description）
    - 让 LLM 自主判断需要哪个 skill
    - 通过 lookup_skill 工具按需读取完整内容
    """
    if not skill_indexes:
        return ""

    # 构建 XML 格式的索引
    skills_xml = "<available_skills>\n"
    for idx in skill_indexes:
        skills_xml += f"""  <skill>
    <name>{idx.name}</name>
    <description>{idx.description}</description>
  </skill>
"""
    skills_xml += "</available_skills>"

    # 构建指令 - 让 LLM 知道何时需要读取 skill
    instructions = """## Skills 使用指南 (渐进式披露)

你可以通过 skills 来处理特定领域的任务。

### 可用 Skills

{skills_xml}

### 使用规则

1. **识别时机**: 当用户请求涉及特定技能领域时（如文件操作、Git操作、代码编写等），应考虑使用 skill

2. **按需读取**:
   - 如果某个 skill 明显适用于用户请求 → 使用 `lookup_skill` 工具读取完整内容
   - 如果多个 skill 都可能适用 → 选择最相关的一个读取
   - 如果没有 skill 明显适用 → 不需要读取任何 skill

3. **执行指令**: 读取 skill 后，按照其中的命令和说明执行任务

4. **引用处理**: skill 文档中可能引用其他文档（使用 路径 格式，如 ../docs/xxx.md），如需读取可使用 `read_reference` 工具

### 注意事项

- 不要在初始阶段就读取所有 skill
- 只在确定需要某个 skill 后才读取
- 读取后严格按照 skill 的指令执行
""".format(skills_xml=skills_xml)

    return instructions


def build_system_prompt(skill_indexes: List[SkillIndex]) -> str:
    """构建完整的 system prompt"""
    skills_prompt = build_skills_prompt(skill_indexes)

    base_prompt = """你是一个智能 AI 助手。

你的职责是帮助用户完成各种任务。当你需要处理特定领域的问题时，可以使用可用的 skills。

一般流程：
1. 理解用户请求
2. 判断是否需要使用 skill
3. 如需要，使用工具读取 skill 完整内容
4. 按照 skill 指令执行

如果用户请求不涉及任何已知的 skill 领域，直接回答即可。

"""

    return base_prompt + "\n\n" + skills_prompt


if __name__ == "__main__":
    from skill_loader import skill_loader

    indexes = skill_loader.load_skill_index()
    prompt = build_system_prompt(indexes)
    print(prompt)
