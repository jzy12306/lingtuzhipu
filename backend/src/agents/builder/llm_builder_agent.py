import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import openai
from openai import OpenAI

from agents.builder.builder_agent import BuilderAgent
from models.knowledge import Entity, Relation
from models.document import Document
from repositories.knowledge_repository import KnowledgeRepository
from utils.config import settings

logger = logging.getLogger(__name__)


class LLMBuilderAgent(BuilderAgent):
    """基于LLM的构建者智能体实现"""
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        super().__init__(knowledge_repository)
        self.llm_client = self._init_llm_client()
        logger.info("LLM构建者智能体初始化完成")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if settings.USE_LOCAL_LLM:
            # 使用本地LLM（如LM Studio）
            logger.info(f"使用本地LLM: {settings.LOCAL_LLM_URL}")
            return OpenAI(
                base_url=settings.LOCAL_LLM_URL,
                api_key="not-needed-for-local-llm"
            )
        else:
            # 使用OpenAI API
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API密钥未设置，使用默认值")
            return OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def process_document(self, document: Document) -> Dict:
        """处理文档并提取知识"""
        try:
            logger.info(f"开始处理文档: {document.title} (ID: {document.id})")
            
            # 更新文档状态为处理中
            await self.knowledge_repository.update_document_status(
                document_id=document.id,
                status="processing"
            )
            
            # 步骤1: 提取实体
            entities = await self.extract_entities(
                content=document.content,
                document_id=document.id,
                user_id=document.user_id
            )
            
            # 步骤2: 丰富实体信息
            enriched_entities = await self.enrich_entities(entities)
            
            # 步骤3: 提取关系
            relations = await self.extract_relations(
                content=document.content,
                entities=enriched_entities,
                document_id=document.id,
                user_id=document.user_id
            )
            
            # 步骤4: 验证提取结果
            valid_entities, valid_relations, validation_errors = await self.validate_extractions(
                entities=enriched_entities,
                relations=relations
            )
            
            # 步骤5: 检查大小限制
            within_limits, limit_error = await self.check_document_size_limits(
                entities=valid_entities,
                relations=valid_relations
            )
            
            if not within_limits:
                raise Exception(limit_error)
            
            # 步骤6: 保存提取的知识
            save_result = await self.save_extracted_knowledge(
                entities=valid_entities,
                relations=valid_relations,
                document_id=document.id
            )
            
            result = {
                **save_result,
                "validation_errors": validation_errors,
                "processing_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"文档处理完成: {document.title}, 结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"处理文档失败: {document.title}, 错误: {str(e)}")
            # 更新文档状态为处理失败
            await self.knowledge_repository.update_document_status(
                document_id=document.id,
                status="processing_failed",
                processing_details={
                    "error": str(e),
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            raise
    
    async def extract_entities(self, content: str, document_id: str, user_id: str) -> List[Entity]:
        """从文本内容中提取实体"""
        try:
            # 准备提示词
            prompt = self._prepare_entity_extraction_prompt(content)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析响应
            entities_data = self._parse_entities_from_response(response)
            
            # 转换为Entity对象
            entities = []
            for entity_data in entities_data:
                entity = Entity(
                    id=self._generate_entity_id(entity_data["name"], document_id),
                    name=entity_data["name"],
                    type=entity_data.get("type", "Unknown"),
                    description=entity_data.get("description", ""),
                    properties=entity_data.get("properties", {}),
                    document_id=document_id,
                    user_id=user_id,
                    created_at=datetime.utcnow()
                )
                entities.append(entity)
            
            logger.info(f"从文档中提取到 {len(entities)} 个实体")
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {str(e)}")
            # 如果LLM调用失败，使用简单的回退方法
            return self._fallback_entity_extraction(content, document_id, user_id)
    
    async def extract_relations(self, content: str, entities: List[Entity], document_id: str, user_id: str) -> List[Relation]:
        """从文本内容和实体列表中提取关系"""
        try:
            # 准备提示词
            prompt = self._prepare_relation_extraction_prompt(content, entities)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析响应
            relations_data = self._parse_relations_from_response(response)
            
            # 转换为Relation对象
            relations = []
            for relation_data in relations_data:
                # 查找源实体和目标实体
                source_entity = next(
                    (e for e in entities if e.name == relation_data["source"]),
                    None
                )
                target_entity = next(
                    (e for e in entities if e.name == relation_data["target"]),
                    None
                )
                
                if source_entity and target_entity:
                    relation = Relation(
                        id=self._generate_relation_id(source_entity.id, target_entity.id, relation_data["type"]),
                        type=relation_data["type"],
                        source_entity_id=source_entity.id,
                        target_entity_id=target_entity.id,
                        source_entity_name=source_entity.name,
                        target_entity_name=target_entity.name,
                        properties=relation_data.get("properties", {}),
                        description=relation_data.get("description", ""),
                        document_id=document_id,
                        user_id=user_id,
                        created_at=datetime.utcnow()
                    )
                    relations.append(relation)
            
            logger.info(f"从文档中提取到 {len(relations)} 个关系")
            return relations
            
        except Exception as e:
            logger.error(f"关系提取失败: {str(e)}")
            # 返回空列表作为回退
            return []
    
    async def enrich_entities(self, entities: List[Entity]) -> List[Entity]:
        """丰富实体信息"""
        try:
            # 为每个实体调用LLM获取更多信息
            enriched_entities = []
            for entity in entities:
                try:
                    prompt = self._prepare_entity_enrichment_prompt(entity)
                    response = await self._call_llm(prompt)
                    enrichment_data = self._parse_entity_enrichment(response)
                    
                    # 更新实体信息
                    entity.type = enrichment_data.get("type", entity.type)
                    entity.description = enrichment_data.get("description", entity.description)
                    entity.properties = {**entity.properties, **enrichment_data.get("properties", {})}
                    
                    enriched_entities.append(entity)
                except Exception as e:
                    logger.warning(f"丰富实体失败: {entity.name}, 错误: {str(e)}")
                    enriched_entities.append(entity)
            
            return enriched_entities
            
        except Exception as e:
            logger.error(f"实体丰富失败: {str(e)}")
            # 返回原始实体列表
            return entities
    
    async def validate_extractions(self, entities: List[Entity], relations: List[Relation]) -> Tuple[List[Entity], List[Relation], List[Dict]]:
        """验证提取的实体和关系的有效性"""
        validation_errors = []
        valid_entities = []
        valid_relations = []
        
        # 验证实体
        entity_names = set()
        for entity in entities:
            errors = []
            
            # 检查名称
            if not entity.name or not entity.name.strip():
                errors.append("实体名称不能为空")
            elif len(entity.name.strip()) < 2:
                errors.append("实体名称太短")
            elif entity.name in entity_names:
                errors.append("实体名称重复")
            
            # 检查类型
            if not entity.type or entity.type == "Unknown":
                errors.append("实体类型未知")
            
            if errors:
                validation_errors.append({
                    "type": "entity",
                    "id": entity.id,
                    "name": entity.name,
                    "errors": errors
                })
            else:
                valid_entities.append(entity)
                entity_names.add(entity.name)
        
        # 验证关系
        for relation in relations:
            errors = []
            
            # 检查关系类型
            if not relation.type or not relation.type.strip():
                errors.append("关系类型不能为空")
            
            # 检查实体引用
            source_exists = any(e.id == relation.source_entity_id for e in valid_entities)
            target_exists = any(e.id == relation.target_entity_id for e in valid_entities)
            
            if not source_exists:
                errors.append("源实体不存在")
            if not target_exists:
                errors.append("目标实体不存在")
            
            if errors:
                validation_errors.append({
                    "type": "relation",
                    "id": relation.id,
                    "source": relation.source_entity_name,
                    "target": relation.target_entity_name,
                    "relation_type": relation.type,
                    "errors": errors
                })
            else:
                valid_relations.append(relation)
        
        logger.info(f"验证结果 - 有效实体: {len(valid_entities)}, 有效关系: {len(valid_relations)}, 错误数: {len(validation_errors)}")
        return valid_entities, valid_relations, validation_errors
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM服务"""
        try:
            # 确保使用异步调用
            import asyncio
            
            # 同步调用，需要在异步环境中运行
            response = await asyncio.to_thread(
                self.llm_client.chat.completions.create,
                model="gpt-4-turbo" if not settings.USE_LOCAL_LLM else "local-model",
                messages=[
                    {"role": "system", "content": "你是一个专业的知识图谱构建助手。请严格按照要求的格式输出JSON。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise
    
    def _prepare_entity_extraction_prompt(self, content: str) -> str:
        """准备实体提取提示词"""
        return f"""
请从以下文本中提取所有实体。每个实体应该包含名称、类型和简要描述。

文本内容:
{content[:3000]}  # 限制输入长度

请以以下JSON格式输出，确保是有效的JSON：
[
    {
        "name": "实体名称",
        "type": "实体类型（如人物、组织、地点、事件、概念等）",
        "description": "实体的简要描述",
        "properties": {{}}
    }
]

请只返回JSON，不要包含其他说明文字。
"""
    
    def _parse_entities_from_response(self, response: str) -> List[Dict]:
        """从LLM响应中解析实体"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析实体响应失败: {str(e)}")
            return []
    
    def _prepare_relation_extraction_prompt(self, content: str, entities: List[Entity]) -> str:
        """准备关系提取提示词"""
        entities_str = "\n".join([f"- {e.name} ({e.type})" for e in entities[:50]])  # 限制实体数量
        
        return f"""
请从以下文本中提取实体之间的关系。

已知实体列表:
{entities_str}

文本内容:
{content[:3000]}  # 限制输入长度

请以以下JSON格式输出，确保是有效的JSON：
[
    {
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型（如包含、属于、发生于、创建于等）",
        "description": "关系的简要描述",
        "properties": {{}}
    }
]

请只返回JSON，不要包含其他说明文字。
"""
    
    def _parse_relations_from_response(self, response: str) -> List[Dict]:
        """从LLM响应中解析关系"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析关系响应失败: {str(e)}")
            return []
    
    def _prepare_entity_enrichment_prompt(self, entity: Entity) -> str:
        """准备实体丰富提示词"""
        return f"""
请为以下实体提供更详细的类型、描述和相关属性。

实体名称: {entity.name}
当前类型: {entity.type}
当前描述: {entity.description}

请以以下JSON格式输出，确保是有效的JSON：
{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {
        "属性1": "值1",
        "属性2": "值2"
    }
}

请只返回JSON，不要包含其他说明文字。
"""
    
    def _parse_entity_enrichment(self, response: str) -> Dict:
        """解析实体丰富响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析实体丰富响应失败: {str(e)}")
            return {}
    
    def _fallback_entity_extraction(self, content: str, document_id: str, user_id: str) -> List[Entity]:
        """简单的回退实体提取方法"""
        # 这是一个简单的基于规则的回退方法
        # 在实际应用中可以实现更复杂的规则
        entities = []
        
        # 提取可能的人名（简单规则）
        person_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
        for match in re.finditer(person_pattern, content):
            name = match.group(1)
            entity = Entity(
                id=self._generate_entity_id(name, document_id),
                name=name,
                type="Person",
                description="",
                document_id=document_id,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            entities.append(entity)
        
        # 提取可能的组织名（简单规则）
        org_pattern = r'(公司|组织|机构|协会|集团|大学|学院)'
        for match in re.finditer(org_pattern, content):
            name = match.group(0)
            entity = Entity(
                id=self._generate_entity_id(name, document_id),
                name=name,
                type="Organization",
                description="",
                document_id=document_id,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            entities.append(entity)
        
        return entities
