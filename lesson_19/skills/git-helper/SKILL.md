---
name: git-helper
description: Git 版本控制助手 - 提交、推送、分支管理
---

# Git 助手

这个技能帮助用户处理 Git 版本控制操作。

## 适用场景

- 用户想要提交代码
- 用户想要推送代码到远程
- 用户想要创建或切换分支
- 用户想要查看提交历史

## 命令

- `/git-commit`: 提交更改
- `/git-push`: 推送到远程
- `/git-pull`: 拉取远程更新
- `/git-branch`: 分支管理
- `/git-status`: 查看状态
- `/git-log`: 查看提交历史

## 使用方法

### 提交代码

使用 `/git-commit` 命令：

```
/git-commit -m "提交信息"
```

### 推送代码

使用 `/git-push` 命令：

```
/git-push origin main
```

### 分支操作

```
/git-branch create new-branch
/git-branch checkout existing-branch
```

## 引用文档

更多 Git 最佳实践请参考：

```
../docs/git-workflow.md
```
