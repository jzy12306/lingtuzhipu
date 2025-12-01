from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import uvicorn
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import asyncio
from typing import Optional

# 加载.env文件
load_dotenv()

# 使用服务工厂和路由管理器
from src.services.service_factory import ServiceFactory, UserCreate
from src.core.security import get_password_hash
from src.routes.router_manager import router_manager
from src.middleware.rate_limiter import RateLimitMiddleware
from src.core.performance import initialize_config
from collections import deque

# 初始化服务工厂实例
service_factory = ServiceFactory()

# 配置日志，将级别设置为WARNING，减少不必要的日志输出
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 为应用日志设置INFO级别，确保关键操作仍能被记录
app_logger = logging.getLogger('src')
app_logger.setLevel(logging.INFO)

# 将uvicorn的日志级别设置为WARNING，减少框架日志输出
uvicorn_logger = logging.getLogger('uvicorn')
uvicorn_logger.setLevel(logging.WARNING)
uvicorn_access_logger = logging.getLogger('uvicorn.access')
uvicorn_access_logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# API统计缓存队列
_api_stats_queue: deque = deque()
_stats_queue_lock = asyncio.Lock()
_stats_flush_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _stats_flush_task
    
    # 启动时执行
    logger.info("正在初始化应用...")
    
    # 使用服务工厂初始化所有服务
    try:
        await service_factory.initialize_all()
        logger.info("所有服务初始化成功")
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}", exc_info=True)
        raise
    
    # 从数据库加载配置
    try:
        await initialize_config()
        logger.info("配置初始化成功")
    except Exception as e:
        logger.error(f"配置初始化失败: {str(e)}", exc_info=True)
        raise
    
    # 启动API统计批量写入任务
    try:
        _stats_flush_task = asyncio.create_task(flush_api_stats())
        logger.info("API统计批量写入任务已启动")
    except Exception as e:
        logger.error(f"启动API统计任务失败: {str(e)}", exc_info=True)
        raise
    
    # 创建默认管理员用户（如果不存在）
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        # 如果没有设置管理员密码，跳过创建
        if not admin_password:
            logger.warning("未设置ADMIN_PASSWORD环境变量，跳过默认管理员创建")
        else:
            # 检查管理员用户是否存在
            try:
                existing_admin = await service_factory.user_repository.find_by_username(admin_username)
            except Exception as e:
                logger.error(f"查询管理员用户失败: {str(e)}")
                existing_admin = None
            
            if not existing_admin:
                try:
                    hashed_password = get_password_hash(admin_password)
                    admin_dict = {
                        "username": admin_username,
                        "email": admin_email,
                        "hashed_password": hashed_password,
                        "is_active": True,
                        "is_admin": True,
                        "email_verified": True,
                    }
                    await service_factory.user_repository.create(admin_dict)
                    logger.info(f"默认管理员用户 {admin_username} 创建成功")
                except Exception as e:
                    logger.error(f"创建管理员用户失败: {str(e)}")
            else:
                logger.info(f"管理员用户 {admin_username} 已存在")
    except Exception as e:
        logger.error(f"创建默认管理员失败: {str(e)}")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    
    # 取消API统计任务
    if _stats_flush_task:
        _stats_flush_task.cancel()
        try:
            await _stats_flush_task
        except asyncio.CancelledError:
            pass
        logger.info("API统计批量写入任务已停止")
    
    # 使用服务工厂关闭所有服务
    try:
        await service_factory.shutdown_all()
        logger.info("所有服务已关闭")
    except Exception as e:
        logger.error(f"关闭服务失败: {str(e)}")


# 创建FastAPI应用实例
app = FastAPI(
    title="灵图智谱 API",
    description="基于大型语言模型的灵图智谱构建和查询系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API调用统计中间件
@app.middleware("http")
async def api_stats_middleware(request: Request, call_next):
    """API调用统计中间件（批量优化版）"""
    # 记录请求开始时间
    start_time = time.time()
    
    # 获取请求信息
    path = request.url.path
    method = request.method
    client_ip = request.client.host if request.client else "unknown"
    
    # 执行请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 获取响应状态码
    status_code = response.status_code
    
    # 记录API调用统计到缓存队列
    try:
        # 构建统计数据
        stats_data = {
            "path": path,
            "method": method,
            "status_code": status_code,
            "process_time": process_time,
            "client_ip": client_ip,
            "timestamp": datetime.utcnow(),
            "date": datetime.utcnow().date().isoformat()
        }
        
        # 添加到缓存队列（非阻塞）
        async with _stats_queue_lock:
            _api_stats_queue.append(stats_data)
        
        # 记录日志
        logger.info(f"API调用: {method} {path} {status_code} {process_time:.3f}s {client_ip}")
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
    except Exception as e:
        logger.error(f"记录API统计失败: {str(e)}")
    
    return response

# 批量写入统计数据的异步函数
async def flush_api_stats():
    """定期将缓存的API统计批量写入数据库"""
    while True:
        try:
            await asyncio.sleep(30)  # 每30秒刷新一次
            
            async with _stats_queue_lock:
                if not _api_stats_queue:
                    continue
                
                # 复制队列数据并清空
                stats_batch = list(_api_stats_queue)
                _api_stats_queue.clear()
            
            if stats_batch:
                mongodb = await service_factory.db_service.get_mongodb()
                if mongodb is not None:
                    await mongodb.api_stats.insert_many(stats_batch)
                    logger.info(f"批量写入 {len(stats_batch)} 条API统计记录")
                    
        except Exception as e:
            logger.error(f"批量写入API统计失败: {str(e)}")


# 添加速率限制中间件
app.add_middleware(RateLimitMiddleware)

# 使用路由管理器注册所有路由
router_manager.register_all_routes()
app.include_router(router_manager.main_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    
    # 根据不同异常类型返回不同的状态码
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_type": "ValueError"}
        )
    elif isinstance(exc, KeyError):
        return JSONResponse(
            status_code=400,
            content={"detail": "请求数据不完整", "error_type": "KeyError"}
        )
    elif isinstance(exc, PermissionError):
        return JSONResponse(
            status_code=403,
            content={"detail": "权限不足", "error_type": "PermissionError"}
        )
    else:
        # 对于未预见的异常，返回500错误
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误", 
                "error_type": type(exc).__name__,
                "message": str(exc) if os.getenv("DEBUG") else "请联系管理员"
            }
        )


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用灵图智谱",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/routes")
async def get_routes():
    """获取所有注册的路由信息"""
    return {
        "routes": router_manager.get_routes_info()
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    # 使用服务工厂获取数据库服务进行健康检查
    db_status = await service_factory.db_service.get_stats()
    
    return {
        "status": "healthy" if db_status.get("healthy") else "unhealthy",
        "database": db_status
    }

@app.get("/api/stats")
async def get_api_stats(start_date: datetime = None, end_date: datetime = None, path: str = None):
    """获取API调用统计"""
    try:
        mongodb = await service_factory.db_service.get_mongodb()
        if mongodb is None:
            return {"success": False, "error": "数据库连接失败"}
        
        # 构建查询条件
        query = {}
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" not in query:
                query["timestamp"] = {}
            query["timestamp"]["$lte"] = end_date
        if path:
            query["path"] = path
        
        # 统计总调用次数
        total_calls = await mongodb.api_stats.count_documents(query)
        
        # 按路径统计
        path_stats = []
        async for stat in mongodb.api_stats.aggregate([
            {"$match": query},
            {"$group": {
                "_id": "$path",
                "count": {"$sum": 1},
                "avg_process_time": {"$avg": "$process_time"},
                "max_process_time": {"$max": "$process_time"},
                "min_process_time": {"$min": "$process_time"}
            }},
            {"$sort": {"count": -1}}
        ]):
            path_stats.append({
                "path": stat["_id"],
                "count": stat["count"],
                "avg_process_time": stat["avg_process_time"],
                "max_process_time": stat["max_process_time"],
                "min_process_time": stat["min_process_time"]
            })
        
        # 按状态码统计
        status_stats = []
        async for stat in mongodb.api_stats.aggregate([
            {"$match": query},
            {"$group": {
                "_id": "$status_code",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]):
            status_stats.append({
                "status_code": stat["_id"],
                "count": stat["count"]
            })
        
        return {
            "success": True,
            "total_calls": total_calls,
            "path_stats": path_stats,
            "status_stats": status_stats,
            "start_date": start_date,
            "end_date": end_date
        }
    except Exception as e:
        logger.error(f"获取API统计失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"启动服务器，监听 {host}:{port}")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )