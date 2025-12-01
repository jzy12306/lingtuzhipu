@echo off
chcp 65001 >nul
title 灵图智谱 - 一键部署系统
color 0A

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              灵图智谱 - 一键部署系统                      ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ============================================================
REM 第1步：检查Docker Desktop是否运行
REM ============================================================
echo [1/7] 检查Docker Desktop状态...
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Docker Desktop运行正常
    goto :docker_ready
)

echo [!] Docker Desktop未运行
echo.
echo 正在尝试启动Docker Desktop...

REM 尝试启动Docker Desktop
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo 等待Docker Desktop启动（这可能需要30-60秒）...
echo 提示：您可以在任务栏看到Docker图标变为绿色时表示启动完成
echo.

REM 等待Docker启动，最多等待120秒
set /a count=0
:wait_docker
timeout /t 5 /nobreak >nul
set /a count+=5

docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Docker Desktop启动成功！
    goto :docker_ready
)

if %count% lss 120 (
    echo 等待中... (%count%/120秒)
    goto :wait_docker
)

echo.
echo [✗] Docker Desktop启动超时
echo.
echo 请手动执行以下操作：
echo 1. 在开始菜单搜索并打开 "Docker Desktop"
echo 2. 等待Docker图标变为绿色
echo 3. 重新运行此脚本
echo.
pause
exit /b 1

:docker_ready
echo.

REM ============================================================
REM 第2步：检查docker-compose.yml文件
REM ============================================================
echo [2/7] 检查配置文件...
if not exist "docker-compose.yml" (
    echo [✗] 找不到 docker-compose.yml 文件
    echo.
    echo 请确保在项目根目录运行此脚本
    echo.
    pause
    exit /b 1
)
echo [✓] 配置文件存在
echo.

REM ============================================================
REM 第3步：拉取Docker镜像
REM ============================================================
echo [3/7] 检查并拉取Docker镜像...
echo.
echo 正在检查镜像...

docker images neo4j:latest -q >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Neo4j镜像不存在，正在下载...
    echo 提示：首次下载可能需要几分钟，请耐心等待
    docker pull neo4j:latest
    if %errorlevel% neq 0 (
        echo [✗] Neo4j镜像下载失败
        echo.
        echo 可能的原因：
        echo 1. 网络连接问题
        echo 2. Docker Hub访问受限
        echo.
        echo 建议：配置Docker镜像加速器（参考 Docker部署完整指南.md）
        echo.
        pause
        exit /b 1
    )
) else (
    echo [✓] Neo4j镜像已存在
)

docker images mongo:latest -q >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] MongoDB镜像不存在，正在下载...
    docker pull mongo:latest
) else (
    echo [✓] MongoDB镜像已存在
)

docker images redis:alpine -q >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Redis镜像不存在，正在下载...
    docker pull redis:alpine
) else (
    echo [✓] Redis镜像已存在
)

echo.
echo [✓] 所有镜像准备完成
echo.

REM ============================================================
REM 第4步：停止旧容器（如果存在）
REM ============================================================
echo [4/7] 清理旧容器...
docker-compose down >nul 2>&1
echo [✓] 清理完成
echo.

REM ============================================================
REM 第5步：启动所有服务
REM ============================================================
echo [5/7] 启动数据库服务...
echo.
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo [✗] 服务启动失败
    echo.
    echo 请检查：
    echo 1. 端口是否被占用（7474, 7687, 27017, 6379）
    echo 2. 磁盘空间是否充足
    echo 3. 查看详细日志：docker-compose logs
    echo.
    pause
    exit /b 1
)

echo.
echo [✓] 服务启动成功
echo.

REM ============================================================
REM 第6步：等待服务就绪
REM ============================================================
echo [6/7] 等待服务完全启动...
echo.
echo 正在等待Neo4j启动（约30秒）...

set /a wait_count=0
:wait_neo4j
timeout /t 3 /nobreak >nul
set /a wait_count+=3

REM 检查Neo4j是否就绪
curl -s http://localhost:7474 >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Neo4j已就绪
    goto :services_ready
)

if %wait_count% lss 60 (
    echo 等待中... (%wait_count%/60秒)
    goto :wait_neo4j
)

echo [!] Neo4j启动时间较长，但服务可能已经可用
echo.

:services_ready
echo.

REM ============================================================
REM 第7步：显示服务状态
REM ============================================================
echo [7/7] 检查服务状态...
echo.
docker-compose ps
echo.

REM ============================================================
REM 显示部署结果
REM ============================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║                  🎉 部署完成！                            ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📊 服务访问地址：
echo    ├─ Neo4j浏览器: http://localhost:7474
echo    ├─ 后端API: http://localhost:8000 (需要手动启动)
echo    └─ API文档: http://localhost:8000/docs
echo.
echo 🔑 Neo4j登录信息：
echo    ├─ 用户名: neo4j
echo    └─ 密码: password
echo.
echo 📝 下一步操作：
echo.
echo    1. 访问 Neo4j浏览器添加测试数据
echo       http://localhost:7474
echo.
echo    2. 在Neo4j浏览器中执行以下Cypher语句：
echo       CREATE (n:Company {name: '网易公司', founder: '丁磊'})
echo       CREATE (p:Person {name: '丁磊'})
echo       MATCH (p:Person), (c:Company) CREATE (p)-[:FOUNDED]-^>(c)
echo.
echo    3. 启动后端服务（在新窗口中）：
echo       cd backend
echo       uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo    4. 打开前端页面测试查询功能
echo       frontend\query.html
echo.
echo 💡 常用命令：
echo    ├─ 查看日志: docker-compose logs -f
echo    ├─ 停止服务: docker-compose down
echo    ├─ 重启服务: docker-compose restart
echo    └─ 查看状态: docker-compose ps
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM 询问是否打开Neo4j浏览器
set /p open_browser="是否现在打开Neo4j浏览器？(Y/N): "
if /i "%open_browser%"=="Y" (
    start http://localhost:7474
    echo.
    echo 已打开Neo4j浏览器
)

echo.
echo 按任意键退出...
pause >nul
