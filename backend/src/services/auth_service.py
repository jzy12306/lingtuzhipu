import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.config.settings import settings
from src.models.user import User, UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.logger = logger.getChild("AuthService")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error(f"密码验证失败: {str(e)}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希值"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            self.logger.error(f"令牌解码失败: {str(e)}")
            return None
    
    def get_current_user_id(self, token: str) -> Optional[str]:
        """从令牌中获取当前用户ID"""
        payload = self.decode_token(token)
        if payload:
            return payload.get("sub")
        return None
    
    def authenticate_user(self, email: str, password: str, user_repository) -> Optional[User]:
        """认证用户"""
        try:
            # 这里假设有一个user_repository来查询用户
            # 在实际实现中，需要连接数据库
            user = user_repository.find_by_email(email)
            if not user:
                return None
            if not self.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            self.logger.error(f"用户认证失败: {str(e)}")
            return None
    
    def create_user(self, user_create: UserCreate, user_repository) -> Optional[User]:
        """创建用户"""
        try:
            # 检查用户是否已存在
            existing_user = user_repository.find_by_email(user_create.email)
            if existing_user:
                self.logger.warning(f"用户已存在: {user_create.email}")
                return None
            
            # 创建新用户
            hashed_password = self.get_password_hash(user_create.password)
            user_data = user_create.dict()
            user_data.pop("password")
            user_data["hashed_password"] = hashed_password
            
            # 生成用户ID（实际实现中可能由数据库自动生成）
            import uuid
            user_data["id"] = str(uuid.uuid4())
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            
            # 创建用户
            user = user_repository.create(user_data)
            return user
        except Exception as e:
            self.logger.error(f"用户创建失败: {str(e)}")
            raise
    
    def generate_reset_password_token(self, user_id: str) -> str:
        """生成重置密码令牌"""
        # 重置密码令牌有效期较短
        expires_delta = timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
        return self.create_access_token(
            data={"sub": user_id, "type": "reset_password"},
            expires_delta=expires_delta
        )
    
    def validate_reset_password_token(self, token: str) -> Optional[str]:
        """验证重置密码令牌"""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "reset_password":
            return payload.get("sub")
        return None


# 创建全局认证服务实例
auth_service = AuthService()