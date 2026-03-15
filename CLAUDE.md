# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Agent learning demo library from the WeChat series "春哥的AI Agent通关秘籍". It contains progressive lessons covering AI Agent development concepts including function calling, ReAct pattern, RAG, memory systems, and LangGraph.

## Environment Setup

- **Python**: Miniconda environment at `D:\miniconda\envs\ai_agent\python.exe`
- **Environment Variables**: Required in `.env` file:
  ```
  DEEP_SEEK_API_KEY = sk-xxxxx
  DEEP_SEEK_API_URL = https://api.deepseek.com
  ```

## Common Commands

Run any lesson script directly:
```bash
python .\lesson_XX\lesson_XX_xxx.py
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Architecture

### Progressive Disclosure System (lesson_19)

The main architecture is a **skills progressive disclosure system** built with LangGraph:

- **`agent.py`**: Creates ReAct agent using `langgraph.prebuilt.create_react_agent`, connects to DeepSeek API
- **`skill_tools.py`**: Defines LangChain tools - `lookup_skill`, `list_skills`, `read_reference`
- **`skill_loader.py`**: Loads skills from `./skills` directory, parses YAML frontmatter from SKILL.md files
- **`prompt_builder.py`**: Builds system prompt with skill index for progressive disclosure

Skills are stored in `./skills/<skill-name>/SKILL.md` with YAML frontmatter containing `name` and `description`.

### Key Dependencies

- `langchain` / `langgraph`: Agent framework
- `langchain-openai`: LLM interface (DeepSeek compatible)
- `chromadb` / `qdrant-client`: Vector databases for RAG
- `mem0ai`: Memory system for agents

## Project Structure

```
├── lesson_02/          # Environment setup
├── lesson_04/          # Structured output
├── lesson_06/          # ReAct pattern, file organizer
├── lesson_09/          # Text splitting, RAG
├── lesson_14/          # LangChain basics
├── lesson_16/          # Memory systems
├── lesson_19/          # Skills progressive disclosure (main)
├── lesson_20/         # mem0ai integration
├── skills/             # Skill definitions for lesson_19
├── chroma_db/          # ChromaDB data (generated)
└── .env                # API keys (not committed)
```
