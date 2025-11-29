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

# 加载.env文件
load_dotenv()

# 使用服务工厂和路由管理器
from src.services.service_factory import ServiceFactory, UserCreate
from src.core.security import get_password_hash
from src.routes.router_manager import router_manager
from src.middleware.rate_limiter import RateLimitMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在初始化应用...")
    
    # 使用服务工厂初始化所有服务
    try:
        await service_factory.initialize_all()
        logger.info("所有服务初始化成功")
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        raise
    
    # 创建默认管理员用户（如果不存在）
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
        
        # 检查管理员用户是否存在
        try:
            existing_admin = await service_factory.user_repository.find_by_username(admin_username)
        except Exception as e:
            logger.error(f"查询管理员用户失败: {str(e)}")
            existing_admin = None
        
        if not existing_admin:
            try:
                # 使用security模块中的get_password_hash函数
                # 现在它使用pbkdf2_sha256算法，没有72字节的限制
                hashed_password = get_password_hash(admin_password)
                
                # 为管理员生成哈希密码并以hashed_password字段保存
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
                # 打印详细的异常信息，帮助调试
                logger.error(f"异常类型: {type(e).__name__}")
                logger.error(f"异常详情: {repr(e)}")
        else:
            logger.info(f"管理员用户 {admin_username} 已存在")
    except Exception as e:
        logger.error(f"创建默认管理员失败: {str(e)}")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    
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
    """API调用统计中间件"""
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
    
    # 记录API调用统计
    try:
        # 构建统计数据
        stats_data = {
            "path": path,
            "method": method,
            "status_code": status_code,
            "process_time": process_time,
            "client_ip": client_ip,
            "timestamp": datetime.utcnow(),
            "date": datetime.utcnow().date()
        }
        
        # 保存到MongoDB
        mongodb = await service_factory.db_service.get_mongodb()
        if mongodb is not None:
            await mongodb.api_stats.insert_one(stats_data)
        
        # 记录日志
        logger.info(f"API调用: {method} {path} {status_code} {process_time:.3f}s {client_ip}")
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
    except Exception as e:
        logger.error(f"记录API统计失败: {str(e)}")
    
    return response

# 添加速率限制中间件
app.add_middleware(RateLimitMiddleware)

# 使用路由管理器注册所有路由
router_manager.register_all_routes()
app.include_router(router_manager.main_router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return {"detail": "服务器内部错误"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用灵图智谱",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
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