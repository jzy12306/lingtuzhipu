import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.models.knowledge import Entity, Relation
from src.models.document import Document
from src.repositories.knowledge_repository import KnowledgeRepository
from src.config.settings import settings

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
    async def extract_entities(self, content: str, document_id: str, user_id: str, industry: Optional[str] = None) -> List[Entity]:
        """
        从文本内容中提取实体
        
        Args:
            content: 文档文本内容
            document_id: 文档ID
            user_id: 用户ID
            industry: 行业类型（可选）
            
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
    
    async def save_extracted_knowledge(self, entities: List[Entity], relations: List[Relation], document_id: str, user_id: str) -> Dict:
        """
        保存提取的知识到数据库
        
        Args:
            entities: 要保存的实体列表
            relations: 要保存的关系列表
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            包含处理结果的字典
        """
        try:
            # 批量保存实体 - 使用事务或批量操作
            saved_entities = []
            entity_errors = []
            
            # 确保user_id为有效字符串
            if not user_id:
                user_id = "default_user"
            
            # 批量保存实体
            saved_entities = []
            entity_errors = []
            
            try:
                # 创建实体ID到名称的映射，用于关系保存
                entity_id_to_name = {entity.id: entity.name for entity in entities}
                
                # 将实体转换为字典格式
                entities_data = []
                for entity in entities:
                    entity_dict = {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "description": entity.description,
                        "properties": entity.properties,
                        "source_document_id": entity.source_document_id,
                        "confidence_score": entity.confidence_score,
                        "is_valid": entity.is_valid,
                        "created_at": entity.created_at,
                        "updated_at": entity.updated_at,
                        "document_id": document_id,
                        "user_id": user_id
                    }
                    entities_data.append(entity_dict)
                
                # 批量保存实体
                saved_entities = await self.knowledge_repository.batch_create_entities(entities_data)
            except Exception as e:
                logger.error(f"批量保存实体失败: {str(e)}")
                entity_errors.append({"entity": "batch", "error": str(e)})
            
            # 批量保存关系
            saved_relations = []
            relation_errors = []
            
            try:
                # 将关系转换为字典格式
                relations_data = []
                for relation in relations:
                    # 获取源实体和目标实体的名称
                    source_entity_name = entity_id_to_name.get(relation.source_entity_id, "未知实体")
                    target_entity_name = entity_id_to_name.get(relation.target_entity_id, "未知实体")
                    
                    relation_dict = {
                        "id": relation.id,
                        "source_entity_id": relation.source_entity_id,
                        "target_entity_id": relation.target_entity_id,
                        "type": relation.type,
                        "description": relation.description,
                        "properties": relation.properties,
                        "source_document_id": relation.source_document_id,
                        "confidence_score": relation.confidence_score,
                        "is_valid": relation.is_valid,
                        "created_at": relation.created_at,
                        "updated_at": relation.updated_at,
                        "source_entity_name": source_entity_name,
                        "target_entity_name": target_entity_name,
                        "document_id": document_id,
                        "user_id": user_id
                    }
                    relations_data.append(relation_dict)
                
                # 批量保存关系
                saved_relations = await self.knowledge_repository.batch_create_relations(relations_data)
            except Exception as e:
                logger.error(f"批量保存关系失败: {str(e)}")
                relation_errors.append({"relation": "batch", "error": str(e)})
            
            # 同时更新文档状态、顶层计数和processing_details字段
            update_success = await self.knowledge_repository.update_document_status(
                document_id=document_id,
                status="processed",
                entities_count=len(saved_entities),
                relations_count=len(saved_relations),
                processing_details={
                    "entities_saved": len(saved_entities),
                    "relations_saved": len(saved_relations),
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
            if update_success:
                logger.info(f"文档状态更新成功: 实体 {len(saved_entities)}, 关系 {len(saved_relations)}")
            else:
                logger.warning(f"文档状态更新失败: {document_id}")
            
            logger.info(f"知识保存完成 - 实体: {len(saved_entities)}, 关系: {len(saved_relations)}")
            logger.info(f"文档计数已更新: 实体 {len(saved_entities)}, 关系 {len(saved_relations)}")
            
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
                "status": "success",
                "errors": {
                    "entities": entity_errors,
                    "relations": relation_errors
                }
            }
        except Exception as e:
            logger.error(f"保存知识失败: {str(e)}")
            return {
                "entities": {
                    "total": len(entities),
                    "saved": 0,
                    "failed": len(entities)
                },
                "relations": {
                    "total": len(relations),
                    "saved": 0,
                    "failed": len(relations)
                },
                "status": "error",
                "errors": {
                    "entities": [],
                    "relations": [],
                    "general": str(e)
                }
            }
    
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
