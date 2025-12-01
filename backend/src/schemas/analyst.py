from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


from enum import Enum

# 查询复杂度枚举
class QueryComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


# 分析类型枚举
class AnalysisType(str, Enum):
    COMPREHENSIVE = "comprehensive"
    SUMMARIZATION = "summarization"
    ENTITY_RECOGNITION = "entity_recognition"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TOPIC_MODELING = "topic_modeling"


# 查询请求模型
class QueryRequest(BaseModel):
    query: str = Field(..., description="自然语言查询", min_length=1, max_length=2000)
    document_ids: Optional[List[str]] = Field(default_factory=list, description="相关文档ID列表")
    include_code: bool = Field(default=True, description="是否包含生成的代码")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('查询不能为空')
        return v


# 查询响应模型
class QueryResponse(BaseModel):
    id: str = Field(..., description="查询ID")
    query: str = Field(..., description="原始查询")
    summary: str = Field(..., description="查询结果摘要")
    detailed_answer: str = Field(..., description="详细回答")
    generated_code: Optional[str] = Field(None, description="生成的代码")
    visualization_data: Optional[Dict[str, Any]] = Field(None, description="可视化数据")
    related_entities: List[Dict[str, Any]] = Field(default_factory=list, description="相关实体")
    related_relationships: List[Dict[str, Any]] = Field(default_factory=list, description="相关关系")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度分数")
    execution_time: float = Field(..., description="执行时间（秒）")
    complexity: QueryComplexity = Field(..., description="查询复杂度")
    timestamp: str = Field(..., description="时间戳")


# 查询历史记录模型
class QueryHistory(BaseModel):
    id: str = Field(..., description="历史记录ID")
    query: str = Field(..., description="查询内容")
    result_summary: str = Field(..., description="结果摘要")
    timestamp: str = Field(..., description="查询时间")
    execution_time: float = Field(..., description="执行时间（秒）")
    complexity: QueryComplexity = Field(..., description="查询复杂度")


# 代码执行请求模型
class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="要执行的代码", min_length=1, max_length=10000)
    language: str = Field(default="python", description="编程语言")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")
    
    @validator('language')
    def validate_language(cls, v):
        supported_languages = ['python']
        if v.lower() not in supported_languages:
            raise ValueError(f"不支持的语言。支持的语言: {', '.join(supported_languages)}")
        return v


# 代码执行结果模型
class CodeExecutionResult(BaseModel):
    success: bool = Field(..., description="执行是否成功")
    output: str = Field(..., description="执行输出")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间（秒）")
    language: str = Field(..., description="使用的编程语言")


# 分析请求模型
class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType = Field(default=AnalysisType.COMPREHENSIVE, description="分析类型")
    limit: Optional[int] = Field(default=1000, ge=1, le=10000, description="返回结果限制")
    entity_types: Optional[List[str]] = Field(default_factory=list, description="实体类型过滤")
    relationship_types: Optional[List[str]] = Field(default_factory=list, description="关系类型过滤")


# 分析结果模型
class AnalysisResult(BaseModel):
    document_id: str = Field(..., description="文档ID")
    document_title: str = Field(..., description="文档标题")
    analysis_summary: str = Field(..., description="分析摘要")
    key_findings: List[str] = Field(default_factory=list, description="关键发现")
    entities_identified: List[Dict[str, Any]] = Field(default_factory=list, description="识别的实体")
    relationships_identified: List[Dict[str, Any]] = Field(default_factory=list, description="识别的关系")
    sentiment: Optional[Dict[str, float]] = Field(None, description="情感分析结果")
    topics: List[Dict[str, Any]] = Field(default_factory=list, description="主题")
    recommendations: List[str] = Field(default_factory=list, description="建议")


# 查询建议模型
class SuggestionItem(BaseModel):
    text: str = Field(..., description="建议文本")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性分数")
    category: Optional[str] = Field(None, description="建议类别")


# 实体详情模型
class EntityDetail(BaseModel):
    id: str = Field(..., description="实体ID")
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实体属性")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="关联关系")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度")


# 知识图谱统计模型
class GraphStats(BaseModel):
    nodes_count: int = Field(..., description="节点数量")
    edges_count: int = Field(..., description="边数量")
    entity_types_count: Dict[str, int] = Field(default_factory=dict, description="各类型实体数量")
    relationship_types_count: Dict[str, int] = Field(default_factory=dict, description="各类型关系数量")
    creation_time: datetime = Field(..., description="创建时间")
    last_updated: datetime = Field(..., description="最后更新时间")


# 代码安全验证结果
class CodeSafetyResult(BaseModel):
    is_safe: bool = Field(..., description="代码是否安全")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="发现的安全问题")
    allowed_operations: List[str] = Field(default_factory=list, description="允许的操作")
    risk_level: str = Field(default="low", description="风险等级")


# 批量查询请求
class BatchQueryRequest(BaseModel):
    queries: List[str] = Field(..., description="查询列表", min_items=1, max_items=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="每个查询的超时时间")


# 批量查询响应
class BatchQueryResponse(BaseModel):
    queries: List[Dict[str, Any]] = Field(..., description="查询结果列表")
    total_processed: int = Field(..., description="处理的查询总数")
    successful: int = Field(..., description="成功的查询数")
    failed: int = Field(..., description="失败的查询数")
    total_time: float = Field(..., description="总处理时间")