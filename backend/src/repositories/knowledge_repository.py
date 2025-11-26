import logging
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
        if mongo_client:
            self.entities_collection = mongo_client.kimi.entities
            self.relations_collection = mongo_client.kimi.relations
        self.logger = logger.getChild("KnowledgeRepository")
    
    async def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """根据查询搜索实体
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            实体列表
        """
        try:
            driver = await self.get_neo4j_driver()
            
            # 使用Neo4j的全文搜索或模糊匹配查找实体
            search_query = """
            MATCH (e:Entity)
            WHERE e.is_valid = true AND 
                  (e.name CONTAINS $query OR e.type CONTAINS $query)
            RETURN e
            LIMIT 50
            """
            
            async with driver.session() as session:
                result = await session.run(search_query, query=query)
                entities = []
                
                async for record in result:
                    entity_node = record["e"]
                    entity = {
                        "id": entity_node.get("id"),
                        "name": entity_node.get("name"),
                        "type": entity_node.get("type"),
                        "confidence_score": entity_node.get("confidence_score"),
                        "source_document_id": entity_node.get("source_document_id")
                    }
                    entities.append(entity)
                
                return entities
                
        except Exception as e:
            self.logger.error(f"搜索实体时发生错误: {str(e)}")
            raise
    
    async def get_neo4j_driver(self):
        """获取Neo4j驱动"""
        return await db_service.get_neo4j_driver()
    
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
            
            # 准备Neo4j查询
            query = """
            CREATE (e:Entity {id: $id, name: $name, type: $type, 
                          confidence_score: $confidence_score, 
                          is_valid: $is_valid, 
                          source_document_id: $source_document_id,
                          created_at: $created_at, 
                          updated_at: $updated_at})
            SET e += $properties
            RETURN e
            """
            
            # 执行查询
            driver = await self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(
                    query,
                    id=entity_data["id"],
                    name=entity_data["name"],
                    type=entity_data["type"],
                    confidence_score=entity_data["confidence_score"],
                    is_valid=entity_data["is_valid"],
                    source_document_id=entity_data["source_document_id"],
                    created_at=entity_data["created_at"].isoformat(),
                    updated_at=entity_data["updated_at"].isoformat(),
                    properties=properties
                )
                
                record = await result.single()
                if record:
                    # 重建实体数据
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
            
            raise ValueError("创建实体失败")
        except Exception as e:
            self.logger.error(f"创建实体失败: {str(e)}")
            raise
    
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
            
            # 从properties中提取属性
            properties = relation_data.pop("properties", {})
            
            # 准备Neo4j查询
            query = """
            MATCH (s:Entity {id: $source_entity_id})
            MATCH (t:Entity {id: $target_entity_id})
            CREATE (s)-[r:RELATION {id: $id, type: $type, 
                                  confidence_score: $confidence_score,
                                  is_valid: $is_valid,
                                  source_document_id: $source_document_id,
                                  created_at: $created_at,
                                  updated_at: $updated_at}]->(t)
            SET r += $properties
            RETURN r
            """
            
            # 执行查询
            driver = await self.get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run(
                    query,
                    source_entity_id=relation_data["source_entity_id"],
                    target_entity_id=relation_data["target_entity_id"],
                    id=relation_data["id"],
                    type=relation_data["type"],
                    confidence_score=relation_data["confidence_score"],
                    is_valid=relation_data["is_valid"],
                    source_document_id=relation_data["source_document_id"],
                    created_at=relation_data["created_at"].isoformat(),
                    updated_at=relation_data["updated_at"].isoformat(),
                    properties=properties
                )
                
                record = await result.single()
                if record:
                    # 重建关系数据
                    relation_edge = record["r"]
                    relation_dict = {
                        "id": relation_edge["id"],
                        "source_entity_id": relation_data["source_entity_id"],
                        "target_entity_id": relation_data["target_entity_id"],
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
            
            raise ValueError("创建关系失败")
        except Exception as e:
            self.logger.error(f"创建关系失败: {str(e)}")
            raise
    
    async def find_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """根据ID查找实体"""
        try:
            query = """
            MATCH (e:Entity {id: $id})
            RETURN e
            """
            
            driver = await self.get_neo4j_driver()
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
            query = """
            MATCH ()-[r:RELATION {id: $id}]->()
            RETURN r, startNode(r).id as source_id, endNode(r).id as target_id
            """
            
            driver = await self.get_neo4j_driver()
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
            query = """
            MATCH (e:Entity {source_document_id: $document_id})
            RETURN e
            """
            
            driver = await self.get_neo4j_driver()
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
            
            driver = await self.get_neo4j_driver()
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
            query = """
            MATCH ()-[r:RELATION {source_document_id: $document_id}]->()
            RETURN r, startNode(r).id as source_id, endNode(r).id as target_id
            """
            
            driver = await self.get_neo4j_driver()
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
            driver = await self.get_neo4j_driver()
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
            
            driver = await self.get_neo4j_driver()
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
            entities_collection = db_service.mongo_client.kimi.entities
            relations_collection = db_service.mongo_client.kimi.relations
            
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
        except Exception as e:
            self.logger.error(f"获取知识统计失败: {str(e)}")
            raise
    
    async def find_entity_path(self, source_id: str, target_id: str, max_depth: int = 3) -> Optional[KnowledgeGraphPath]:
        """查找两个实体之间的路径"""
        try:
            # 使用db_service访问Neo4j
            neo4j_driver = await self.get_neo4j_driver()
            
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
                # 默认获取最新的50个实体
                entities = await self.find_entities(limit=50, sort_by="created_at", sort_order="desc")
                
                # 获取相关关系
                entity_ids = [e.id for e in entities]
                relations = await self.find_relations_by_entity_ids(entity_ids)
            
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
    
    async def update_document_status(self, document_id: str, status: str, processing_details: Optional[Dict] = None) -> bool:
        """更新文档处理状态"""
        try:
            # 这里需要实现文档状态更新的逻辑
            # 由于我们没有看到 DocumentRepository，这里先实现一个简单的版本
            logger.info(f"更新文档状态 - 文档ID: {document_id}, 状态: {status}")
            
            # 在实际实现中，这里应该更新文档的状态
            # 例如：await self.document_repository.update_document_status(document_id, status, processing_details)
            
            return True
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {str(e)}")
            raise