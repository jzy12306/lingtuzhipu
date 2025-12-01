from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    max_concurrent: int = Field(default=100, ge=1, le=1000, description="最大并发数")
    timeout_seconds: int = Field(default=30, ge=5, le=3600, description="超时时间(秒)")
    cache_size_mb: int = Field(default=512, ge=64, le=8192, description="缓存大小(MB)")
    enable_compression: bool = Field(default=True, description="是否启用压缩")
    max_concurrent_llm_calls: int = Field(default=5, ge=1, le=50, description="LLM最大并发调用数")
    enable_response_caching: bool = Field(default=True, description="是否启用响应缓存")


class SystemConfigCreate(SystemConfigBase):
    """系统配置创建模型"""
    pass


class SystemConfigUpdate(BaseModel):
    """系统配置更新模型"""
    max_concurrent: Optional[int] = Field(None, ge=1, le=1000)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=3600)
    cache_size_mb: Optional[int] = Field(None, ge=64, le=8192)
    enable_compression: Optional[bool] = None
    max_concurrent_llm_calls: Optional[int] = Field(None, ge=1, le=50)
    enable_response_caching: Optional[bool] = None


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    id: str = Field(..., description="配置ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class SystemConfig(SystemConfigResponse):
    """系统配置数据库模型"""
    pass
