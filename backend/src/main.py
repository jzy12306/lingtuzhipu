from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import uvicorn
import sys
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
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