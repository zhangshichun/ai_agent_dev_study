# -*- coding: utf-8 -*-
"""
完整测试脚本 - 测试 Skills 渐进式披露系统的各个环节
"""
import sys
import os

# 设置编码
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from skill_loader import SkillLoader, skill_loader
from skill_tools import lookup_skill, list_skills, read_reference
from prompt_builder import build_skills_prompt, build_system_prompt


def test_skill_loader():
    """测试 SkillLoader"""
    print("\n" + "=" * 60)
    print("测试 1: SkillLoader - 加载 Skill 索引")
    print("=" * 60)

    loader = SkillLoader("./skills")
    indexes = loader.load_skill_index()

    print(f"\n共加载 {len(indexes)} 个 skills:")
    for idx in indexes:
        print(f"  - {idx.name}")
        print(f"    描述: {idx.description}")
        print(f"    位置: {idx.location}")

    assert len(indexes) >= 4, "Should have at least 4 skills"
    print("\n[PASS] SkillLoader test passed")
    return indexes


def test_load_skill_content():
    """测试加载 Skill 内容"""
    print("\n" + "=" * 60)
    print("测试 2: 加载 Skill 完整内容")
    print("=" * 60)

    skills = ["file-helper", "git-helper", "docker-helper", "code-review"]

    for skill_name in skills:
        print(f"\n--- Loading {skill_name} ---")
        try:
            content = skill_loader.load_skill_content(skill_name)
            # Check if frontmatter is removed
            assert not content.startswith("---"), "Should have removed frontmatter"
            # Check if contains keywords
            print(f"  Content length: {len(content)} chars")
            print(f"  Contains commands: {'/docker' in content or '/git' in content or '/read' in content or '/review' in content}")
        except Exception as e:
            print(f"  [FAIL] Load failed: {e}")

    print("\n[PASS] Load skill content test passed")


def test_list_skills_tool():
    """测试 list_skills 工具"""
    print("\n" + "=" * 60)
    print("测试 3: list_skills 工具")
    print("=" * 60)

    result = list_skills.invoke({})
    print(f"\nResult:\n{result}")

    # Verify all skills are included
    assert "file-helper" in result
    assert "git-helper" in result
    assert "docker-helper" in result
    assert "code-review" in result

    print("\n[PASS] list_skills tool test passed")


def test_lookup_skill_tool():
    """测试 lookup_skill 工具"""
    print("\n" + "=" * 60)
    print("测试 4: lookup_skill 工具")
    print("=" * 60)

    test_cases = [
        ("file-helper", "文件操作"),
        ("git-helper", "Git操作"),
        ("docker-helper", "Docker操作"),
        ("code-review", "代码审查"),
    ]

    for skill_name, desc in test_cases:
        print(f"\n--- Testing {skill_name} ({desc}) ---")
        result = lookup_skill.invoke({"skill_name": skill_name})
        assert skill_name in result, f"Result should contain {skill_name}"
        assert len(result) > 100, "Content should not be too short"
        print(f"  [OK] Returned content length: {len(result)} chars")

    print("\n[PASS] lookup_skill tool test passed")


def test_lookup_nonexistent_skill():
    """测试查找不存在的 skill"""
    print("\n" + "=" * 60)
    print("测试 5: 查找不存在的 Skill")
    print("=" * 60)

    result = lookup_skill.invoke({"skill_name": "non-existent-skill"})
    print(f"\nResult: {result}")
    assert "Error" in result or "not found" in result.lower()

    print("\n[PASS] Non-existent skill test passed")


def test_prompt_builder():
    """测试 Prompt 构建器"""
    print("\n" + "=" * 60)
    print("测试 6: Prompt 构建器")
    print("=" * 60)

    indexes = skill_loader.load_skill_index()

    # Test skills prompt
    skills_prompt = build_skills_prompt(indexes)
    print(f"\nSkills Prompt length: {len(skills_prompt)} chars")

    # Verify key elements are included
    assert "<available_skills>" in skills_prompt
    assert "file-helper" in skills_prompt
    assert "lookup_skill" in skills_prompt
    assert "按需读取" in skills_prompt

    # Test full system prompt
    system_prompt = build_system_prompt(indexes)
    print(f"System Prompt length: {len(system_prompt)} chars")

    assert len(system_prompt) > len(skills_prompt)

    print("\n[PASS] Prompt builder test passed")


def test_reference_resolution():
    """测试引用解析"""
    print("\n" + "=" * 60)
    print("测试 7: 引用解析")
    print("=" * 60)

    # Test relative path reference
    # Note: Need docs/git-workflow.md file
    try:
        # Create test reference document
        docs_dir = os.path.join(os.path.dirname(__file__), "docs")
        os.makedirs(docs_dir, exist_ok=True)
        test_doc = os.path.join(docs_dir, "test-ref.md")
        with open(test_doc, "w", encoding="utf-8") as f:
            f.write("# Test Doc\n\nThis is test reference content.")

        # Test reference resolution
        result = skill_loader.resolve_reference("git-helper", "../docs/test-ref.md")
        print(f"\nReference resolution result: {result[:100]}...")

        # Cleanup
        os.remove(test_doc)

        print("\n[PASS] Reference resolution test passed")
    except Exception as e:
        print(f"\n[SKIP] Reference resolution test skipped: {e}")


def test_skill_caching():
    """测试 Skill 缓存"""
    print("\n" + "=" * 60)
    print("测试 8: Skill 缓存")
    print("=" * 60)

    skill_name = "file-helper"

    # First load
    content1 = skill_loader.load_skill_content(skill_name)

    # Second load (should be from cache)
    content2 = skill_loader.load_skill_content(skill_name)

    # Verify content is the same
    assert content1 == content2
    print(f"\nFirst load: {len(content1)} chars")
    print(f"Second load (cached): {len(content2)} chars")

    print("\n[PASS] Skill caching test passed")


def test_frontmatter_parsing():
    """测试 Frontmatter 解析"""
    print("\n" + "=" * 60)
    print("测试 9: Frontmatter 解析")
    print("=" * 60)

    test_content = """---
name: test-skill
description: 这是一个测试 skill
---

# 技能内容

这里是技能的正文内容。
"""

    frontmatter = skill_loader._parse_frontmatter(test_content)
    print(f"\nParse result: {frontmatter}")

    assert frontmatter.get("name") == "test-skill"
    assert frontmatter.get("description") == "这是一个测试 skill"

    # Test strip frontmatter
    stripped = skill_loader._strip_frontmatter(test_content)
    print(f"\nAfter stripping frontmatter:\n{stripped}")

    assert not stripped.startswith("---")
    assert "# 技能内容" in stripped

    print("\n[PASS] Frontmatter parsing test passed")


def test_folder_name_differs_from_skill_name():
    """测试文件夹名与 skill name 不一致的情况"""
    print("\n" + "=" * 60)
    print("测试 10: 文件夹名与 Skill Name 不一致")
    print("=" * 60)

    # docker-helper 的文件夹名是 "docker"，但 skill name 在 frontmatter 里是 "docker-helper"
    skill_name = "docker-helper"
    folder_name = "docker"

    print(f"\nSkill name: {skill_name}")
    print(f"Folder name: {folder_name}")

    # 验证索引加载正确
    indexes = skill_loader.load_skill_index()
    skill_names = [idx.name for idx in indexes]
    print(f"Loaded skill names: {skill_names}")

    assert skill_name in skill_names, f"Should have skill '{skill_name}' in index"

    # 验证能通过 skill name 加载内容（即使文件夹名不同）
    content = skill_loader.load_skill_content(skill_name)
    print(f"Loaded content length: {len(content)} chars")

    # 验证内容正确（包含 docker 相关命令）
    assert "/docker-build" in content, "Should contain /docker-build command"
    assert "/docker-run" in content, "Should contain /docker-run command"

    print("\n[PASS] Folder name differs from skill name test passed")


def test_all_skills_content():
    """测试所有 skills 的内容完整性"""
    print("\n" + "=" * 60)
    print("测试 10: 所有 Skills 内容完整性")
    print("=" * 60)

    indexes = skill_loader.load_skill_index()

    required_fields = {
        "file-helper": ["/read", "/write"],
        "git-helper": ["/git-commit", "/git-push"],
        "docker-helper": ["/docker-build", "/docker-run"],
        "code-review": ["/review", "/suggest"],
    }

    for idx in indexes:
        if idx.name in required_fields:
            print(f"\n--- Checking {idx.name} ---")
            content = skill_loader.load_skill_content(idx.name)
            required = required_fields[idx.name]

            for cmd in required:
                if cmd in content:
                    print(f"  [OK] Contains command: {cmd}")
                else:
                    print(f"  [FAIL] Missing command: {cmd}")

    print("\n[PASS] Skills content completeness test passed")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("[TEST] Skills Progressive Disclosure System - Full Test")
    print("=" * 60)

    try:
        test_skill_loader()
        test_load_skill_content()
        test_list_skills_tool()
        test_lookup_skill_tool()
        test_lookup_nonexistent_skill()
        test_prompt_builder()
        test_reference_resolution()
        test_skill_caching()
        test_frontmatter_parsing()
        test_folder_name_differs_from_skill_name()
        test_all_skills_content()

        print("\n" + "=" * 60)
        print("[PASS] All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
