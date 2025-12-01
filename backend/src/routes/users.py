from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.user import User, UserCreate, UserUpdate, UserResponse, LoginHistoryResponse
from src.utils.dependencies import get_current_user, get_current_active_user, get_current_admin_user
from src.repositories.user_repository import UserRepository
from src.core.security import get_password_hash

router = APIRouter(prefix="/api/users", tags=["users"])


async def get_user_repository() -> UserRepository:
    """获取用户仓库实例"""
    return UserRepository()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """获取用户列表（管理员权限）"""
    try:
        # 构建查询条件
        filters = {}
        if search:
            filters["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # 获取用户列表
        users = await user_repo.find_all(skip=skip, limit=limit, filters=filters)
        
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """获取用户详情
    
    - 普通用户只能查看自己的信息
    - 管理员可以查看所有用户信息
    """
    try:
        # 检查权限：只能查看自己或管理员查看所有
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="无权访问其他用户信息"
            )
        
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """创建用户（管理员权限）"""
    try:
        # 检查用户名是否已存在
        existing_user = await user_repo.find_by_username(user_create.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="用户名已被使用"
            )
        
        # 检查邮箱是否已存在
        existing_email = await user_repo.find_by_email(user_create.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="邮箱已被使用"
            )
        
        # 创建用户数据
        user_data = user_create.dict()
        user_data["password"] = get_password_hash(user_data["password"])
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["is_active"] = True
        user_data["is_admin"] = False
        user_data["last_login"] = None
        user_data["email_verified"] = False
        
        # 创建用户
        user = await user_repo.create_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建用户失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """更新用户信息（管理员权限）"""
    try:
        # 检查用户是否存在
        existing_user = await user_repo.find_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        # 准备更新数据
        update_data = user_update.dict(exclude_unset=True)
        
        # 如果更新密码，需要加密
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])
        
        # 如果更新用户名，检查是否已存在
        if "username" in update_data:
            username_user = await user_repo.find_by_username(update_data["username"])
            if username_user and username_user.id != user_id:
                raise HTTPException(
                    status_code=400,
                    detail="用户名已被使用"
                )
        
        # 如果更新邮箱，检查是否已存在
        if "email" in update_data:
            email_user = await user_repo.find_by_email(update_data["email"])
            if email_user and email_user.id != user_id:
                raise HTTPException(
                    status_code=400,
                    detail="邮箱已被使用"
                )
        
        # 更新用户信息
        update_data["updated_at"] = datetime.utcnow()
        updated_user = await user_repo.update_user(user_id, update_data)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """删除用户（管理员权限）"""
    try:
        # 检查用户是否存在
        existing_user = await user_repo.find_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        # 不允许删除管理员自己
        if user_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="不能删除自己的账户"
            )
        
        # 删除用户
        await user_repo.delete_user(user_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除用户失败: {str(e)}"
        )


@router.get("/stats/overview")
async def get_user_stats(
    current_user: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """获取用户统计信息（管理员权限）"""
    try:
        # 获取用户总数
        total_users = await user_repo.count_all()
        
        # 获取活跃用户数
        active_users = await user_repo.count_active_users()
        
        # 获取管理员用户数
        admin_users = await user_repo.count_admin_users()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "active_rate": round(active_users / total_users * 100, 2) if total_users > 0 else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户统计信息失败: {str(e)}"
        )


@router.get("/me/login-history", response_model=List[LoginHistoryResponse])
async def get_login_history(
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """获取当前用户的登录历史"""
    try:
        # 这里应该调用user_repo的get_login_history方法
        # 目前返回模拟数据
        login_history = [
            {
                "id": "1",
                "login_time": datetime.utcnow().isoformat(),
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "device_info": "Windows 10",
                "location": "北京市",
                "is_current": True,
                "logout_time": None
            },
            {
                "id": "2",
                "login_time": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "device_info": "Mac OS X",
                "location": "上海市",
                "is_current": False,
                "logout_time": (datetime.utcnow() - timedelta(hours=12)).isoformat()
            }
        ]
        return login_history
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取登录历史失败: {str(e)}"
        )


@router.get("/me/mfa-status")
async def get_mfa_status(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的双因素认证状态"""
    try:
        return {
            "mfa_enabled": current_user.mfa_enabled,
            "mfa_secret": current_user.mfa_secret is not None,
            "has_recovery_codes": current_user.mfa_recovery_codes is not None and len(current_user.mfa_recovery_codes) > 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取双因素认证状态失败: {str(e)}"
        )


@router.get("/debug/token")
async def debug_token(
    token: str = Query(..., description="访问令牌"),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """调试端点：验证令牌是否有效"""
    from fastapi import HTTPException, status
    from jose import JWTError, jwt
    from src.config.settings import settings
    from src.models.user import TokenData
    
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, username=username)
    except JWTError as e:
        return {
            "valid": False,
            "error": f"JWT错误: {str(e)}",
            "payload": None
        }
    
    user = await user_repo.find_by_id(token_data.user_id)
    if user is None:
        return {
            "valid": False,
            "error": "用户不存在",
            "payload": {
                "user_id": token_data.user_id,
                "username": token_data.username
            }
        }
    
    return {
        "valid": True,
        "error": None,
        "payload": {
            "user_id": token_data.user_id,
            "username": token_data.username
        },
        "user": user.dict()
    }
