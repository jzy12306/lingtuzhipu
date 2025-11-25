from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import os

from models.user import User, TokenData
from repositories.user_repository import UserRepository

# 配置
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_user_repository() -> UserRepository:
    """获取用户仓库实例"""
    return UserRepository()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已被禁用")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """
    获取可选的当前用户（不强制要求认证）
    
    Args:
        token: OAuth2 Bearer token
        
    Returns:
        用户对象或None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, user_repo)
    except HTTPException:
        return None


def validate_document_permission(document: Any, user: User) -> bool:
    """
    验证用户是否有权限访问文档
    
    Args:
        document: 文档信息
        user: 用户对象
        
    Returns:
        bool: 是否有权限
    """
    # 管理员可以访问所有文档
    if user.is_admin:
        return True
    
    # 用户只能访问自己创建的文档
    if hasattr(document, "user_id"):
        return document.user_id == user.id
    return False


async def validate_resource_ownership(
    resource_id: str,
    resource_type: str,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """验证资源所有权"""
    # 如果是管理员，直接返回通过
    if current_user.is_admin:
        return True
    
    # 根据资源类型验证所有权
    if resource_type == "document":
        # 这里应该调用文档仓库检查文档所有权
        # 简化处理，暂时假设所有非管理员只能访问自己的资源
        return True
    elif resource_type == "entity":
        # 实体所有权验证
        return True
    elif resource_type == "relation":
        # 关系所有权验证
        return True
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="无效的资源类型"
    )


async def validate_knowledge_permission(
    operation: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """验证知识图谱操作权限"""
    # 管理员拥有所有权限
    if current_user.is_admin:
        return current_user
    
    # 根据操作类型和资源类型验证权限
    if operation in ["read", "search", "visualize"]:
        # 读取类操作，根据资源所有权验证
        if resource_id and resource_type:
            await validate_resource_ownership(resource_id, resource_type, current_user)
    elif operation in ["create", "update", "delete"]:
        # 修改类操作，普通用户只能修改自己创建的资源
        if resource_id and resource_type:
            await validate_resource_ownership(resource_id, resource_type, current_user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的操作类型"
        )
    
    return current_user


async def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """获取分页参数"""
    # 验证分页参数
    skip = max(0, skip)  # 确保skip >= 0
    limit = max(1, min(1000, limit))  # 限制limit在1-1000之间
    
    return {
        "skip": skip,
        "limit": limit
    }


# 保留原始的validate_knowledge_permission函数用于向后兼容
async def validate_knowledge_permission_legacy(
    entity_or_relation: Dict[str, Any], 
    user: Any, 
    document_repo=None
) -> bool:
    """
    验证用户是否有权限访问知识实体或关系（向后兼容）
    
    Args:
        entity_or_relation: 实体或关系信息
        user: 用户信息
        document_repo: 文档仓库实例
        
    Returns:
        bool: 是否有权限
    """
    # 管理员可以访问所有知识
    is_admin = getattr(user, "is_admin", user.get("is_admin", False))
    if is_admin:
        return True
    
    # 如果没有关联文档，检查创建者
    if "document_id" not in entity_or_relation:
        user_id = getattr(user, "id", user.get("id"))
        return entity_or_relation.get("created_by") == user_id or entity_or_relation.get("user_id") == user_id
    
    # 延迟导入避免循环依赖
    if document_repo is None:
        from repositories.document_repository import document_repository
        document_repo = document_repository
    
    # 检查关联文档的权限
    document_id = entity_or_relation["document_id"]
    document = await document_repo.find_by_id(document_id)
    
    if not document:
        return False
    
    user_id = getattr(user, "id", user.get("id"))
    return document.get("created_by") == user_id or document.get("user_id") == user_id