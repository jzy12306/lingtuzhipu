from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


class EntityBase(BaseModel):
    """实体基础模型"""
    name: str = Field(..., min_length=1, max_length=255, description="实体名称")
    type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(default="", description="实体描述")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="实体属性")
    source_document_id: str = Field(..., description="来源文档ID")
    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")


class EntityCreate(EntityBase):
    """实体创建模型"""
    pass


class EntityUpdate(BaseModel):
    """实体更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    is_valid: Optional[bool] = None


class EntityResponse(EntityBase):
    """实体响应模型"""
    id: str = Field(..., description="实体ID")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度分数")
    is_valid: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class Entity(EntityResponse):
    """实体数据库模型"""
    class Config:
        from_attributes = True


class RelationBase(BaseModel):
    """关系基础模型"""
    source_entity_id: str = Field(..., description="源实体ID")
    target_entity_id: str = Field(..., description="目标实体ID")
    source_entity_name: str = Field(..., description="源实体名称")
    target_entity_name: str = Field(..., description="目标实体名称")
    type: str = Field(..., description="关系类型")
    description: Optional[str] = Field(default="", description="关系描述")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="关系属性")
    source_document_id: str = Field(..., description="来源文档ID")
    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")


class RelationCreate(RelationBase):
    """关系创建模型"""
    pass


class RelationUpdate(BaseModel):
    """关系更新模型"""
    type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    is_valid: Optional[bool] = None


class RelationResponse(RelationBase):
    """关系响应模型"""
    id: str = Field(..., description="关系ID")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度分数")
    is_valid: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class Relation(RelationResponse):
    """关系数据库模型"""
    class Config:
        from_attributes = True


class KnowledgeGraphQuery(BaseModel):
    """知识图谱查询模型"""
    query: str = Field(..., description="查询语句")
    query_type: str = Field(default="natural_language", description="查询类型")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="查询参数")
    max_results: int = Field(default=50, ge=1, le=1000, description="最大结果数")


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应模型"""
    query_id: str = Field(..., description="查询ID")
    entities: List[EntityResponse] = Field(default_factory=list, description="查询结果实体")
    relations: List[RelationResponse] = Field(default_factory=list, description="查询结果关系")
    explanation: Optional[str] = Field(None, description="结果解释")
    execution_time_ms: float = Field(..., description="执行时间(毫秒)")
    total_results: int = Field(..., description="总结果数")
    
    class Config:
        from_attributes = True


class KnowledgeConflict(BaseModel):
    """知识冲突模型"""
    conflict_id: str = Field(..., description="冲突ID")
    type: str = Field(..., description="冲突类型")
    entities: List[EntityResponse] = Field(default_factory=list, description="冲突相关实体")
    relations: List[RelationResponse] = Field(default_factory=list, description="冲突相关关系")
    description: str = Field(..., description="冲突描述")
    severity: str = Field(default="medium", description="严重程度")  # low, medium, high
    suggested_resolution: Optional[str] = Field(None, description="建议解决方案")
    
    class Config:
        from_attributes = True


class KnowledgeStats(BaseModel):
    """知识图谱统计信息模型"""
    total_entities: int
    total_relations: int
    entity_types: Dict[str, int]
    relation_types: Dict[str, int]
    avg_entities_per_document: float
    avg_relations_per_document: float


class KnowledgeGraphPath(BaseModel):
    """知识图谱路径模型"""
    entities: List[EntityResponse]
    relations: List[RelationResponse]
    path_sequence: List[Tuple[str, str, str]]  # (source_id, relation_id, target_id)


class EntityNode(BaseModel):
    """实体节点模型（用于可视化）"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    size: int = Field(default=1, description="节点大小")
    color: Optional[str] = None


class RelationEdge(BaseModel):
    """关系边模型（用于可视化）"""
    id: str
    source: str
    target: str
    label: str
    properties: Dict[str, Any]
    width: float = Field(default=1.0, description="边宽度")
    color: Optional[str] = None


class GraphVisualization(BaseModel):
    """图谱可视化模型"""
    nodes: List[EntityNode]
    edges: List[RelationEdge]
    layout: Optional[str] = Field(default="force", description="布局算法")
    statistics: KnowledgeStats


class KnowledgeGraphQueryAdvanced(BaseModel):
    """高级知识图谱查询模型"""
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    relation_type: Optional[str] = None
    source_entity: Optional[str] = None
    target_entity: Optional[str] = None
    depth: int = Field(default=2, ge=1, le=5, description="查询深度")
    limit: int = Field(default=50, ge=1, le=100, description="返回结果数量限制")
    document_ids: Optional[List[str]] = None
    include_invalid: bool = Field(default=False, description="是否包含无效实体/关系")