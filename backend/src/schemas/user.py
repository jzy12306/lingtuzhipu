from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from enum import Enum
import re
from datetime import datetime


# 用户角色枚举
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


# 用户创建模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    
    @validator('username')
    def username_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和中文')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        # 简单的密码强度检查
        if not any(c.isupper() for c in v) and not any(c.islower() for c in v):
            raise ValueError('密码必须包含大小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


# 用户更新模型
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(None, min_length=6, description="密码")
    role: Optional[UserRole] = Field(None, description="用户角色")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v


# 用户响应模型
class UserResponse(BaseModel):
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    is_admin: bool = Field(default=False, description="是否为管理员")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        from_attributes = True  # Pydantic V2 语法，允许从ORM对象创建


# 用户登录模型
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


# Token响应模型
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


# Token数据模型（用于JWT解码）
class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


# 验证码模型
class VerificationCode(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., description="验证码")
    expires_at: datetime = Field(..., description="过期时间")


# MFA验证请求模型
class MfaVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, description="MFA验证码")


# User模型（数据库模型的Pydantic表示）
class User(BaseModel):
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    password_hash: Optional[str] = Field(None, description="密码哈希值")
    hashed_password: Optional[str] = Field(None, description="密码哈希值（兼容字段）")
    password: Optional[str] = Field(None, description="密码（兼容字段）")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    is_admin: bool = Field(default=False, description="是否为管理员")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    is_active: bool = Field(default=True, description="是否活跃")
    
    class Config:
        from_attributes = True  # Pydantic V2 语法，允许从ORM对象创建
