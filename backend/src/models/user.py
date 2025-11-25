from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否为超级用户")
    is_admin: bool = Field(default=False, description="是否为管理员")
    email_verified: bool = Field(default=False, description="邮箱是否已验证")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8, description="密码")


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_superuser: Optional[bool] = None
    email_verified: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")


class User(UserResponse):
    """用户数据库模型"""
    hashed_password: Optional[str] = Field(None, description="哈希后的密码")


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[str] = None


class UserStats(BaseModel):
    """用户统计信息模型"""
    total_users: int
    active_users: int
    admin_users: int
    recent_users: int  # 最近30天注册的用户数


class VerificationCode(BaseModel):
    """验证码模型"""
    email: EmailStr
    code: str
    created_at: datetime
    expires_at: datetime