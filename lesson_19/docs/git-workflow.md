# Git 工作流最佳实践

## 分支策略

- `main`: 生产分支，只接受合并
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

## 提交规范

使用 conventional commits：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
```

## Code Review 要点

1. 代码逻辑是否正确
2. 是否有单元测试
3. 命名是否清晰
4. 是否有注释
5. 性能是否达标
