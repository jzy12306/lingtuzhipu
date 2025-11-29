from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class IndustryTemplateBase(BaseModel):
    """行业模板基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    industry: str = Field(..., description="所属行业")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    is_active: bool = Field(default=True, description="是否激活")
    config: Dict[str, Any] = Field(default_factory=dict, description="模板配置")


class IndustryTemplateCreate(IndustryTemplateBase):
    """行业模板创建模型"""
    pass


class IndustryTemplateUpdate(BaseModel):
    """行业模板更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class IndustryTemplateResponse(IndustryTemplateBase):
    """行业模板响应模型"""
    id: str = Field(..., description="模板ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class IndustryTemplate(IndustryTemplateResponse):
    """行业模板数据库模型"""
    class Config:
        from_attributes = True