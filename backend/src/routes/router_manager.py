from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
import logging

from src.core.security import get_current_user, get_current_active_user
from src.schemas.user import User
from src.routes import auth, documents, knowledge, health, analyst

logger = logging.getLogger(__name__)


class RouterManager:
    """路由管理器，统一注册和管理所有API路由"""
    
    def __init__(self):
        # 创建主路由
        self.main_router = APIRouter()
        # 创建各功能模块路由
        self.api_router = APIRouter(prefix="/api")
        self.auth_router = APIRouter(prefix="/auth", tags=["authentication"])
        self.documents_router = APIRouter(prefix="/documents", tags=["documents"])
        self.knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])
        self.health_router = APIRouter(prefix="/health", tags=["health"])
        self.analyst_router = APIRouter(prefix="/analyst", tags=["analyst"])
    
    def register_all_routes(self):
        """注册所有路由"""
        try:
            logger.info("开始注册API路由...")
            
            # 注册各模块路由到主路由
            self._register_auth_routes()
            self._register_document_routes()
            self._register_knowledge_routes()
            self._register_health_routes()
            self._register_analyst_routes()
            
            logger.info("所有API路由注册完成")
            
        except Exception as e:
            logger.error(f"路由注册失败: {str(e)}")
            raise
    
    def _register_auth_routes(self):
        """注册认证相关路由"""
        try:
            # 直接注册auth模块的路由（auth.router已经包含了/api/auth前缀）
            self.main_router.include_router(auth.router)
            
            logger.info("认证路由注册完成")
            
        except Exception as e:
            logger.error(f"认证路由注册失败: {str(e)}")
            raise
    
    def _register_document_routes(self):
        """注册文档相关路由"""
        try:
            # 直接注册documents模块的路由（documents.router已经包含了/api/documents前缀）
            # 并应用认证依赖
            self.main_router.include_router(
                documents.router,
                dependencies=[Depends(get_current_active_user)]
            )
            
            logger.info("文档路由注册完成")
            
        except Exception as e:
            logger.error(f"文档路由注册失败: {str(e)}")
            raise
    
    def _register_knowledge_routes(self):
        """注册知识图谱相关路由"""
        try:
            # 直接注册knowledge模块的路由（knowledge.router已经包含了/api/knowledge前缀）
            # 并应用认证依赖
            self.main_router.include_router(
                knowledge.router,
                dependencies=[Depends(get_current_active_user)]
            )
            
            logger.info("知识图谱路由注册完成")
            
        except Exception as e:
            logger.error(f"知识图谱路由注册失败: {str(e)}")
            raise
    
    def _register_health_routes(self):
        """注册健康检查相关路由"""
        try:
            # 注册health模块的路由，添加/api/health前缀
            self.main_router.include_router(
                health.router,
                prefix="/api/health",
                tags=["health"]
            )
            
            logger.info("健康检查路由注册完成")
            
        except Exception as e:
            logger.error(f"健康检查路由注册失败: {str(e)}")
            raise
    
    def _register_analyst_routes(self):
        """注册分析师相关路由"""
        try:
            # 注册analyst模块的路由，添加/api/analyst前缀并应用认证依赖
            self.main_router.include_router(
                analyst.router,
                prefix="/api/analyst",
                tags=["analyst"],
                dependencies=[Depends(get_current_active_user)]
            )
            
            logger.info("分析师路由注册完成")
            
        except Exception as e:
            logger.error(f"分析师路由注册失败: {str(e)}")
            raise
    
    def get_routes_info(self) -> List[Dict[str, any]]:
        """获取所有路由信息"""
        routes_info = []
        
        def _extract_routes(router: APIRouter, prefix: str = ""):
            """递归提取路由信息"""
            for route in router.routes:
                if hasattr(route, "path"):
                    route_path = prefix + route.path
                    methods = getattr(route, "methods", set())
                    tags = getattr(route, "tags", [])
                    
                    routes_info.append({
                        "path": route_path,
                        "methods": list(methods),
                        "tags": tags
                    })
                
                # 处理子路由
                if hasattr(route, "include_in_schema") and route.include_in_schema:
                    for child_router in getattr(router, "routes", []):
                        if hasattr(child_router, "routes"):
                            _extract_routes(child_router, prefix + route.path)
        
        _extract_routes(self.main_router)
        return routes_info


# 创建全局路由管理器实例
router_manager = RouterManager()