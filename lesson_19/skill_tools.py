# -*- coding: utf-8 -*-
"""
Skill 工具 - LangChain 工具定义
"""
from langchain_core.tools import tool
from skill_loader import skill_loader


@tool
def lookup_skill(skill_name: str) -> str:
    """
    查找并读取指定 skill 的完整内容。

    当用户请求涉及特定技能（如文件操作、Git操作、代码编写等）时，
    使用此工具读取对应的 skill 文档，然后按照 skill 的指令执行。

    Args:
        skill_name: skill 的名称，例如 "file-helper", "git-helper"

    Returns:
        skill 的完整内容，包含命令列表和使用方法
    """
    try:
        content = skill_loader.load_skill_content(skill_name)
        return f"# Skill: {skill_name}\n\n{content}"
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error loading skill: {str(e)}"


@tool
def list_skills() -> str:
    """
    列出所有可用的 skills。

    当用户询问"你能做什么"或"有哪些技能"时，使用此工具。

    Returns:
        所有可用 skill 的索引信息，包含名称和描述
    """
    indexes = skill_loader.load_skill_index()

    if not indexes:
        return "No skills available."

    result = "## Available Skills\n\n"
    for idx in indexes:
        result += f"- **{idx.name}**: {idx.description}\n"

    result += "\n当用户的请求涉及以上领域时，请使用 `lookup_skill` 工具读取对应的 skill 文档。"

    return result


@tool
def read_reference(skill_name: str, reference: str) -> str:
    """
    读取 skill 内部引用的文档。

    在 skill 文档中可能会引用其他文档（如 ../docs/xxx.md），
    使用此工具解析并读取引用的内容。

    Args:
        skill_name: 当前 skill 的名称
        reference: 引用路径，例如 "../docs/git-workflow.md"

    Returns:
        引用的文档内容
    """
    return skill_loader.resolve_reference(skill_name, reference)


# 导出所有工具
tools = [lookup_skill, list_skills, read_reference]
