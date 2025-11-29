from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BusinessRuleBase(BaseModel):
    """业务规则基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    is_active: bool = Field(default=True, description="是否激活")
    config: Dict[str, Any] = Field(default_factory=dict, description="规则配置")


class BusinessRuleCreate(BusinessRuleBase):
    """业务规则创建模型"""
    pass


class BusinessRuleUpdate(BaseModel):
    """业务规则更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class BusinessRuleResponse(BusinessRuleBase):
    """业务规则响应模型"""
    id: str = Field(..., description="规则ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class BusinessRule(BusinessRuleResponse):
    """业务规则数据库模型"""
    pass