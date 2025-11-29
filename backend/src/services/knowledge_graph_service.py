import logging
import json
from typing import List, Dict, Optional, Any
from src.repositories.knowledge_repository import KnowledgeRepository
from src.models.knowledge import KnowledgeGraphQuery, KnowledgeGraphResponse

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        from src.repositories.knowledge_repository import KnowledgeRepository
        self._repository = KnowledgeRepository()
        self._is_initialized = False
    
    @property
    def is_initialized(self):
        return self._is_initialized
    
    async def initialize(self):
        """初始化服务"""
        try:
            # 创建Neo4j索引
            await self._repository.create_neo4j_indexes()
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
            logger.info(f"搜索实体: {query}")
            entities = await self._repository.search_entities(query)
            logger.info(f"搜索到 {len(entities)} 个实体")
            logger.debug(f"搜索到的实体: {json.dumps(entities, ensure_ascii=False)}")
            return entities
        except Exception as e:
            logger.error(f"搜索实体失败: {str(e)}", exc_info=True)
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
    
    async def find_shortest_path(self, source_id: str, target_id: str, max_depth: int = 5) -> Optional[Dict[str, Any]]:
        """查找两个实体之间的最短路径"""
        try:
            logger.info(f"查找最短路径: {source_id} -> {target_id}")
            return await self._repository.find_shortest_path(source_id, target_id, max_depth)
        except Exception as e:
            logger.error(f"查找最短路径失败: {str(e)}")
            return None
    
    async def detect_communities(self, algorithm: str = "louvain", weight_property: str = "confidence_score") -> Optional[Dict[str, Any]]:
        """检测社区"""
        try:
            logger.info(f"使用{algorithm}算法检测社区")
            return await self._repository.detect_communities(algorithm, weight_property)
        except Exception as e:
            logger.error(f"检测社区失败: {str(e)}")
            return None
    
    async def find_entity_path(self, source_id: str, target_id: str, max_depth: int = 3) -> Optional[Dict[str, Any]]:
        """查找两个实体之间的路径"""
        try:
            logger.info(f"查找实体路径: {source_id} -> {target_id}")
            path = await self._repository.find_entity_path(source_id, target_id, max_depth)
            if path:
                # 转换为字典格式
                return {
                    "entities": [entity.dict() for entity in path.entities],
                    "relations": [relation.dict() for relation in path.relations],
                    "path_sequence": path.path_sequence
                }
            return None
        except Exception as e:
            logger.error(f"查找实体路径失败: {str(e)}")
            return None

# 创建知识图谱服务实例
knowledge_graph_service = KnowledgeGraphService()
