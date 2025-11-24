from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from src.models.user import UserResponse, UserUpdate
from src.repositories.user_repository import user_repository
from src.utils.dependencies import get_current_user, get_admin_user

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    current_user: dict = Depends(get_admin_user)
):
    """获取用户列表（管理员权限）"""
    try:
        users = await user_repository.find_all(skip=skip, limit=limit)
        
        # 转换为响应模型
        return [
            UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                created_at=user["created_at"],
                updated_at=user["updated_at"]
            )
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取用户详情
    
    - 普通用户只能查看自己的信息
    - 管理员可以查看所有用户信息
    """
    try:
        # 检查权限：只能查看自己或管理员查看所有
        if user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问其他用户信息"
            )
        
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
            updated_at=user["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新用户信息
    
    - 普通用户只能更新自己的信息
    - 管理员可以更新所有用户信息
    """
    try:
        # 检查权限：只能更新自己或管理员更新所有
        if user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他用户信息"
            )
        
        # 检查用户是否存在
        existing_user = await user_repository.find_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 准备更新数据
        update_data = user_update.dict(exclude_unset=True)
        
        # 检查用户名是否被其他用户使用
        if "username" in update_data:
            username_user = await user_repository.find_by_username(update_data["username"])
            if username_user and username_user["id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
        
        # 检查邮箱是否被其他用户使用
        if "email" in update_data:
            email_user = await user_repository.find_by_email(update_data["email"])
            if email_user and email_user["id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被使用"
                )
        
        # 更新用户信息
        updated_user = await user_repository.update_user(user_id, update_data)
        
        return UserResponse(
            id=updated_user["id"],
            username=updated_user["username"],
            email=updated_user["email"],
            created_at=updated_user["created_at"],
            updated_at=updated_user["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """删除用户（管理员权限）"""
    try:
        # 检查用户是否存在
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不允许删除管理员自己
        if user_id == current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        # 删除用户
        await user_repository.delete_user(user_id)
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.get("/stats/overview")
async def get_user_stats(
    current_user: dict = Depends(get_admin_user)
):
    """获取用户统计信息（管理员权限）"""
    try:
        # 获取用户总数
        total_users = await user_repository.count_all()
        
        # 获取最近注册的用户数（7天内）
        recent_users = await user_repository.count_recent(7)
        
        # 获取用户活跃度统计
        active_users = await user_repository.count_active_users()
        
        return {
            "total_users": total_users,
            "recent_users": recent_users,
            "active_users": active_users,
            "user_growth_rate": round(recent_users / total_users * 100, 2) if total_users > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计信息失败: {str(e)}"
        )