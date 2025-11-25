from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets


# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 获取密码哈希
def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    return pwd_context.hash(password)


# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    return pwd_context.verify(plain_password, hashed_password)


# 生成访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        编码后的JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)  # 默认30分钟过期
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 解码访问令牌
def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT令牌
    
    Returns:
        解码后的数据，如果令牌无效则返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 生成API密钥
def generate_api_key(length: int = 40) -> str:
    """
    生成安全的API密钥
    
    Args:
        length: 密钥长度
    
    Returns:
        生成的API密钥
    """
    return secrets.token_urlsafe(length)


# 安全配置
SECRET_KEY = "your-secret-key-here"  # 在生产环境中应该从环境变量中获取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# 获取当前用户（FastAPI依赖项）
async def get_current_user(token: str):
    """
    从JWT令牌获取当前用户信息
    用于FastAPI的依赖注入
    """
    # 这里实现从令牌获取用户的逻辑
    # 暂时返回模拟用户数据
    from schemas.user import UserResponse, UserRole
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    # 这里应该从数据库获取用户
    # 暂时返回模拟用户
    return UserResponse(
        id=payload.get("user_id", "admin"),
        username=payload.get("username", "admin"),
        email=payload.get("email", "admin@example.com"),
        role=UserRole(payload.get("role", "admin")),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )


# 获取当前活跃用户（FastAPI依赖项）
async def get_current_active_user(current_user):
    """
    获取当前活跃用户
    用于FastAPI的依赖注入
    """
    # 这里可以添加额外的用户活跃性检查
    if not current_user:
        return None
    return current_user


# 获取当前用户（可选认证版本）
async def get_current_user_optional(token: Optional[str] = None):
    """
    从JWT令牌获取当前用户信息（可选认证版本）
    如果没有令牌或令牌无效，返回None而不是抛出异常
    用于FastAPI的依赖注入
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except Exception:
        # 如果令牌无效或其他错误，返回None
        return None


# 密码强度检查
def check_password_strength(password: str) -> dict:
    """
    检查密码强度
    
    Args:
        password: 要检查的密码
    
    Returns:
        包含强度信息的字典
    """
    import re
    
    strength = {
        "score": 0,
        "message": "",
        "requirements": [
            {"met": False, "message": "长度至少8个字符"},
            {"met": False, "message": "包含大写字母"},
            {"met": False, "message": "包含小写字母"},
            {"met": False, "message": "包含数字"},
            {"met": False, "message": "包含特殊字符"}
        ]
    }
    
    if len(password) >= 8:
        strength["score"] += 1
        strength["requirements"][0]["met"] = True
    
    if re.search(r'[A-Z]', password):
        strength["score"] += 1
        strength["requirements"][1]["met"] = True
    
    if re.search(r'[a-z]', password):
        strength["score"] += 1
        strength["requirements"][2]["met"] = True
    
    if re.search(r'\d', password):
        strength["score"] += 1
        strength["requirements"][3]["met"] = True
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        strength["score"] += 1
        strength["requirements"][4]["met"] = True
    
    # 设置强度消息
    if strength["score"] <= 2:
        strength["message"] = "弱"
    elif strength["score"] <= 4:
        strength["message"] = "中"
    else:
        strength["message"] = "强"
    
    return strength
