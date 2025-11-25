from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
import logging

from core.security import get_current_user, get_current_active_user
from schemas.user import User
from routes import auth, documents, knowledge, health, analyst

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
            
            # 注册各模块路由到API路由
            self._register_auth_routes()
            self._register_document_routes()
            self._register_knowledge_routes()
            self._register_health_routes()
            self._register_analyst_routes()
            
            # 将API路由注册到主路由
            self.main_router.include_router(self.api_router)
            
            logger.info("所有API路由注册完成")
            
        except Exception as e:
            logger.error(f"路由注册失败: {str(e)}")
            raise
    
    def _register_auth_routes(self):
        """注册认证相关路由"""
        try:
            # 从auth模块导入路由并注册
            self.api_router.include_router(self.auth_router)
            
            # 注册具体的认证端点
            self.auth_router.include_router(auth.router)
            
            logger.info("认证路由注册完成")
            
        except Exception as e:
            logger.error(f"认证路由注册失败: {str(e)}")
            raise
    
    def _register_document_routes(self):
        """注册文档相关路由"""
        try:
            # 应用认证依赖
            document_router = APIRouter()
            document_router.include_router(documents.router)
            
            # 注册文档路由到API路由
            self.api_router.include_router(
                self.documents_router,
                dependencies=[Depends(get_current_active_user)]
            )
            
            # 将文档模块路由注册到文档路由
            self.documents_router.include_router(document_router)
            
            logger.info("文档路由注册完成")
            
        except Exception as e:
            logger.error(f"文档路由注册失败: {str(e)}")
            raise
    
    def _register_knowledge_routes(self):
        """注册知识图谱相关路由"""
        try:
            # 应用认证依赖
            knowledge_router = APIRouter()
            knowledge_router.include_router(knowledge.router)
            
            # 注册知识图谱路由到API路由
            self.api_router.include_router(
                self.knowledge_router,
                dependencies=[Depends(get_current_active_user)]
            )
            
            # 将知识图谱模块路由注册到知识图谱路由
            self.knowledge_router.include_router(knowledge_router)
            
            logger.info("知识图谱路由注册完成")
            
        except Exception as e:
            logger.error(f"知识图谱路由注册失败: {str(e)}")
            raise
    
    def _register_health_routes(self):
        """注册健康检查相关路由"""
        try:
            # 从health模块导入路由并注册
            self.api_router.include_router(self.health_router)
            self.health_router.include_router(health.router)
            
            logger.info("健康检查路由注册完成")
            
        except Exception as e:
            logger.error(f"健康检查路由注册失败: {str(e)}")
            raise
    
    def _register_analyst_routes(self):
        """注册分析师相关路由"""
        try:
            # 应用认证依赖
            analyst_router = APIRouter()
            analyst_router.include_router(analyst.router)
            
            # 注册分析师路由到API路由
            self.api_router.include_router(
                self.analyst_router,
                dependencies=[Depends(get_current_active_user)]
            )
            
            # 将分析师模块路由注册到分析师路由
            self.analyst_router.include_router(analyst_router)
            
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