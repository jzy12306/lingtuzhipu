from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import uvicorn

from src.api import api_router
from src.services.db_service import db_service
from src.repositories.user_repository import user_repository
from src.models.user import UserCreate


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在初始化应用...")
    
    # 初始化数据库连接
    try:
        await db_service.initialize()
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
    
    # 创建默认管理员用户（如果不存在）
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
        
        # 检查管理员用户是否存在
        existing_admin = await user_repository.find_by_username(admin_username)
        if not existing_admin:
            admin_data = UserCreate(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            await user_repository.create_user(
                admin_data.dict(),
                is_admin=True
            )
            logger.info(f"默认管理员用户 {admin_username} 创建成功")
        else:
            logger.info(f"管理员用户 {admin_username} 已存在")
    except Exception as e:
        logger.error(f"创建默认管理员失败: {str(e)}")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    await db_service.close()
    logger.info("数据库连接已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="智能知识图谱系统 API",
    description="基于大型语言模型的智能知识图谱构建和查询系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部错误"}
    )


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用智能知识图谱系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    # 检查数据库连接状态
    db_status = await db_service.health_check()
    
    return {
        "status": "healthy" if db_status["status"] == "healthy" else "unhealthy",
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
        reload=reload
    )