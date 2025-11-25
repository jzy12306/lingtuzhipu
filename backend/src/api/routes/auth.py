from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta

from models.user import UserCreate, UserResponse, Token
from repositories.user_repository import user_repository
from services.auth_service import auth_service
from utils.dependencies import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """用户注册"""
    try:
        # 检查邮箱是否已存在
        existing_user = await user_repository.find_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        existing_username = await user_repository.find_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        
        # 创建新用户
        new_user = await auth_service.create_user(user_data)
        
        # 转换为响应模型
        return UserResponse(
            id=new_user["id"],
            username=new_user["username"],
            email=new_user["email"],
            created_at=new_user["created_at"],
            updated_at=new_user["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录（OAuth2兼容）"""
    try:
        # 使用用户名查找用户（OAuth2表单使用username字段）
        user = await user_repository.find_by_username(form_data.username)
        if not user:
            # 也尝试使用邮箱查找
            user = await user_repository.find_by_email(form_data.username)
        
        # 验证用户和密码
        if not user or not auth_service.verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(data={"sub": user["email"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"]
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """用户登出
    
    在实际生产环境中，这里应该将token加入黑名单
    使用Redis存储已注销的token
    """
    # 此处简化处理，实际应该实现token黑名单
    return {"message": "登出成功"}


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """刷新访问令牌"""
    try:
        # 创建新的访问令牌
        access_token = auth_service.create_access_token(data={"sub": current_user["email"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新令牌失败: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """修改密码"""
    try:
        # 验证旧密码
        if not auth_service.verify_password(old_password, current_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 验证新密码强度
        if not auth_service.validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码不符合安全要求（至少8位，包含大小写字母和数字）"
            )
        
        # 更新密码
        hashed_password = auth_service.hash_password(new_password)
        await user_repository.update_user(current_user["id"], {"hashed_password": hashed_password})
        
        return {"message": "密码修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}"
        )