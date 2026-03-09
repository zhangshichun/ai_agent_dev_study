---
name: docker-helper
description: Docker 容器管理 - 构建镜像、运行容器、查看日志
---

# Docker 助手

这个技能帮助用户处理 Docker 容器操作。

## 适用场景

- 用户想要构建 Docker 镜像
- 用户想要运行 Docker 容器
- 用户想要查看容器状态或日志

## 命令

- `/docker-build`: 构建镜像
- `/docker-run`: 运行容器
- `/docker-ps`: 查看运行中的容器
- `/docker-logs`: 查看容器日志
- `/docker-stop`: 停止容器

## 使用方法

### 构建镜像

```bash
/docker-build -t myimage:latest -f Dockerfile .
```

### 运行容器

```bash
/docker-run -d --name mycontainer myimage:latest
```

### 查看日志

```bash
/docker-logs mycontainer
```

## 注意事项

- 需要 Docker daemon 运行
- 确保有足够的磁盘空间
