"""
依赖工具模块
提供认证、权限校验等依赖函数
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime
import os

from src.repositories.user_repository import UserRepository
from src.schemas.user import User, UserRole, TokenData
from src.config.settings import settings

# 安全配置
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# HTTP Bearer Token认证
security = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    """获取用户仓库实例"""
    return UserRepository()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """
    从Token中提取用户ID
    
    返回:
        用户ID或None（如果token无效）
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """
    获取当前用户（可选）
    
    如果token无效或用户不存在，返回None而不是抛出异常
    
    返回:
        User对象或None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    # 获取用户
    user = await user_repo.find_by_id(user_id)
    if user is None:
        return None
    
    # 转换并确保is_admin字段存在
    return _ensure_user_fields(user)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    获取当前活跃用户
    
    依赖:
        credentials: HTTP Bearer Token
        
    返回:
        User对象
        
    异常:
        HTTPException: 401 - 无法验证凭据
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # 验证token类型
        token_type = payload.get("type")
        if token_type == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="访问令牌无效，请使用访问令牌"
            )
    except JWTError as e:
        # 记录详细的错误信息
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JWT验证错误: {str(e)}")
        raise credentials_exception
    
    # 获取用户
    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    # 转换并确保is_admin字段存在
    return _ensure_user_fields(user)


def _ensure_user_fields(user_data):
    """
    确保用户对象包含所有必要字段，特别是is_admin
    
    参数:
        user_data: 从数据库加载的用户数据（dict或User对象）
        
    返回:
        User对象，确保包含is_admin字段
    """
    # 如果是字典，转换为User对象
    if isinstance(user_data, dict):
        # 确保is_admin字段存在
        if 'is_admin' not in user_data:
            # 根据role字段推断
            role = user_data.get('role', 'user')
            user_data['is_admin'] = (role == 'admin')
        
        return User(**user_data)
    
    # 如果是User对象，检查是否有is_admin属性
    if not hasattr(user_data, 'is_admin'):
        # 根据role字段设置
        role = getattr(user_data, 'role', UserRole.USER)
        user_data.is_admin = (role == UserRole.ADMIN)
    
    return user_data


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    依赖: get_current_user
    
    异常:
        HTTPException: 400 - 用户账户已被禁用
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已被禁用")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """
    可选的用户认证
    
    有有效的token则返回用户，否则返回None
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = await user_repo.get_user_by_id(user_id)
    if user is None:
        return None
    
    return _ensure_user_fields(user)


async def validate_document_permission(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    验证文档访问权限
    
    依赖:
        document_id: 文档ID（路径参数）
        current_user: 当前用户
        
    返回:
        Document对象
        
    异常:
        HTTPException: 404 - 文档不存在
        HTTPException: 403 - 无权访问此文档
    """
    from src.repositories.document_repository import DocumentRepository
    document_repo = DocumentRepository()
    
    document = await document_repo.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 管理员可以访问所有文档
    if getattr(current_user, 'is_admin', False):
        return document
    
    # 用户只能访问自己创建的文档
    if hasattr(document, "user_id"):
        if document.user_id == current_user.id:
            return document
    elif isinstance(document, dict):
        if document.get("user_id") == current_user.id:
            return document
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问此文档"
    )


async def validate_resource_ownership(
    resource_id: str,
    resource_type: str,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """
    验证资源所有权
    
    参数:
        resource_id: 资源ID
        resource_type: 资源类型（document/entity/relation）
        current_user: 当前用户
        
    返回:
        bool: 是否有权限
        
    异常:
        HTTPException: 403 - 权限不足
    """
    from src.repositories.document_repository import DocumentRepository
    from src.repositories.knowledge_repository import KnowledgeRepository
    
    document_repo = DocumentRepository()
    knowledge_repo = KnowledgeRepository()
    
    # 管理员可以访问所有资源
    if getattr(current_user, 'is_admin', False):
        return True
    
    # 如果是文档相关的权限检查
    if resource_type == "document":
        document = await document_repo.get_document(resource_id)
        if document and (document.user_id == current_user.id or getattr(current_user, 'is_admin', False)):
            return True
    
    # 如果是知识实体相关的权限检查
    elif resource_type == "entity":
        entity = await knowledge_repo.get_entity(resource_id)
        if entity and (entity.user_id == current_user.id or getattr(current_user, 'is_admin', False)):
            return True
    
    # 如果是关系相关的权限检查
    elif resource_type == "relation":
        relation = await knowledge_repo.get_relation(resource_id)
        if relation and (relation.user_id == current_user.id or getattr(current_user, 'is_admin', False)):
            return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问此资源"
    )


async def validate_knowledge_permission(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    验证知识实体访问权限
    
    依赖:
        entity_id: 实体ID（路径参数）
        current_user: 当前用户
        
    返回:
        实体或关系对象
        
    异常:
        HTTPException: 404 - 实体不存在
        HTTPException: 403 - 无权访问
    """
    from src.repositories.knowledge_repository import KnowledgeRepository
    knowledge_repo = KnowledgeRepository()
    
    # 尝试获取实体
    entity = await knowledge_repo.get_entity(entity_id)
    if entity:
        # 管理员可以访问所有
        if getattr(current_user, 'is_admin', False):
            return entity
        # 用户只能访问自己的
        if hasattr(entity, "user_id") and entity.user_id == current_user.id:
            return entity
        elif isinstance(entity, dict) and entity.get("user_id") == current_user.id:
            return entity
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此知识实体"
        )
    
    # 尝试获取关系
    relation = await knowledge_repo.get_relation(entity_id)
    if relation:
        # 管理员可以访问所有
        if getattr(current_user, 'is_admin', False):
            return relation
        # 用户只能访问自己的
        if hasattr(relation, "user_id") and relation.user_id == current_user.id:
            return relation
        elif isinstance(relation, dict) and relation.get("user_id") == current_user.id:
            return relation
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此关系"
        )
    
    # 都不存在
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="知识实体或关系不存在"
    )
