from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import os

from src.repositories.user_repository import user_repository
from src.services.auth_service import auth_service

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    获取当前认证用户
    
    Args:
        token: OAuth2 Bearer token
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 当token无效或用户不存在时
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码token
        payload = auth_service.decode_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 获取用户信息
    user = await user_repository.find_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    # 检查用户是否被禁用
    if user.get("is_disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 返回用户信息
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"]
    }


async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    获取管理员用户（验证管理员权限）
    
    Args:
        current_user: 当前认证用户信息
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 当用户不是管理员时
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """
    获取可选的当前用户（不强制要求认证）
    
    Args:
        token: OAuth2 Bearer token
        
    Returns:
        用户信息字典或None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def validate_document_permission(document: Dict[str, Any], user: Dict[str, Any]) -> bool:
    """
    验证用户是否有权限访问文档
    
    Args:
        document: 文档信息
        user: 用户信息
        
    Returns:
        bool: 是否有权限
    """
    # 管理员可以访问所有文档
    if user.get("is_admin", False):
        return True
    
    # 用户只能访问自己创建的文档
    return document.get("created_by") == user["id"]


async def validate_knowledge_permission(entity_or_relation: Dict[str, Any], user: Dict[str, Any], 
                                document_repo=None) -> bool:
    """
    验证用户是否有权限访问知识实体或关系
    
    Args:
        entity_or_relation: 实体或关系信息
        user: 用户信息
        document_repo: 文档仓库实例
        
    Returns:
        bool: 是否有权限
    """
    # 管理员可以访问所有知识
    if user.get("is_admin", False):
        return True
    
    # 如果没有关联文档，检查创建者
    if "document_id" not in entity_or_relation:
        return entity_or_relation.get("created_by") == user["id"]
    
    # 延迟导入避免循环依赖
    if document_repo is None:
        from src.repositories.document_repository import document_repository
        document_repo = document_repository
    
    # 检查关联文档的权限
    document_id = entity_or_relation["document_id"]
    document = await document_repo.find_by_id(document_id)
    
    if not document:
        return False
    
    return document.get("created_by") == user["id"]