from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from src.models.user import User, UserCreate, UserUpdate, UserResponse, Token, TokenData, UserLogin
from src.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 配置
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_user_repository() -> UserRepository:
    return UserRepository()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)


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


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = await user_repo.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    existing_email = await user_repo.get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=400,
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
    
    # 创建用户
    new_user = await user_repo.create_user(user_data_dict)
    
    # 返回用户响应对象，不包含密码
    return UserResponse.from_orm(new_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """用户登录"""
    # 使用用户名查找用户（OAuth2PasswordRequestForm使用username字段，但我们接受用户名或邮箱）
    user = await user_repo.get_user_by_username(form_data.username)
    if not user:
        # 尝试用邮箱查找
        user = await user_repo.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 更新最后登录时间
    await user_repo.update_user_last_login(user.id)
    
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
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: UserLogin,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """用户登录（JSON格式）"""
    # 根据提供的凭据查找用户
    if login_data.username:
        user = await user_repo.get_user_by_username(login_data.username)
    elif login_data.email:
        user = await user_repo.get_user_by_email(login_data.email)
    else:
        raise HTTPException(
            status_code=400,
            detail="必须提供用户名或邮箱"
        )
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 更新最后登录时间
    await user_repo.update_user_last_login(user.id)
    
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
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
        token_type: str = payload.get("type")
        user_id: str = payload.get("sub")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.get_user_by_id(user_id)
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)


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
    
    updated_user = await user_repo.update_user(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse.from_orm(updated_user)


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """修改密码"""
    # 验证当前密码
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="当前密码错误"
        )
    
    # 设置新密码
    hashed_password = get_password_hash(new_password)
    await user_repo.update_user(current_user.id, {"hashed_password": hashed_password})
    
    return {"message": "密码修改成功"}
