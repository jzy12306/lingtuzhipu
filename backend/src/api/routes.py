from fastapi import APIRouter

from src.api.routes import auth, users, documents, knowledge, agents

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档处理"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识图谱"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体管理"])