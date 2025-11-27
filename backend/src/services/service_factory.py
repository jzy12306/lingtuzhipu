import logging
from typing import Optional
from contextlib import asynccontextmanager

from src.services.db_service import DatabaseService
from src.services.llm_service import LLMService
from src.services.document_service import DocumentService
from src.services.knowledge_graph_service import KnowledgeGraphService
from src.services.ocr_service import OCRService
from src.repositories.user_repository import UserRepository
from src.repositories.document_repository import DocumentRepository
from src.repositories.knowledge_repository import KnowledgeRepository
from src.repositories.query_history_repository import QueryHistoryRepository
from src.services.analyst_agent_service import AnalystAgentService
from src.schemas.user import UserCreate, UserRole
from src.core.security import get_password_hash

logger = logging.getLogger(__name__)


class ServiceFactory:
    """服务工厂，统一管理和访问所有服务实例"""
    
    _instance = None
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(ServiceFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化服务工厂"""
        if not self._initialized:
            self._initialized = True
            self._db_service: Optional[DatabaseService] = None
            self._llm_service: Optional[LLMService] = None
            self._document_service: Optional[DocumentService] = None
            self._knowledge_graph_service: Optional[KnowledgeGraphService] = None
            self._analyst_agent: Optional[AnalystAgent] = None
            self._ocr_service: Optional[OCRService] = None
            self._user_repository: Optional[UserRepository] = None
            self._document_repository: Optional[DocumentRepository] = None
            self._knowledge_repository: Optional[KnowledgeRepository] = None
            self._query_history_repository: Optional[QueryHistoryRepository] = None
    
    @property
    def db_service(self) -> DatabaseService:
        """获取数据库服务实例"""
        if self._db_service is None:
            self._db_service = DatabaseService()
        return self._db_service
    
    @property
    def llm_service(self) -> LLMService:
        """获取LLM服务实例"""
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service
    
    @property
    def knowledge_repository(self) -> KnowledgeRepository:
        """获取知识仓库实例"""
        if self._knowledge_repository is None:
            self._knowledge_repository = KnowledgeRepository()
        return self._knowledge_repository
    
    @property
    def document_service(self) -> DocumentService:
        """获取文档服务实例"""
        if self._document_service is None:
            self._document_service = DocumentService(
                document_repository=self.document_repository,
                knowledge_repository=self.knowledge_repository
            )
        return self._document_service
    
    @property
    def knowledge_graph_service(self) -> KnowledgeGraphService:
        """获取知识图谱服务实例"""
        if self._knowledge_graph_service is None:
            self._knowledge_graph_service = KnowledgeGraphService()
        return self._knowledge_graph_service
    
    @property
    def analyst_agent(self):
        """获取分析师智能体实例"""
        if self._analyst_agent is None:
            # 使用延迟导入避免循环依赖
            from src.services.analyst_agent import AnalystAgent
            self._analyst_agent = AnalystAgent()
        return self._analyst_agent
    
    @property
    def analyst_agent_service(self):
        """
        获取分析师代理服务实例
        """
        if not hasattr(self, '_analyst_agent_service'):
            self._analyst_agent_service = AnalystAgentService(
                knowledge_repository=self.knowledge_repository,
                document_service=self.document_service
            )
        return self._analyst_agent_service
    
    @property
    def user_repository(self) -> UserRepository:
        """获取用户仓库实例"""
        if self._user_repository is None:
            self._user_repository = UserRepository()
        return self._user_repository
    
    @property
    def document_repository(self) -> DocumentRepository:
        """获取文档仓库实例"""
        if self._document_repository is None:
            self._document_repository = DocumentRepository()
        return self._document_repository
    
    @property
    def query_history_repository(self) -> QueryHistoryRepository:
        """获取查询历史仓库实例"""
        if self._query_history_repository is None:
            self._query_history_repository = QueryHistoryRepository()
        return self._query_history_repository
    
    @property
    def ocr_service(self) -> OCRService:
        """获取OCR服务实例"""
        if self._ocr_service is None:
            self._ocr_service = OCRService()
        return self._ocr_service
    
    async def initialize_all(self):
        """初始化所有服务"""
        try:
            logger.info("开始初始化所有服务...")
            
            # 初始化数据库服务
            await self.db_service.initialize()
            logger.info("数据库服务初始化完成")
            
            # 初始化知识图谱服务
            await self.knowledge_graph_service.initialize()
            logger.info("知识图谱服务初始化完成")
            
            # 初始化LLM服务
            await self.llm_service.initialize()
            logger.info("LLM服务初始化完成")
            
            # 初始化文档服务
            await self.document_service.initialize()
            logger.info("文档服务初始化完成")
            
            logger.info("所有服务初始化完成")
            
        except Exception as e:
            logger.error(f"服务初始化失败: {str(e)}")
            raise
    
    async def shutdown_all(self):
        """关闭所有服务"""
        try:
            logger.info("开始关闭所有服务...")
            
            # 关闭文档服务
            if self._document_service:
                await self._document_service.shutdown()
                self._document_service = None
                logger.info("文档服务已关闭")
            
            # 关闭LLM服务
            if self._llm_service:
                await self._llm_service.shutdown()
                self._llm_service = None
                logger.info("LLM服务已关闭")
            
            # 关闭知识图谱服务
            if self._knowledge_graph_service:
                await self._knowledge_graph_service.shutdown()
                self._knowledge_graph_service = None
                logger.info("知识图谱服务已关闭")
            
            # 关闭数据库服务
            if self._db_service:
                await self._db_service.disconnect()
                self._db_service = None
                logger.info("数据库服务已关闭")
            
            # 重置其他服务实例
            self._analyst_agent = None
            self._user_repository = None
            self._document_repository = None
            self._query_history_repository = None
            
            logger.info("所有服务已关闭")
            
        except Exception as e:
            logger.error(f"服务关闭失败: {str(e)}")
            raise
    
    @asynccontextmanager
    async def managed_services(self):
        """异步上下文管理器，用于自动初始化和关闭服务"""
        try:
            await self.initialize_all()
            yield self
        finally:
            await self.shutdown_all()


# 创建全局服务工厂实例
service_factory = ServiceFactory()