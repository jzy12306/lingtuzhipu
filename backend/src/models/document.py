from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"  # 已上传
    PROCESSING = "processing"  # 处理中
    OCR_PROCESSING = "ocr_processing"  # OCR识别中
    KNOWLEDGE_EXTRACTING = "knowledge_extracting"  # 知识提取中
    PROCESSED = "processed"  # 已处理
    FAILED = "failed"  # 处理失败


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    description: Optional[str] = Field(None, max_length=2000, description="文档描述")
    document_type: DocumentType = Field(..., description="文档类型")
    filename: str = Field(..., description="文件名")
    industry: Optional[str] = Field(None, description="所属行业")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    file_name: Optional[str] = None  # 兼容字段
    file_type: Optional[str] = None  # 兼容字段


class DocumentCreate(DocumentBase):
    """文档创建模型"""
    content: Optional[str] = Field(None, description="文档内容")
    file_path: Optional[str] = Field(None, description="文件路径")


class DocumentUpdate(BaseModel):
    """文档更新模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="上传用户ID")
    status: DocumentStatus = Field(..., description="文档状态")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: int = Field(..., description="文件大小(字节)")
    entities_count: int = Field(default=0, description="提取的实体数量")
    relations_count: int = Field(default=0, description="提取的关系数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")
    processed: bool = False  # 兼容字段
    embedding_status: str = "none"  # 兼容字段
    ocr_status: Optional[str] = Field(None, description="OCR识别状态")
    ocr_result: Optional[Dict[str, Any]] = Field(None, description="OCR识别结果")
    ocr_confidence: Optional[float] = Field(None, description="OCR识别置信度")
    ocr_error: Optional[str] = Field(None, description="OCR识别错误信息")
    
    class Config:
        from_attributes = True


class Document(DocumentResponse):
    """文档数据库模型"""
    content_hash: str = Field(..., description="内容哈希值")
    content: Optional[str] = None  # 文档内容
    processing_error: Optional[str] = None  # 处理错误
    embedding_id: Optional[str] = None  # 嵌入ID
    ocr_status: Optional[str] = Field(None, description="OCR识别状态")
    ocr_result: Optional[Dict[str, Any]] = Field(None, description="OCR识别结果")
    ocr_confidence: Optional[float] = Field(None, description="OCR识别置信度")
    ocr_error: Optional[str] = Field(None, description="OCR识别错误信息")
    
    class Config:
        from_attributes = True


class DocumentContent(BaseModel):
    """文档内容模型"""
    id: str
    content: str
    title: str


class DocumentQuery(BaseModel):
    """文档查询模型"""
    query: str = Field(..., description="查询语句")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数量")
    user_id: Optional[str] = None
    metadata_filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentStats(BaseModel):
    """文档统计信息模型"""
    total_documents: int
    processed_documents: int
    unprocessed_documents: int
    total_size: int  # 总大小（字节）
    avg_size: float  # 平均大小（字节）
    document_types: Dict[str, int]  # 按类型统计


class ChunkBase(BaseModel):
    """文档块基础模型"""
    document_id: str
    text: str
    chunk_number: int
    start_index: int
    end_index: int
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Chunk(ChunkBase):
    """文档块响应模型"""
    id: str
    created_at: datetime
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True