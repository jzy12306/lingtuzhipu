import logging
from typing import List, Dict, Optional, Any
from src.repositories.knowledge_repository import KnowledgeRepository
from src.models.knowledge import KnowledgeGraphQuery, KnowledgeGraphResponse

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        self._repository = KnowledgeRepository()
        self._is_initialized = False
    
    @property
    def is_initialized(self):
        return self._is_initialized
    
    async def initialize(self):
        """初始化服务"""
        try:
            self._is_initialized = True
            logger.info("知识图谱服务初始化完成")
        except Exception as e:
            logger.error(f"知识图谱服务初始化失败: {str(e)}")
            self._is_initialized = False
            raise
    
    async def shutdown(self):
        """关闭服务"""
        self._is_initialized = False
        logger.info("知识图谱服务已关闭")
    
    async def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """搜索实体"""
        try:
            return await self._repository.search_entities(query)
        except Exception as e:
            logger.error(f"搜索实体失败: {str(e)}")
            return []
    
    async def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        try:
            return await self._repository.get_stats()
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {"entity_count": 0, "relation_count": 0}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取指标信息"""
        try:
            stats = await self.get_stats()
            return {
                "entity_count": stats.get("entity_count", 0),
                "relation_count": stats.get("relation_count", 0),
                "is_healthy": True
            }
        except Exception as e:
            logger.error(f"获取指标信息失败: {str(e)}")
            return {
                "entity_count": 0,
                "relation_count": 0,
                "is_healthy": False,
                "error": str(e)
            }

# 创建设置为 None
knowledge_graph_service: Optional[KnowledgeGraphService] = None
