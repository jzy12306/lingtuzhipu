from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets
import string
import os
from typing import Optional

from src.models.user import User, UserCreate, UserUpdate, UserResponse, Token, TokenData, UserLogin, VerificationCode
from src.repositories.user_repository import UserRepository
from src.services.email_service import email_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 配置（统一从全局设置读取）
from src.config.settings import settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码上下文
from src.core.security import verify_password, get_password_hash

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 存储验证码的内存缓存（实际项目中应使用Redis等）
verification_codes = {}

# 开发模式下跳过验证码验证的配置
SKIP_VERIFICATION_CODE = os.getenv("SKIP_VERIFICATION_CODE", "False").lower() == "true"


def get_user_repository() -> UserRepository:
    return UserRepository()


# 使用统一安全模块的verify_password


# 使用统一安全模块的get_password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_verification_code(length: int = 6) -> str:
    """生成验证码"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


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
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    if token_data.user_id is None:
        raise credentials_exception
        
    user = await user_repo.find_by_id(token_data.user_id)
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


@router.post("/send-verification-code")
async def send_verification_code(email: str):
    """发送验证码到邮箱"""
    try:
        # 生成6位数字验证码
        code = generate_verification_code(6)
        
        # 保存验证码及过期时间
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        verification_codes[email] = {
            "code": code,
            "expires_at": expires_at
        }
        
        # 发送验证码邮件
        email_service.send_verification_code(email, code, "verification")
        
        return {"message": f"验证码已发送到 {email}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送验证码失败: {str(e)}"
        )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    verification_code: str,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """用户注册"""
    # 开发模式下跳过验证码验证
    if not SKIP_VERIFICATION_CODE:
        # 验证验证码
        email_verification = verification_codes.get(user_data.email)
        if not email_verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先获取验证码"
            )
        
        if datetime.utcnow() > email_verification["expires_at"]:
            del verification_codes[user_data.email]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期，请重新获取"
            )
        
        if email_verification["code"] != verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
    
    # 检查用户名是否已存在
    existing_user = await user_repo.find_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    existing_email = await user_repo.find_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户，密码加密
    hashed_password = get_password_hash(user_data.password)
    user_data_dict = user_data.dict()
    user_data_dict["hashed_password"] = hashed_password
    del user_data_dict["password"]
    
    # 设置默认值
    user_data_dict.setdefault("is_active", True)
    user_data_dict.setdefault("is_admin", False)
    user_data_dict.setdefault("email_verified", True)  # 验证码验证通过，邮箱已验证
    
    # 创建用户
    new_user = await user_repo.create(user_data_dict)
    
    # 删除已使用的验证码
    if user_data.email in verification_codes:
        del verification_codes[user_data.email]
    
    # 返回用户响应对象，不包含密码
    return UserResponse(**new_user.dict())


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """用户登录"""
    # 根据邮箱查找用户
    user = await user_repo.find_by_email(login_data.email)
    
    if not user or not user.hashed_password or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 更新最后登录时间
    await user_repo.update_last_login(user.id)
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse(**user.dict())
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """刷新访问令牌"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证刷新令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: Optional[str] = payload.get("type")
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """用户登出"""
    # 在实际应用中，可能需要将令牌加入黑名单
    # 这里简化处理，只返回成功消息
    return {"message": "成功登出"}


@router.get("/verify-token")
async def verify_token(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """验证访问令牌是否有效"""
    try:
        current_user = await get_current_user(token, user_repo)
        return {
            "valid": True,
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "email": current_user.email,
                "is_active": current_user.is_active,
                "is_admin": current_user.is_admin
            }
        }
    except HTTPException:
        return {
            "valid": False,
            "error": "Token已过期或无效"
        }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserResponse(**current_user.dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """更新当前用户信息"""
    # 转换为字典并移除None值
    update_data = user_update.dict(exclude_unset=True)
    
    # 如果提供了密码，需要加密
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    # 不允许用户修改自己的管理员状态
    if "is_admin" in update_data:
        del update_data["is_admin"]
    
    # 不允许用户修改自己的活跃状态
    if "is_active" in update_data:
        del update_data["is_active"]
    
    # 不允许修改用户名和邮箱
    if "username" in update_data:
        del update_data["username"]
    if "email" in update_data:
        del update_data["email"]
    
    updated_user = await user_repo.update(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse(**updated_user.dict())


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """修改密码"""
    # 验证当前密码
    if not current_user.hashed_password or not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 检查新密码强度
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少8位"
        )
    
    # 设置新密码
    hashed_password = get_password_hash(new_password)
    await user_repo.update(current_user.id, {"hashed_password": hashed_password})
    
    return {"message": "密码修改成功"}