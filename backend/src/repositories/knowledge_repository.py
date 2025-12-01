import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId
from src.services.db_service import db_service
from src.models.knowledge import (
    Entity, EntityCreate, EntityUpdate, EntityResponse,
    Relation, RelationCreate, RelationUpdate, RelationResponse,
    KnowledgeGraphQuery, KnowledgeGraphResponse,
    KnowledgeConflict, GraphVisualization, EntityNode, RelationEdge,
    KnowledgeGraphQueryAdvanced, KnowledgeStats, KnowledgeGraphPath
)
import uuid
from pymongo import MongoClient
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """知识图谱仓库"""
    
    def __init__(self, mongo_client: MongoClient = None, neo4j_driver = None):
        self.mongo_client = mongo_client
        self.neo4j_driver = neo4j_driver
        self.logger = logger.getChild("KnowledgeRepository")
    

    
    def get_neo4j_driver(self):
        """获取Neo4j驱动"""
        return db_service.get_neo4j_driver()
    
    async def create_neo4j_indexes(self):
        """创建Neo4j索引"""
        try:
            self.logger.info("开始创建Neo4j索引")
            
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is not None:
                async with neo4j_driver.session() as session:
                    # 创建实体ID索引
                    await session.run("CREATE INDEX entity_id_idx IF NOT EXISTS FOR (e:Entity) ON (e.id)")
                    self.logger.info("创建实体ID索引成功")
                    
                    # 创建实体名称索引
                    await session.run("CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)")
                    self.logger.info("创建实体名称索引成功")
                    
                    # 创建实体类型索引
                    await session.run("CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)")
                    self.logger.info("创建实体类型索引成功")
                    
                    # 创建实体来源文档ID索引
                    await session.run("CREATE INDEX entity_source_doc_idx IF NOT EXISTS FOR (e:Entity) ON (e.source_document_id)")
                    self.logger.info("创建实体来源文档ID索引成功")
                    
                    # 创建关系ID索引
                    await session.run("CREATE INDEX relation_id_idx IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.id)")
                    self.logger.info("创建关系ID索引成功")
                    
                    # 创建关系类型索引
                    await session.run("CREATE INDEX relation_type_idx IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.type)")
                    self.logger.info("创建关系类型索引成功")
                    
                    # 创建关系来源文档ID索引
                    await session.run("CREATE INDEX relation_source_doc_idx IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.source_document_id)")
                    self.logger.info("创建关系来源文档ID索引成功")
                    
                    # 创建关系源实体ID索引
                    await session.run("CREATE INDEX relation_source_entity_idx IF NOT EXISTS FOR ()-[r:RELATION]->() ON (r.source_entity_id)")
                    self.logger.info("创建关系源实体ID索引成功")
                    
                    # 创建关系目标实体ID索引
                    await session.run("CREATE INDEX relation_target_entity_idx IF NOT EXISTS FOR ()-[r:RELATION]->() ON (r.target_entity_id)")
                    self.logger.info("创建关系目标实体ID索引成功")
            
            self.logger.info("Neo4j索引创建完成")
        except Exception as e:
            self.logger.error(f"创建Neo4j索引失败: {str(e)}")
            # 索引创建失败不影响程序运行，继续执行
    
    async def create_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """创建实体"""
        try:
            # 生成实体ID
            if "id" not in entity_data:
                entity_data["id"] = str(uuid.uuid4())
            
            # 确保必要字段存在
            if "confidence_score" not in entity_data:
                entity_data["confidence_score"] = 1.0
            if "is_valid" not in entity_data:
                entity_data["is_valid"] = True
            if "created_at" not in entity_data:
                entity_data["created_at"] = datetime.utcnow()
            if "updated_at" not in entity_data:
                entity_data["updated_at"] = datetime.utcnow()
            
            # 从properties中提取属性
            properties = entity_data.pop("properties", {})
            
            # 保存到MongoDB
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                # 将properties合并回entity_data
                entity_data["properties"] = properties
                
                # 保存到MongoDB
                entities_collection = mongodb.entities
                await entities_collection.insert_one(entity_data)
            
            # 保存到Neo4j（异步，不阻塞主流程）
            asyncio.create_task(self._save_entity_to_neo4j(entity_data))
            
            # 返回创建的实体
            return Entity(**entity_data)
        except Exception as e:
            self.logger.error(f"创建实体失败: {str(e)}")
            raise
    
    async def _save_entity_to_neo4j(self, entity_data: Dict[str, Any]):
        """异步保存实体到Neo4j"""
        try:
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is not None:
                async with neo4j_driver.session() as session:
                    # 构建Cypher查询
                    cypher = """
                    CREATE (e:Entity {
                        id: $id,
                        name: $name,
                        type: $type,
                        description: $description,
                        properties: $properties,
                        confidence_score: $confidence_score,
                        is_valid: $is_valid,
                        source_document_id: $source_document_id,
                        document_id: $document_id,
                        user_id: $user_id,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                    RETURN e
                    """
                    
                    # 执行Cypher查询
                    result = await session.run(cypher, {
                        "id": entity_data["id"],
                        "name": entity_data["name"],
                        "type": entity_data["type"],
                        "description": entity_data.get("description", ""),
                        "properties": entity_data.get("properties", {}),
                        "confidence_score": entity_data["confidence_score"],
                        "is_valid": entity_data["is_valid"],
                        "source_document_id": entity_data.get("source_document_id"),
                        "document_id": entity_data.get("document_id"),
                        "user_id": entity_data.get("user_id"),
                        "created_at": entity_data["created_at"].isoformat(),
                        "updated_at": entity_data["updated_at"].isoformat()
                    })
                    
                    # 检查结果
                    record = await result.single()
                    if not record:
                        self.logger.warning(f"Neo4j保存实体失败: {entity_data['id']}")
        except Exception as neo4j_error:
            self.logger.error(f"Neo4j保存实体失败: {str(neo4j_error)}")
    
    async def create_relation(self, relation_data: Dict[str, Any]) -> Relation:
        """创建关系"""
        try:
            # 生成关系ID
            if "id" not in relation_data:
                relation_data["id"] = str(uuid.uuid4())
            
            # 确保必要字段存在
            if "confidence_score" not in relation_data:
                relation_data["confidence_score"] = 1.0
            if "is_valid" not in relation_data:
                relation_data["is_valid"] = True
            if "created_at" not in relation_data:
                relation_data["created_at"] = datetime.utcnow()
            if "updated_at" not in relation_data:
                relation_data["updated_at"] = datetime.utcnow()
            # 添加description字段，默认值为空字符串
            if "description" not in relation_data:
                relation_data["description"] = ""
            
            # 从properties中提取属性
            properties = relation_data.pop("properties", {})
            
            # 保存到MongoDB
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                # 将properties合并回relation_data
                relation_data["properties"] = properties
                
                # 保存到MongoDB
                relations_collection = mongodb.relations
                await relations_collection.insert_one(relation_data)
            
            # 保存到Neo4j（异步，不阻塞主流程）
            asyncio.create_task(self._save_relation_to_neo4j(relation_data))
            
            # 返回创建的关系
            return Relation(**relation_data)
        except Exception as e:
            self.logger.error(f"创建关系失败: {str(e)}")
            raise
    
    async def _save_relation_to_neo4j(self, relation_data: Dict[str, Any]):
        """异步保存关系到Neo4j"""
        try:
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is not None:
                async with neo4j_driver.session() as session:
                    # 构建Cypher查询
                    cypher = """
                    MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
                    CREATE (source)-[r:RELATION {
                        id: $id,
                        type: $type,
                        source_entity_name: $source_entity_name,
                        target_entity_name: $target_entity_name,
                        description: $description,
                        properties: $properties,
                        confidence_score: $confidence_score,
                        is_valid: $is_valid,
                        source_document_id: $source_document_id,
                        document_id: $document_id,
                        user_id: $user_id,
                        created_at: $created_at,
                        updated_at: $updated_at
                    }]->(target)
                    RETURN r
                    """
                    
                    # 执行Cypher查询
                    result = await session.run(cypher, {
                        "id": relation_data["id"],
                        "source_id": relation_data["source_entity_id"],
                        "target_id": relation_data["target_entity_id"],
                        "type": relation_data["type"],
                        "source_entity_name": relation_data.get("source_entity_name"),
                        "target_entity_name": relation_data.get("target_entity_name"),
                        "description": relation_data.get("description", ""),
                        "properties": relation_data.get("properties", {}),
                        "confidence_score": relation_data["confidence_score"],
                        "is_valid": relation_data["is_valid"],
                        "source_document_id": relation_data.get("source_document_id"),
                        "document_id": relation_data.get("document_id"),
                        "user_id": relation_data.get("user_id"),
                        "created_at": relation_data["created_at"].isoformat(),
                        "updated_at": relation_data["updated_at"].isoformat()
                    })
                    
                    # 检查结果
                    record = await result.single()
                    if not record:
                        self.logger.warning(f"Neo4j保存关系失败: {relation_data['id']}")
        except Exception as neo4j_error:
            self.logger.error(f"Neo4j保存关系失败: {str(neo4j_error)}")
    
    async def batch_create_entities(self, entities_data: List[Dict[str, Any]]) -> List[Entity]:
        """批量创建实体"""
        try:
            saved_entities = []
            mongodb = await db_service.get_mongodb()
            
            if mongodb is not None:
                entities_collection = mongodb.entities
                
                # 批量插入到MongoDB
                if entities_data:
                    # 确保每个实体都有必要字段
                    for entity_data in entities_data:
                        if "id" not in entity_data:
                            entity_data["id"] = str(uuid.uuid4())
                        if "confidence_score" not in entity_data:
                            entity_data["confidence_score"] = 1.0
                        if "is_valid" not in entity_data:
                            entity_data["is_valid"] = True
                        if "created_at" not in entity_data:
                            entity_data["created_at"] = datetime.utcnow()
                        if "updated_at" not in entity_data:
                            entity_data["updated_at"] = datetime.utcnow()
                    
                    # 批量插入
                    await entities_collection.insert_many(entities_data)
                    saved_entities = [Entity(**entity_data) for entity_data in entities_data]
            
            # 临时禁用Neo4j写入（由于连接问题）
            # asyncio.create_task(self._batch_save_entities_to_neo4j(entities_data))
            if entities_data:
                self.logger.warning(f"Neo4j连接不可用，跳过实体写入Neo4j (MongoDB已保存 {len(entities_data)} 个实体)")
            
            return saved_entities
        except Exception as e:
            self.logger.error(f"批量创建实体失败: {str(e)}")
            raise
    
    async def batch_create_relations(self, relations_data: List[Dict[str, Any]]) -> List[Relation]:
        """批量创建关系"""
        try:
            saved_relations = []
            mongodb = await db_service.get_mongodb()
            
            if mongodb is not None:
                relations_collection = mongodb.relations
                
                # 批量插入到MongoDB
                if relations_data:
                    # 确保每个关系都有必要字段
                    for relation_data in relations_data:
                        if "id" not in relation_data:
                            relation_data["id"] = str(uuid.uuid4())
                        if "confidence_score" not in relation_data:
                            relation_data["confidence_score"] = 1.0
                        if "is_valid" not in relation_data:
                            relation_data["is_valid"] = True
                        if "created_at" not in relation_data:
                            relation_data["created_at"] = datetime.utcnow()
                        if "updated_at" not in relation_data:
                            relation_data["updated_at"] = datetime.utcnow()
                        if "description" not in relation_data:
                            relation_data["description"] = ""
                    
                    # 批量插入
                    await relations_collection.insert_many(relations_data)
                    saved_relations = [Relation(**relation_data) for relation_data in relations_data]
            
            # 临时禁用Neo4j写入（由于连接问题）
            # asyncio.create_task(self._batch_save_relations_to_neo4j(relations_data))
            if relations_data:
                self.logger.warning(f"Neo4j连接不可用，跳过关系统写入Neo4j (MongoDB已保存 {len(relations_data)} 个关系)")
            
            return saved_relations
        except Exception as e:
            self.logger.error(f"批量创建关系失败: {str(e)}")
            raise
    
    async def _batch_save_entities_to_neo4j(self, entities_data: List[Dict[str, Any]]):
        """异步批量保存实体到Neo4j"""
        try:
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is not None and entities_data:
                async with neo4j_driver.session() as session:
                    # 使用UNWIND进行批量插入
                    cypher = """
                    UNWIND $entities as entity
                    CREATE (e:Entity {
                        id: entity.id,
                        name: entity.name,
                        type: entity.type,
                        description: entity.description,
                        properties: entity.properties,
                        confidence_score: entity.confidence_score,
                        is_valid: entity.is_valid,
                        source_document_id: entity.source_document_id,
                        document_id: entity.document_id,
                        user_id: entity.user_id,
                        created_at: entity.created_at.isoformat(),
                        updated_at: entity.updated_at.isoformat()
                    })
                    RETURN count(e) as created_count
                    """
                    
                    result = await session.run(cypher, entities=entities_data)
                    record = await result.single()
                    if record:
                        self.logger.info(f"Neo4j批量保存实体成功，创建了 {record['created_count']} 个实体")
        except Exception as neo4j_error:
            self.logger.error(f"Neo4j批量保存实体失败: {str(neo4j_error)}")
    
    async def _batch_save_relations_to_neo4j(self, relations_data: List[Dict[str, Any]]):
        """异步批量保存关系到Neo4j"""
        try:
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is not None and relations_data:
                async with neo4j_driver.session() as session:
                    # 使用UNWIND进行批量插入
                    cypher = """
                    UNWIND $relations as relation
                    MATCH (source:Entity {id: relation.source_entity_id}), (target:Entity {id: relation.target_entity_id})
                    CREATE (source)-[r:RELATION {
                        id: relation.id,
                        type: relation.type,
                        source_entity_name: relation.source_entity_name,
                        target_entity_name: relation.target_entity_name,
                        description: relation.description,
                        properties: relation.properties,
                        confidence_score: relation.confidence_score,
                        is_valid: relation.is_valid,
                        source_document_id: relation.source_document_id,
                        document_id: relation.document_id,
                        user_id: relation.user_id,
                        created_at: relation.created_at.isoformat(),
                        updated_at: relation.updated_at.isoformat()
                    }]->(target)
                    RETURN count(r) as created_count
                    """
                    
                    result = await session.run(cypher, relations=relations_data)
                    record = await result.single()
                    if record:
                        self.logger.info(f"Neo4j批量保存关系成功，创建了 {record['created_count']} 个关系")
        except Exception as neo4j_error:
            self.logger.error(f"Neo4j批量保存关系失败: {str(neo4j_error)}")
    
    async def find_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """根据ID查找实体"""
        try:
            # 先从MongoDB查找
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                entities_collection = mongodb.entities
                entity_doc = await entities_collection.find_one({"id": entity_id})
                if entity_doc:
                    return Entity(**entity_doc)
            
            # 如果MongoDB中找不到，再从Neo4j查找
            query = """
            MATCH (e:Entity {id: $id})
            RETURN e
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query, id=entity_id)
                record = await result.single()
                
                if record:
                    entity_node = record["e"]
                    entity_dict = {
                        "id": entity_node["id"],
                        "name": entity_node["name"],
                        "type": entity_node["type"],
                        "confidence_score": entity_node["confidence_score"],
                        "is_valid": entity_node["is_valid"],
                        "source_document_id": entity_node["source_document_id"],
                        "created_at": datetime.fromisoformat(entity_node["created_at"]),
                        "updated_at": datetime.fromisoformat(entity_node["updated_at"]),
                        "properties": {}
                    }
                    
                    # 添加额外属性
                    for key, value in entity_node.items():
                        if key not in entity_dict:
                            entity_dict["properties"][key] = value
                    
                    return Entity(**entity_dict)
            
            return None
        except Exception as e:
            self.logger.error(f"查找实体失败: {str(e)}")
            raise
    
    async def find_relation_by_id(self, relation_id: str) -> Optional[Relation]:
        """根据ID查找关系"""
        try:
            # 先从MongoDB查找
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                relations_collection = mongodb.relations
                relation_doc = await relations_collection.find_one({"id": relation_id})
                if relation_doc:
                    return Relation(**relation_doc)
            
            # 如果MongoDB中找不到，再从Neo4j查找
            query = """
            MATCH ()-[r:RELATION {id: $id}]->()
            RETURN r, startNode(r).id as source_id, endNode(r).id as target_id
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query, id=relation_id)
                record = await result.single()
                
                if record:
                    relation_edge = record["r"]
                    relation_dict = {
                        "id": relation_edge["id"],
                        "source_entity_id": record["source_id"],
                        "target_entity_id": record["target_id"],
                        "type": relation_edge["type"],
                        "confidence_score": relation_edge["confidence_score"],
                        "is_valid": relation_edge["is_valid"],
                        "source_document_id": relation_edge["source_document_id"],
                        "created_at": datetime.fromisoformat(relation_edge["created_at"]),
                        "updated_at": datetime.fromisoformat(relation_edge["updated_at"]),
                        "properties": {}
                    }
                    
                    # 添加额外属性
                    for key, value in relation_edge.items():
                        if key not in relation_dict:
                            relation_dict["properties"][key] = value
                    
                    return Relation(**relation_dict)
            
            return None
        except Exception as e:
            self.logger.error(f"查找关系失败: {str(e)}")
            raise
    
    async def find_entities_by_document(self, document_id: str) -> List[Entity]:
        """查找文档中的所有实体"""
        try:
            # 先从MongoDB查找
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                entities_collection = mongodb.entities
                cursor = entities_collection.find({"source_document_id": document_id})
                entities = [Entity(**doc) async for doc in cursor]
                if entities:
                    return entities
            
            # 如果MongoDB中找不到，再从Neo4j查找
            query = """
            MATCH (e:Entity {source_document_id: $document_id})
            RETURN e
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query, document_id=document_id)
                entities = []
                
                async for record in result:
                    entity_node = record["e"]
                    entity_dict = {
                        "id": entity_node["id"],
                        "name": entity_node["name"],
                        "type": entity_node["type"],
                        "confidence_score": entity_node["confidence_score"],
                        "is_valid": entity_node["is_valid"],
                        "source_document_id": entity_node["source_document_id"],
                        "created_at": datetime.fromisoformat(entity_node["created_at"]),
                        "updated_at": datetime.fromisoformat(entity_node["updated_at"]),
                        "properties": {}
                    }
                    
                    # 添加额外属性
                    for key, value in entity_node.items():
                        if key not in entity_dict:
                            entity_dict["properties"][key] = value
                    
                    entities.append(Entity(**entity_dict))
                
                return entities
        except Exception as e:
            self.logger.error(f"查找文档实体失败: {str(e)}")
            raise
    
    async def search_entities(self, query: str) -> List[Entity]:
        """根据查询条件搜索实体"""
        try:
            # 使用Neo4j的全文搜索功能，在实体名称和属性中搜索
            search_query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($query) AND e.is_valid = true
            RETURN e
            ORDER BY e.confidence_score DESC
            LIMIT 100
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(search_query, query=query)
                entities = []
                
                async for record in result:
                    entity_node = record["e"]
                    entity_dict = {
                        "id": entity_node["id"],
                        "name": entity_node["name"],
                        "type": entity_node["type"],
                        "confidence_score": entity_node["confidence_score"],
                        "is_valid": entity_node["is_valid"],
                        "source_document_id": entity_node["source_document_id"],
                        "created_at": datetime.fromisoformat(entity_node["created_at"]),
                        "updated_at": datetime.fromisoformat(entity_node["updated_at"]),
                        "properties": {}
                    }
                    
                    # 添加额外属性
                    for key, value in entity_node.items():
                        if key not in entity_dict:
                            entity_dict["properties"][key] = value
                    
                    entities.append(Entity(**entity_dict))
                
                return entities
        except Exception as e:
            self.logger.error(f"搜索实体失败: {str(e)}")
            raise
    
    async def find_relations_by_document(self, document_id: str) -> List[Relation]:
        """查找文档中的所有关系"""
        try:
            # 先从MongoDB查找
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                relations_collection = mongodb.relations
                cursor = relations_collection.find({"source_document_id": document_id})
                relations = [Relation(**doc) async for doc in cursor]
                if relations:
                    return relations
            
            # 如果MongoDB中找不到，再从Neo4j查找
            query = """
            MATCH ()-[r:RELATION {source_document_id: $document_id}]->()
            RETURN r, startNode(r).id as source_id, endNode(r).id as target_id
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query, document_id=document_id)
                relations = []
                
                async for record in result:
                    relation_edge = record["r"]
                    relation_dict = {
                        "id": relation_edge["id"],
                        "source_entity_id": record["source_id"],
                        "target_entity_id": record["target_id"],
                        "type": relation_edge["type"],
                        "confidence_score": relation_edge["confidence_score"],
                        "is_valid": relation_edge["is_valid"],
                        "source_document_id": relation_edge["source_document_id"],
                        "created_at": datetime.fromisoformat(relation_edge["created_at"]),
                        "updated_at": datetime.fromisoformat(relation_edge["updated_at"]),
                        "properties": {}
                    }
                    
                    # 添加额外属性
                    for key, value in relation_edge.items():
                        if key not in relation_dict:
                            relation_dict["properties"][key] = value
                    
                    relations.append(Relation(**relation_dict))
                
                return relations
        except Exception as e:
            self.logger.error(f"查找文档关系失败: {str(e)}")
            raise
    
    async def execute_graph_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行自定义Cypher查询"""
        try:
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query, params or {})
                
                # 将结果转换为列表
                records = []
                async for record in result:
                    record_dict = {}
                    for key, value in record.items():
                        # 简单转换节点和关系
                        if hasattr(value, "id"):  # 节点或关系
                            if hasattr(value, "labels"):  # 节点
                                record_dict[key] = {
                                    "id": value.id,
                                    "labels": list(value.labels),
                                    "properties": dict(value)
                                }
                            else:  # 关系
                                record_dict[key] = {
                                    "id": value.id,
                                    "type": value.type,
                                    "properties": dict(value)
                                }
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                return {
                    "records": records,
                    "summary": str(result.consume())
                }
        except Exception as e:
            self.logger.error(f"执行图查询失败: {str(e)}")
            raise
    
    async def validate_knowledge_graph(self) -> List[KnowledgeConflict]:
        """验证知识图谱，检测潜在冲突"""
        conflicts = []
        
        try:
            # 1. 检测同名不同类型的实体
            query = """
            MATCH (e1:Entity), (e2:Entity)
            WHERE e1.name = e2.name AND e1.type <> e2.type AND e1.id < e2.id
            RETURN e1, e2
            """
            
            driver = self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(query)
                
                async for record in result:
                    e1 = record["e1"]
                    e2 = record["e2"]
                    
                    # 创建冲突记录
                    conflict = KnowledgeConflict(
                        conflict_id=str(uuid.uuid4()),
                        type="entity_type_conflict",
                        entities=[
                            Entity(
                                id=e1["id"],
                                name=e1["name"],
                                type=e1["type"],
                                confidence_score=e1["confidence_score"],
                                is_valid=e1["is_valid"],
                                source_document_id=e1["source_document_id"],
                                created_at=datetime.fromisoformat(e1["created_at"]),
                                updated_at=datetime.fromisoformat(e1["updated_at"]),
                                properties={}
                            ),
                            Entity(
                                id=e2["id"],
                                name=e2["name"],
                                type=e2["type"],
                                confidence_score=e2["confidence_score"],
                                is_valid=e2["is_valid"],
                                source_document_id=e2["source_document_id"],
                                created_at=datetime.fromisoformat(e2["created_at"]),
                                updated_at=datetime.fromisoformat(e2["updated_at"]),
                                properties={}
                            )
                        ],
                        relations=[],
                        description=f"实体 '{e1['name']}' 存在冲突的类型定义",
                        severity="medium",
                        suggested_resolution="检查实体定义，合并或重命名冲突的实体"
                    )
                    conflicts.append(conflict)
            
            return conflicts
        except Exception as e:
            self.logger.error(f"验证知识图谱失败: {str(e)}")
            raise
    
    async def get_knowledge_stats(self) -> KnowledgeStats:
        """获取知识图谱统计信息"""
        try:
            # 使用db_service访问数据库
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                entities_collection = mongodb.entities
                relations_collection = mongodb.relations
                
                # 统计实体总数
                total_entities = await entities_collection.count_documents({"is_valid": True})
                
                # 统计关系总数
                total_relations = await relations_collection.count_documents({"is_valid": True})
                
                # 统计实体类型分布
                entity_types = {}
                async for doc in entities_collection.aggregate([
                    {"$match": {"is_valid": True}},
                    {"$group": {"_id": "$type", "count": {"$sum": 1}}}
                ]):
                    entity_types[doc["_id"]] = doc["count"]
                
                # 统计关系类型分布
                relation_types = {}
                async for doc in relations_collection.aggregate([
                    {"$match": {"is_valid": True}},
                    {"$group": {"_id": "$type", "count": {"$sum": 1}}}
                ]):
                    relation_types[doc["_id"]] = doc["count"]
                
                # 统计每个文档的实体和关系数量
                doc_entity_counts = {}
                async for doc in entities_collection.aggregate([
                    {"$match": {"is_valid": True}},
                    {"$group": {"_id": "$source_document_id", "count": {"$sum": 1}}}
                ]):
                    doc_entity_counts[doc["_id"]] = doc["count"]
                
                # 计算平均值
                avg_entities = sum(doc_entity_counts.values()) / len(doc_entity_counts) if doc_entity_counts else 0
                
                doc_relation_counts = {}
                async for doc in relations_collection.aggregate([
                    {"$match": {"is_valid": True}},
                    {"$group": {"_id": "$source_document_id", "count": {"$sum": 1}}}
                ]):
                    doc_relation_counts[doc["_id"]] = doc["count"]
                
                avg_relations = sum(doc_relation_counts.values()) / len(doc_relation_counts) if doc_relation_counts else 0
                
                return KnowledgeStats(
                    total_entities=total_entities,
                    total_relations=total_relations,
                    entity_types=entity_types,
                    relation_types=relation_types,
                    avg_entities_per_document=avg_entities,
                    avg_relations_per_document=avg_relations
                )
            else:
                # MongoDB连接不可用，返回空统计
                return KnowledgeStats(
                    total_entities=0,
                    total_relations=0,
                    entity_types={},
                    relation_types={},
                    avg_entities_per_document=0,
                    avg_relations_per_document=0
                )
        except Exception as e:
            self.logger.error(f"获取知识统计失败: {str(e)}")
            raise
    
    async def find_entity_path(self, source_id: str, target_id: str, max_depth: int = 3) -> Optional[KnowledgeGraphPath]:
        """查找两个实体之间的路径"""
        try:
            # 使用db_service访问Neo4j
            neo4j_driver = self.get_neo4j_driver()
            
            # 使用Neo4j查找路径
            async with neo4j_driver.session() as session:
                result = await session.run(
                    "MATCH path = shortestPath((s:Entity {id: $source_id})-[*1..$max_depth]->(t:Entity {id: $target_id})) "
                    "RETURN path LIMIT 1",
                    source_id=source_id,
                    target_id=target_id,
                    max_depth=max_depth
                )
                
                path_record = await result.single()
                if not path_record:
                    return None
                
                path = path_record["path"]
                node_ids = []
                relationship_ids = []
                path_sequence = []
                
                # 提取节点和关系ID
                for rel in path.relationships:
                    source_id = rel.start_node["id"]
                    target_id = rel.end_node["id"]
                    rel_id = rel["id"] if "id" in rel else str(uuid.uuid4())
                    path_sequence.append((source_id, rel_id, target_id))
                    node_ids.extend([source_id, target_id])
                    relationship_ids.append(rel_id)
                
                # 查询完整实体信息
                entities = []
                for node_id in set(node_ids):
                    entity = await self.find_entity_by_id(node_id)
                    if entity:
                        entities.append(entity)
                
                # 查询完整关系信息
                relations = []
                for rel_id in set(relationship_ids):
                    relation = await self.find_relation_by_id(rel_id)
                    if relation:
                        relations.append(relation)
                
                return KnowledgeGraphPath(
                    entities=entities,
                    relations=relations,
                    path_sequence=path_sequence
                )
        except Exception as e:
            self.logger.error(f"查找实体路径失败: {str(e)}")
            raise
    
    async def find_shortest_path(self, source_id: str, target_id: str, max_depth: int = 5) -> Optional[Dict[str, Any]]:
        """查找两个实体之间的最短路径"""
        try:
            self.logger.info(f"查找最短路径: {source_id} -> {target_id}, 最大深度: {max_depth}")
            
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is None:
                return None
            
            async with neo4j_driver.session() as session:
                # 使用Dijkstra算法查找最短路径
                result = await session.run(
                    """
                    MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
                    CALL gds.shortestPath.dijkstra.stream('entity_relation_graph', {
                        sourceNode: source,
                        targetNode: target,
                        relationshipWeightProperty: 'confidence_score'
                    })
                    YIELD path
                    RETURN path
                    LIMIT 1
                    """,
                    source_id=source_id,
                    target_id=target_id
                )
                
                path_record = await result.single()
                if not path_record:
                    return None
                
                path = path_record["path"]
                
                # 构建路径结果
                path_result = {
                    "source_id": source_id,
                    "target_id": target_id,
                    "nodes": [],
                    "relationships": [],
                    "path": []
                }
                
                # 提取节点信息
                for node in path.nodes:
                    path_result["nodes"].append({
                        "id": node["id"],
                        "name": node["name"],
                        "type": node["type"]
                    })
                
                # 提取关系信息
                for rel in path.relationships:
                    path_result["relationships"].append({
                        "id": rel["id"] if "id" in rel else str(uuid.uuid4()),
                        "type": rel.type,
                        "source_id": rel.start_node["id"],
                        "target_id": rel.end_node["id"],
                        "confidence_score": rel["confidence_score"] if "confidence_score" in rel else 1.0
                    })
                    
                    # 构建路径序列
                    path_result["path"].append({
                        "source_id": rel.start_node["id"],
                        "target_id": rel.end_node["id"],
                        "relation_type": rel.type
                    })
                
                return path_result
        except Exception as e:
            self.logger.error(f"查找最短路径失败: {str(e)}")
            return None
    
    async def detect_communities(self, algorithm: str = "louvain", weight_property: str = "confidence_score") -> Dict[str, Any]:
        """检测社区"""
        try:
            self.logger.info(f"使用{algorithm}算法检测社区")
            
            neo4j_driver = self.get_neo4j_driver()
            if neo4j_driver is None:
                return None
            
            async with neo4j_driver.session() as session:
                # 创建图投影
                await session.run(
                    '''CALL gds.graph.project('entity_relation_graph', 'Entity', 'RELATION', {
                        relationshipProperties: $weight_property
                    })''',
                    weight_property=weight_property
                )
                
                # 运行社区检测算法
                if algorithm.lower() == "louvain":
                    result = await session.run(
                        """
                        CALL gds.louvain.stream('entity_relation_graph', {
                            relationshipWeightProperty: $weight_property
                        })
                        YIELD nodeId, communityId
                        MATCH (n) WHERE id(n) = nodeId
                        RETURN n.id AS entity_id, communityId AS community_id
                        """,
                        weight_property=weight_property
                    )
                elif algorithm.lower() == "leiden":
                    result = await session.run(
                        """
                        CALL gds.leiden.stream('entity_relation_graph', {
                            relationshipWeightProperty: $weight_property
                        })
                        YIELD nodeId, communityId
                        MATCH (n) WHERE id(n) = nodeId
                        RETURN n.id AS entity_id, communityId AS community_id
                        """,
                        weight_property=weight_property
                    )
                else:
                    self.logger.error(f"不支持的社区检测算法: {algorithm}")
                    return None
                
                # 处理结果
                communities = {}
                async for record in result:
                    entity_id = record["entity_id"]
                    community_id = record["community_id"]
                    
                    if community_id not in communities:
                        communities[community_id] = []
                    communities[community_id].append(entity_id)
                
                return {
                    "algorithm": algorithm,
                    "communities": communities,
                    "community_count": len(communities)
                }
        except Exception as e:
            self.logger.error(f"社区检测失败: {str(e)}")
            return None
    
    async def get_visualization_data(self, query: Optional[KnowledgeGraphQueryAdvanced] = None) -> GraphVisualization:
        """获取知识图谱可视化数据"""
        try:
            # 获取统计信息
            stats = await self.get_knowledge_stats()
            
            # 获取实体和关系数据
            entities = []
            relations = []
            
            if query:
                # 实现根据查询条件获取实体和关系
                # 这里简化实现，实际应该调用更复杂的查询方法
                pass
            else:
                # 使用MongoDB获取最新的50个实体
                mongodb = await db_service.get_mongodb()
                if mongodb is not None:
                    entities_collection = mongodb.entities
                    relations_collection = mongodb.relations
                    
                    # 获取最新的50个实体
                    cursor = entities_collection.find({"is_valid": True}).sort("created_at", -1).limit(50)
                    entities = [Entity(**doc) async for doc in cursor]
                    
                    # 获取相关关系
                    if entities:
                        entity_ids = [e.id for e in entities]
                        relations_cursor = relations_collection.find({
                            "is_valid": True,
                            "$or": [
                                {"source_entity_id": {"$in": entity_ids}},
                                {"target_entity_id": {"$in": entity_ids}}
                            ]
                        })
                        relations = [Relation(**doc) async for doc in relations_cursor]
            
            # 转换为可视化数据
            nodes = []
            for entity in entities:
                node = EntityNode(
                    id=entity.id,
                    label=entity.name,
                    type=entity.type,
                    properties=entity.properties or {},
                    size=1,
                    color=self._get_node_color(entity.type)
                )
                nodes.append(node)
            
            edges = []
            for relation in relations:
                edge = RelationEdge(
                    id=relation.id,
                    source=relation.source_entity_id,
                    target=relation.target_entity_id,
                    label=relation.type,
                    properties=relation.properties or {},
                    width=1.0,
                    color="#666"
                )
                edges.append(edge)
            
            return GraphVisualization(
                nodes=nodes,
                edges=edges,
                layout="force",
                statistics=stats
            )
        except Exception as e:
            self.logger.error(f"获取可视化数据失败: {str(e)}")
            raise
    
    def _get_node_color(self, entity_type: str) -> str:
        """根据实体类型返回颜色"""
        color_map = {
            "Person": "#FF6B6B",
            "Organization": "#4ECDC4",
            "Location": "#45B7D1",
            "Event": "#FED766",
            "Concept": "#96CEB4",
            "Object": "#FFEAA7",
            "Date": "#DDA0DD",
            "Time": "#98D8C8",
            "Quantity": "#F7DC6F"
        }
        return color_map.get(entity_type, "#BDC3C7")
    
    async def update_document_status(self, document_id: str, status: str, processing_details: Optional[Dict] = None, entities_count: Optional[int] = None, relations_count: Optional[int] = None) -> bool:
        """更新文档处理状态"""
        try:
            # 获取MongoDB连接
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                # 更新文档状态
                documents_collection = mongodb.documents
                update_data = {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
                
                # 如果提供了处理详情，也更新它
                if processing_details:
                    update_data["processing_details"] = processing_details
                
                # 如果提供了实体和关系数量，更新到顶层字段（重要！）
                if entities_count is not None:
                    update_data["entities_count"] = entities_count
                if relations_count is not None:
                    update_data["relations_count"] = relations_count
                
                # 执行更新
                result = await documents_collection.update_one(
                    {"id": document_id},
                    {"$set": update_data}
                )
                
                logger.info(f"更新文档状态 - 文档ID: {document_id}, 状态: {status}, "
                           f"实体: {entities_count}, 关系: {relations_count}, "
                           f"更新结果: {result.modified_count} 条记录被更新")
                return result.modified_count > 0
            
            logger.warning(f"无法更新文档状态，MongoDB连接不可用")
            return False
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {str(e)}")
            raise