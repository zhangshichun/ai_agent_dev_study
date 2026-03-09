# Skills 渐进式披露系统

基于 LangChain + LangGraph + DeepSeek 实现的 Skills 渐进式披露系统。

## 核心思想

**渐进式披露（Progressive Disclosure）**：不一次性将所有 skill 的完整内容注入到 System Prompt，而是：

1. **初始阶段**：只注入 skill 的**索引**（name + description）
2. **决策阶段**：Agent（LLM）根据用户请求自主判断需要哪个 skill
3. **按需读取**：Agent 主动调用工具读取对应 skill 的完整 SKILL.md
4. **执行阶段**：按照 skill 定义的指令执行

## 项目结构

```
lesson_19/
├── skills/                      # Skill 定义目录
│   ├── file-helper/SKILL.md    # 文件操作 skill
│   ├── git-helper/SKILL.md     # Git 操作 skill
│   ├── docker-helper/SKILL.md  # Docker 操作 skill
│   └── code-review/SKILL.md    # 代码审查 skill
├── docs/                        # 引用的文档
│   └── git-workflow.md
├── skill_loader.py             # Skill 加载器
├── skill_tools.py              # LangChain 工具定义
├── prompt_builder.py           # System Prompt 构建器
├── agent.py                    # LangGraph Agent
├── main.py                     # 主入口
├── demo.py                     # 模拟演示
├── test_skills.py              # 测试脚本
└── requirements.txt            # 依赖
```

## 快速开始

### 1. 安装依赖

```powershell
conda activate ai_agent
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目目录创建 `.env` 文件：

```
DEEP_SEEK_API_KEY=your-api-key
DEEP_SEEK_API_URL=https://api.deepseek.com/v1
```

### 3. 运行

```powershell
# 交互式运行
python main.py

# 运行单元测试
python test_skills.py
```

## 核心功能

### 1. Skill 工具

- `lookup_skill(skill_name)` - 读取指定 skill 的完整内容
- `list_skills()` - 列出所有可用的 skills
- `read_reference(skill_name, reference)` - 读取 skill 引用的文档

### 2. Skill 定义

每个 skill 是一个目录，包含 `SKILL.md` 文件：

```markdown
---
name: skill-name
description: Skill 描述
---

# Skill 名称

## 适用场景

- 场景1
- 场景2

## 命令

- `/command1`: 命令1说明
- `/command2`: 命令2说明

## 使用方法

### 示例1

使用 `/command1` 命令...
```

### 3. 引用文档

在 SKILL.md 中使用 `相对路径` 格式引用其他文档：

```
../docs/git-workflow.md
docs/test_ref.md
```

## 工作流程

```
用户请求 → 初始 System Prompt（含 skill 索引）
         → LLM 识别需要使用的 skill
         → 调用 lookup_skill 工具读取完整内容
         → 按 skill 指令执行并返回结果
```

## 技术栈

- **LangChain** - LLM 应用框架
- **LangGraph** - Agent 工作流编排
- **DeepSeek** - 大语言模型
- **YAML** - Skill 元数据解析

## 与传统方式对比

| 方式 | 初始 Prompt | 按需加载 |
|------|-------------|----------|
| **传统** | 所有 skill 完整内容 | ❌ 无 |
| **渐进式披露** | 仅索引（name + description） | Agent 主动读取 |

## 优势

- **减少 token 消耗**：初始只注入索引
- **按需读取**：Agent 自主决策，灵活高效
- **易于扩展**：新增 skill 只需添加目录和 SKILL.md
- **标准化**：工具调用流程统一
