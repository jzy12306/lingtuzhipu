# Neo4j 国内安装指南

## 🚫 问题说明
Neo4j官网在国内可能无法访问，本指南提供国内可用的安装方法。

## ✅ 推荐方案：使用Docker（最简单）

### 方案1：Docker Hub镜像（推荐 ⭐）

#### 步骤1：安装Docker Desktop

**下载地址**（国内可访问）：
- 官方：https://www.docker.com/products/docker-desktop/
- 阿里云镜像：https://mirrors.aliyun.com/docker-toolbox/windows/docker-desktop/

#### 步骤2：配置Docker国内镜像加速

创建或编辑文件：`C:\Users\你的用户名\.docker\daemon.json`

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

重启Docker Desktop使配置生效。

#### 步骤3：拉取Neo4j镜像

打开PowerShell或CMD：

```bash
# 拉取Neo4j镜像（使用国内镜像加速）
docker pull neo4j:latest

# 如果上面的命令很慢，尝试使用阿里云镜像
docker pull registry.cn-hangzhou.aliyuncs.com/library/neo4j:latest
```

#### 步骤4：启动Neo4j容器

```bash
docker run -d ^
  --name lingtu_neo4j ^
  -p 7474:7474 ^
  -p 7687:7687 ^
  -e NEO4J_AUTH=neo4j/password ^
  -e NEO4J_dbms_memory_pagecache_size=512M ^
  -e NEO4J_dbms_memory_heap_max__size=1G ^
  -v neo4j_data:/data ^
  -v neo4j_logs:/logs ^
  neo4j:latest
```

**注意**：Windows CMD使用 `^` 作为换行符，PowerShell使用 `` ` ``

**PowerShell版本**：
```powershell
docker run -d `
  --name lingtu_neo4j `
  -p 7474:7474 `
  -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/password `
  -e NEO4J_dbms_memory_pagecache_size=512M `
  -e NEO4J_dbms_memory_heap_max__size=1G `
  -v neo4j_data:/data `
  -v neo4j_logs:/logs `
  neo4j:latest
```

#### 步骤5：验证安装

等待30秒后，访问：http://localhost:7474

- 用户名：`neo4j`
- 密码：`password`

### 方案2：使用Docker Compose（一键启动所有服务）

#### 创建 docker-compose.yml

在项目根目录创建文件：

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    container_name: lingtu_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_dbms_memory_pagecache_size=512M
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: lingtu_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  mongodb:
    image: mongo:latest
    container_name: lingtu_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  redis_data:
  mongodb_data:
```

#### 启动所有服务

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f neo4j

# 停止
docker-compose down
```

## 🔧 方案3：本地安装（不推荐，但可用）

### 使用国内镜像下载

#### 清华大学镜像站
```
https://mirrors.tuna.tsinghua.edu.cn/
```

#### 中科大镜像站
```
https://mirrors.ustc.edu.cn/
```

### 下载Neo4j Community Edition

1. 访问清华镜像站或中科大镜像站
2. 搜索 "neo4j"
3. 下载 Windows版本的zip包

### 手动安装步骤

1. **解压文件**
   ```
   解压到：C:\neo4j
   ```

2. **配置环境变量**
   - 添加到PATH：`C:\neo4j\bin`

3. **修改配置文件**
   
   编辑 `C:\neo4j\conf\neo4j.conf`：
   ```
   # 取消注释并修改
   dbms.default_listen_address=0.0.0.0
   dbms.connector.bolt.listen_address=:7687
   dbms.connector.http.listen_address=:7474
   
   # 设置初始密码
   dbms.security.auth_enabled=true
   ```

4. **启动Neo4j**
   ```bash
   cd C:\neo4j\bin
   neo4j.bat console
   ```

## 📦 方案4：使用便携版（最快）

### 下载便携版Neo4j

创建启动脚本 `start_neo4j.bat`：

```batch
@echo off
echo 正在启动Neo4j...

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

REM 检查容器是否存在
docker ps -a | findstr lingtu_neo4j >nul 2>&1
if %errorlevel% equ 0 (
    echo Neo4j容器已存在，正在启动...
    docker start lingtu_neo4j
) else (
    echo 创建并启动Neo4j容器...
    docker run -d ^
      --name lingtu_neo4j ^
      -p 7474:7474 ^
      -p 7687:7687 ^
      -e NEO4J_AUTH=neo4j/password ^
      -e NEO4J_dbms_memory_pagecache_size=512M ^
      -e NEO4J_dbms_memory_heap_max__size=1G ^
      -v neo4j_data:/data ^
      neo4j:latest
)

echo.
echo Neo4j启动成功！
echo 浏览器访问: http://localhost:7474
echo 用户名: neo4j
echo 密码: password
echo.
echo 按任意键继续...
pause >nul
```

双击运行 `start_neo4j.bat` 即可启动。

## ✅ 验证安装

### 1. 检查Docker容器状态

```bash
docker ps
```

应该看到：
```
CONTAINER ID   IMAGE          STATUS         PORTS
xxxxx          neo4j:latest   Up 2 minutes   0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
```

### 2. 访问Neo4j浏览器

打开浏览器访问：http://localhost:7474

### 3. 登录

- 用户名：`neo4j`
- 密码：`password`

首次登录会要求修改密码，可以保持为 `password` 或改为其他密码。

### 4. 测试连接

在Neo4j浏览器中执行：

```cypher
RETURN "Hello Neo4j!" AS message
```

如果看到结果，说明安装成功！

## 🎯 添加测试数据

在Neo4j浏览器中执行以下Cypher语句：

```cypher
// 清空现有数据（可选）
MATCH (n) DETACH DELETE n;

// 创建网易公司
CREATE (netease:Company {
  name: '网易公司',
  englishName: 'NetEase',
  founded: '1997年6月',
  founder: '丁磊',
  headquarters: '中国杭州',
  industry: '互联网',
  stockCode: 'NTES',
  employees: '30000+',
  description: '网易是中国领先的互联网技术公司，在开发互联网应用、服务及其它技术方面处于业界领先地位。'
});

// 创建丁磊
CREATE (ding:Person {
  name: '丁磊',
  englishName: 'William Ding',
  birthYear: '1971年',
  birthPlace: '浙江宁波',
  education: '电子科技大学',
  position: '创始人兼CEO',
  wealth: '福布斯中国富豪榜前列'
});

// 创建产品
CREATE (cloudMusic:Product {
  name: '网易云音乐',
  category: '音乐流媒体',
  launchYear: '2013年',
  users: '8亿+'
});

CREATE (game:Product {
  name: '网易游戏',
  category: '游戏',
  products: '梦幻西游、大话西游、阴阳师等'
});

CREATE (email:Product {
  name: '网易邮箱',
  category: '电子邮件',
  launchYear: '1997年',
  users: '数亿'
});

CREATE (youdao:Product {
  name: '有道词典',
  category: '教育工具',
  users: '8亿+'
});

// 创建关系
MATCH (ding:Person {name: '丁磊'})
MATCH (netease:Company {name: '网易公司'})
CREATE (ding)-[:FOUNDED {year: '1997年'}]->(netease)
CREATE (ding)-[:CEO_OF]->(netease);

MATCH (netease:Company {name: '网易公司'})
MATCH (cloudMusic:Product {name: '网易云音乐'})
MATCH (game:Product {name: '网易游戏'})
MATCH (email:Product {name: '网易邮箱'})
MATCH (youdao:Product {name: '有道词典'})
CREATE (netease)-[:OWNS]->(cloudMusic)
CREATE (netease)-[:OWNS]->(game)
CREATE (netease)-[:OWNS]->(email)
CREATE (netease)-[:OWNS]->(youdao);

// 验证数据
MATCH (n) RETURN n LIMIT 25;
```

## 🔧 常用Docker命令

```bash
# 查看运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 启动容器
docker start lingtu_neo4j

# 停止容器
docker stop lingtu_neo4j

# 重启容器
docker restart lingtu_neo4j

# 查看容器日志
docker logs lingtu_neo4j

# 实时查看日志
docker logs -f lingtu_neo4j

# 进入容器
docker exec -it lingtu_neo4j bash

# 删除容器
docker rm lingtu_neo4j

# 删除镜像
docker rmi neo4j:latest
```

## 📝 配置后端连接

创建或更新 `backend/.env` 文件：

```env
# Neo4j配置
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# MongoDB配置
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=knowledge_graph

# Redis配置
REDIS_URL=redis://localhost:6379/0
```

## 🚀 启动完整系统

### 1. 启动数据库（Docker Compose）

```bash
docker-compose up -d
```

### 2. 启动后端

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 打开前端

直接在浏览器中打开 `frontend/query.html`

### 4. 测试查询

输入："给我介绍一下网易公司"

应该能看到从Neo4j查询到的结果！

## ❓ 故障排查

### 问题1：Docker拉取镜像很慢

**解决方案**：使用国内镜像加速器（见上文配置）

### 问题2：端口被占用

```bash
# 检查端口占用
netstat -ano | findstr :7687
netstat -ano | findstr :7474

# 修改端口映射
docker run -d --name lingtu_neo4j -p 17474:7474 -p 17687:7687 ...
```

### 问题3：容器启动失败

```bash
# 查看详细日志
docker logs lingtu_neo4j

# 删除并重新创建
docker rm -f lingtu_neo4j
# 然后重新运行docker run命令
```

### 问题4：内存不足

减少内存配置：
```bash
-e NEO4J_dbms_memory_pagecache_size=256M
-e NEO4J_dbms_memory_heap_max__size=512M
```

## 🎉 完成！

现在您应该有一个完全运行的Neo4j数据库，可以支持知识图谱查询功能了！
