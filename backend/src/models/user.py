# 从schemas导入基础模型以避免重复
from ..schemas.user import (
    User as BaseUser, UserCreate, UserUpdate, UserResponse, 
    UserLogin, TokenResponse, TokenData
)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class User(BaseUser):
    """用户数据库模型"""
    hashed_password: Optional[str] = Field(None, description="哈希后的密码")
    location: Optional[str] = Field(None, description="登录地点")
    is_current: bool = Field(default=False, description="是否为当前登录")
    logout_time: Optional[datetime] = Field(None, description="登出时间")


class LoginHistoryResponse(BaseModel):
    """登录历史响应模型"""
    id: str
    login_time: datetime
    ip_address: str
    user_agent: str
    device_info: Optional[str]
    location: Optional[str]
    is_current: bool
    logout_time: Optional[datetime]