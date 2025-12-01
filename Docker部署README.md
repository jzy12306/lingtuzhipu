# 🚀 灵图智谱 - Docker 部署指南

## 📋 快速开始（3步完成部署）

### 第1步：启动Docker Desktop

确保Docker Desktop正在运行（任务栏图标为绿色）

### 第2步：一键部署

双击运行：**`一键部署.bat`**

这个脚本会自动：
- ✅ 检测并启动Docker Desktop
- ✅ 拉取所需的Docker镜像
- ✅ 启动Neo4j、MongoDB、Redis服务
- ✅ 验证服务状态

### 第3步：添加测试数据

1. 访问：http://localhost:7474
2. 登录（用户名：`neo4j`，密码：`password`）
3. 复制 `添加测试数据.cypher` 文件内容并执行

## 📁 文件说明

| 文件名 | 说明 |
|--------|------|
| `一键部署.bat` | 🌟 **推荐使用** - 自动化部署脚本 |
| `docker-compose.yml` | Docker服务编排配置 |
| `测试部署.bat` | 检查部署状态和服务健康 |
| `添加测试数据.cypher` | Neo4j测试数据脚本 |
| `Docker部署完整指南.md` | 详细的部署文档 |
| `启动所有服务.bat` | 快速启动所有服务 |
| `start_neo4j.bat` | 单独启动Neo4j |

## 🎯 部署后的服务

| 服务 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| Neo4j浏览器 | http://localhost:7474 | neo4j | password |
| Neo4j Bolt | bolt://localhost:7687 | neo4j | password |
| MongoDB | mongodb://localhost:27017 | - | - |
| Redis | redis://localhost:6379 | - | - |

## 🔧 常用命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f neo4j
```

### 启动/停止服务
```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart
```

### 进入容器
```bash
# 进入Neo4j
docker exec -it lingtu_neo4j bash

# 进入MongoDB
docker exec -it lingtu_mongodb bash

# 进入Redis
docker exec -it lingtu_redis sh
```

## 📊 验证部署

### 方法1：使用测试脚本

双击运行：**`测试部署.bat`**

### 方法2：手动验证

1. **检查容器状态**
   ```bash
   docker ps
   ```
   应该看到3个运行中的容器

2. **访问Neo4j浏览器**
   
   打开：http://localhost:7474
   
   执行测试查询：
   ```cypher
   RETURN "Hello Neo4j!" AS message
   ```

3. **测试MongoDB**
   ```bash
   docker exec lingtu_mongodb mongosh --eval "db.adminCommand('ping')"
   ```

4. **测试Redis**
   ```bash
   docker exec lingtu_redis redis-cli ping
   ```

## 🚀 启动后端服务

数据库部署完成后，启动后端：

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

应该看到：
```
✅ MongoDB连接成功
✅ Neo4j连接成功
✅ 所有服务初始化成功
```

## 🧪 测试完整功能

### 1. 测试查询功能

1. 打开 `frontend/query.html`
2. 输入："给我介绍一下网易公司"
3. 点击查询
4. 应该能看到从Neo4j查询到的结果

### 2. 测试文档上传

1. 打开 `frontend/index.html`
2. 上传一个文档
3. 查看处理进度和结果

## ❓ 常见问题

### Q1: Docker Desktop启动失败

**解决方案**：
1. 以管理员身份运行Docker Desktop
2. 检查Windows版本（需要Windows 10 1903+）
3. 启用Hyper-V和WSL 2
4. 重启电脑

### Q2: 端口被占用

**错误信息**：
```
Error: bind: address already in use
```

**解决方案**：

查看端口占用：
```bash
netstat -ano | findstr :7474
netstat -ano | findstr :7687
```

关闭占用端口的程序或修改 `docker-compose.yml` 中的端口映射。

### Q3: 镜像下载很慢

**解决方案**：

配置Docker镜像加速器：

1. 打开Docker Desktop设置
2. 选择 "Docker Engine"
3. 添加配置：
   ```json
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com"
     ]
   }
   ```
4. 点击 "Apply & Restart"

### Q4: 容器启动失败

**查看日志**：
```bash
docker-compose logs neo4j
```

**常见原因**：
- 内存不足
- 磁盘空间不足
- 配置错误

**解决方案**：
```bash
# 清理并重新启动
docker-compose down
docker-compose up -d
```

### Q5: Neo4j连接超时

**解决方案**：
1. 等待更长时间（首次启动需要1-2分钟）
2. 检查防火墙设置
3. 重启容器：
   ```bash
   docker-compose restart neo4j
   ```

## 🔄 数据备份与恢复

### 备份数据

```bash
# 备份Neo4j
docker exec lingtu_neo4j neo4j-admin dump --to=/data/backup.dump

# 备份MongoDB
docker exec lingtu_mongodb mongodump --out=/data/backup

# 复制备份文件到本地
docker cp lingtu_neo4j:/data/backup.dump ./backup/
docker cp lingtu_mongodb:/data/backup ./backup/mongodb/
```

### 恢复数据

```bash
# 恢复Neo4j
docker exec lingtu_neo4j neo4j-admin load --from=/data/backup.dump --force

# 恢复MongoDB
docker exec lingtu_mongodb mongorestore /data/backup
```

## 🧹 清理和重置

### 停止并删除容器
```bash
docker-compose down
```

### 删除容器和数据卷（⚠️ 会删除所有数据）
```bash
docker-compose down -v
```

### 清理未使用的镜像
```bash
docker image prune -a
```

### 完全清理Docker
```bash
docker system prune -a --volumes
```

## 📈 性能优化

### 调整内存限制

编辑 `docker-compose.yml`：

```yaml
neo4j:
  environment:
    # 根据您的机器配置调整
    - NEO4J_dbms_memory_pagecache_size=1G
    - NEO4J_dbms_memory_heap_max__size=2G
```

### 限制容器资源

```yaml
neo4j:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## 🎓 学习资源

### Neo4j
- 官方文档：https://neo4j.com/docs/
- Cypher查询语言：https://neo4j.com/docs/cypher-manual/

### Docker
- 官方文档：https://docs.docker.com/
- Docker Compose：https://docs.docker.com/compose/

### MongoDB
- 官方文档：https://docs.mongodb.com/

## 🆘 获取帮助

如果遇到问题：

1. **查看日志**
   ```bash
   docker-compose logs -f
   ```

2. **检查容器状态**
   ```bash
   docker-compose ps
   ```

3. **运行测试脚本**
   ```bash
   测试部署.bat
   ```

4. **查看详细文档**
   - `Docker部署完整指南.md`
   - `Neo4j国内安装指南.md`

## 📝 下一步

部署完成后：

1. ✅ 添加测试数据到Neo4j
2. ✅ 启动后端服务
3. ✅ 测试查询功能
4. ✅ 测试文档上传功能
5. ✅ 开始使用系统！

---

**祝您使用愉快！** 🎉
