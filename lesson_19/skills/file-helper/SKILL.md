---
name: file-helper
description: 文件操作助手 - 读取、写入、复制、移动文件
---

# 技能 1: 文件操作助手

## 概述

这个技能帮助用户进行文件操作，包括读取、写入、复制、移动等。

## 适用场景

- 用户想要读取文件内容
- 用户想要写入或修改文件
- 用户想要复制或移动文件

## 命令

- `/read`: 读取文件内容
- `/write`: 写入文件内容
- `/copy`: 复制文件
- `/move`: 移动文件
- `/delete`: 删除文件

## 使用方法

### 读取文件

使用 `/read` 命令，指定文件路径：

```
/read path/to/file.txt
```

### 写入文件

使用 `/write` 命令，指定文件路径和内容：

```
/write path/to/file.txt "要写入的内容"
```

### 引用其他文档

你可以使用相对路径引用 skills 目录下的其他文档：

```
../docs/coding-standards.md
```

### 执行命令

你可以执行 shell 命令：

```
!ls -la
!cat file.txt
```
