# -*- coding: utf-8 -*-
"""
Skill 加载器 - 负责加载 skill 索引和内容
"""
from pathlib import Path
from typing import List, Dict, Optional
import re
import yaml


class SkillIndex:
    """Skill 索引"""
    def __init__(self, name: str, description: str, location: str):
        self.name = name
        self.description = description
        self.location = location


class SkillLoader:
    """Skill 加载器"""

    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = Path(skills_dir)
        self._cache: Dict[str, str] = {}

    def load_skill_index(self) -> List[SkillIndex]:
        """加载所有 skills 的索引"""
        indexes = []

        if not self.skills_dir.exists():
            return indexes

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            # 解析 frontmatter
            content = skill_md.read_text(encoding='utf-8')
            frontmatter = self._parse_frontmatter(content)

            indexes.append(SkillIndex(
                name=frontmatter.get('name', skill_dir.name),
                description=frontmatter.get('description', ''),
                location=str(skill_md)
            ))

        return indexes

    def load_skill_content(self, skill_name: str) -> str:
        """按需加载单个 skill 的完整内容"""
        if skill_name in self._cache:
            return self._cache[skill_name]

        # 查找 skill 目录
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            # 尝试在所有 skill 中查找
            for s in self.skills_dir.iterdir():
                if s.is_dir() and s.name == skill_name:
                    skill_dir = s
                    break

        if not skill_dir.exists():
            raise FileNotFoundError(f"Skill not found: {skill_name}")

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found for: {skill_name}")

        content = skill_md.read_text(encoding='utf-8')
        # 去除 frontmatter，只保留正文
        content = self._strip_frontmatter(content)

        self._cache[skill_name] = content
        return content

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """解析 YAML frontmatter"""
        pattern = r'^---\n(.*?)\n---'
        match = re.match(pattern, content, re.DOTALL)
        if not match:
            return {}

        try:
            return yaml.safe_load(match.group(1)) or {}
        except:
            return {}

    def _strip_frontmatter(self, content: str) -> str:
        """去除 frontmatter"""
        pattern = r'^---\n.*?\n---\n?'
        return re.sub(pattern, '', content, count=1, flags=re.DOTALL).strip()

    def resolve_reference(self, skill_name: str, reference: str) -> str:
        """
        解析 skill 内部的引用（如 @../docs/xxx.md）
        支持相对路径解析
        """
        # 去除 @ 符号
        ref_path = reference.lstrip('@').strip()

        # 获取 skill 所在目录
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            return f"Error: Skill directory not found: {skill_name}"

        # 解析相对路径
        base_dir = skill_dir.parent
        target_path = (base_dir / ref_path).resolve()

        if not target_path.exists():
            return f"Error: Reference not found: {reference}"

        # 读取引用的文件内容
        try:
            return target_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading reference {reference}: {e}"


# 全局实例
skill_loader = SkillLoader()


if __name__ == "__main__":
    # 测试
    indexes = skill_loader.load_skill_index()
    for idx in indexes:
        print(f"- {idx.name}: {idx.description}")
        print(f"  Location: {idx.location}")
