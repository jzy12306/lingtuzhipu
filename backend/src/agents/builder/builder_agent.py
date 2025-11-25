import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.models.knowledge import Entity, Relation
from src.models.document import Document
from src.repositories.knowledge_repository import KnowledgeRepository
from src.utils.config import settings

logger = logging.getLogger(__name__)


class BuilderAgent(ABC):
    """构建者智能体基类，负责文档处理和知识抽取"""
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        self.knowledge_repository = knowledge_repository
        self.enabled = settings.BUILDER_AGENT_ENABLED
        logger.info("构建者智能体初始化完成")
    
    @abstractmethod
    async def process_document(self, document: Document) -> Dict:
        """
        处理文档并提取知识
        
        Args:
            document: 要处理的文档对象
            
        Returns:
            包含处理结果的字典
        """
        pass
    
    @abstractmethod
    async def extract_entities(self, content: str, document_id: str, user_id: str) -> List[Entity]:
        """
        从文本内容中提取实体
        
        Args:
            content: 文档文本内容
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            提取的实体列表
        """
        pass
    
    @abstractmethod
    async def extract_relations(self, content: str, entities: List[Entity], document_id: str, user_id: str) -> List[Relation]:
        """
        从文本内容和实体列表中提取关系
        
        Args:
            content: 文档文本内容
            entities: 文档中的实体列表
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            提取的关系列表
        """
        pass
    
    @abstractmethod
    async def enrich_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        丰富实体信息（添加类型、描述等）
        
        Args:
            entities: 要丰富的实体列表
            
        Returns:
            丰富后的实体列表
        """
        pass
    
    @abstractmethod
    async def validate_extractions(self, entities: List[Entity], relations: List[Relation]) -> Tuple[List[Entity], List[Relation], List[Dict]]:
        """
        验证提取的实体和关系的有效性
        
        Args:
            entities: 提取的实体列表
            relations: 提取的关系列表
            
        Returns:
            (有效实体列表, 有效关系列表, 验证错误列表)
        """
        pass
    
    async def save_extracted_knowledge(self, entities: List[Entity], relations: List[Relation], document_id: str) -> Dict:
        """
        保存提取的知识到数据库
        
        Args:
            entities: 要保存的实体列表
            relations: 要保存的关系列表
            document_id: 文档ID
            
        Returns:
            保存结果统计
        """
        try:
            # 保存实体
            saved_entities = []
            for entity in entities:
                try:
                    saved_entity = await self.knowledge_repository.create_entity(entity)
                    saved_entities.append(saved_entity)
                except Exception as e:
                    logger.error(f"保存实体失败: {entity.name}, 错误: {str(e)}")
            
            # 保存关系
            saved_relations = []
            for relation in relations:
                try:
                    saved_relation = await self.knowledge_repository.create_relation(relation)
                    saved_relations.append(saved_relation)
                except Exception as e:
                    logger.error(f"保存关系失败: {relation.type}, 错误: {str(e)}")
            
            # 更新文档状态
            await self.knowledge_repository.update_document_status(
                document_id=document_id,
                status="processed",
                processing_details={
                    "entities_count": len(saved_entities),
                    "relations_count": len(saved_relations),
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"知识保存完成 - 实体: {len(saved_entities)}, 关系: {len(saved_relations)}")
            
            return {
                "entities": {
                    "total": len(entities),
                    "saved": len(saved_entities),
                    "failed": len(entities) - len(saved_entities)
                },
                "relations": {
                    "total": len(relations),
                    "saved": len(saved_relations),
                    "failed": len(relations) - len(saved_relations)
                },
                "status": "success"
            }
        except Exception as e:
            logger.error(f"保存知识失败: {str(e)}")
            # 更新文档状态为处理失败
            await self.knowledge_repository.update_document_status(
                document_id=document_id,
                status="processing_failed",
                processing_details={
                    "error": str(e),
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            raise
    
    def _generate_entity_id(self, name: str, document_id: str) -> str:
        """
        生成实体ID
        
        Args:
            name: 实体名称
            document_id: 文档ID
            
        Returns:
            实体ID
        """
        # 这里可以使用更复杂的算法生成唯一ID
        return f"{document_id}_entity_{hash(name)}_{datetime.utcnow().timestamp()}"
    
    def _generate_relation_id(self, source_id: str, target_id: str, relation_type: str) -> str:
        """
        生成关系ID
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            
        Returns:
            关系ID
        """
        # 这里可以使用更复杂的算法生成唯一ID
        return f"{source_id}_to_{target_id}_{relation_type}_{datetime.utcnow().timestamp()}"
    
    async def check_document_size_limits(self, entities: List[Entity], relations: List[Relation]) -> Tuple[bool, Optional[str]]:
        """
        检查文档的实体和关系数量是否超过限制
        
        Args:
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            (是否超过限制, 错误消息)
        """
        if len(entities) > settings.MAX_ENTITIES_PER_DOCUMENT:
            return False, f"实体数量超过限制: {len(entities)} > {settings.MAX_ENTITIES_PER_DOCUMENT}"
        
        if len(relations) > settings.MAX_RELATIONS_PER_DOCUMENT:
            return False, f"关系数量超过限制: {len(relations)} > {settings.MAX_RELATIONS_PER_DOCUMENT}"
        
        return True, None
