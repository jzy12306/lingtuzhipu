import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
        
        # 延迟导入，避免循环依赖
        self.db_service = None
        self.email_service = None
        self.user_repository = None
    
    def _lazy_import(self):
        """延迟导入依赖"""
        if self.db_service is None:
            from src.services.db_service import db_service as _db_service
            self.db_service = _db_service
        
        if self.email_service is None:
            from src.services.email_service import email_service as _email_service
            self.email_service = _email_service
        
        if self.user_repository is None:
            from src.repositories.user_repository import UserRepository
            self.user_repository = UserRepository()
    
    def generate_verification_code(self, length: int = 6) -> str:
        """生成指定长度的数字验证码"""
        return ''.join(random.choices('0123456789', k=length))
    
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
    
    async def send_verification_code(self, email: str, purpose: str = "login", ip_address: str = None, user_agent: str = None) -> bool:
        """
        发送验证码到用户邮箱
        
        Args:
            email: 接收验证码的邮箱
            purpose: 验证码用途（login, reset_password, register）
            ip_address: 请求IP地址
            user_agent: 请求用户代理
            
        Returns:
            bool: 是否发送成功
        """
        self._lazy_import()
        
        # 1. 检查用户是否存在
        user = await self.user_repository.find_by_email(email)
        if not user:
            self.logger.warning(f"尝试向不存在的邮箱发送验证码: {email}")
            # 在开发环境中，允许向不存在的邮箱发送验证码
            # 生产环境中应该返回错误
        
        # 2. 检查发送频率限制
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            self.logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 检查1分钟内发送次数
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        one_minute_count = await mongodb.verification_codes.count_documents({
            "email": email,
            "purpose": purpose,
            "created_at": {"$gte": one_minute_ago}
        })
        if one_minute_count >= 1:
            self.logger.warning(f"发送频率过高: {email}")
            raise Exception("发送频率过高，请1分钟后再试")
        
        # 检查1小时内发送次数
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        one_hour_count = await mongodb.verification_codes.count_documents({
            "email": email,
            "purpose": purpose,
            "created_at": {"$gte": one_hour_ago}
        })
        if one_hour_count >= 5:
            self.logger.warning(f"发送次数过多: {email}")
            raise Exception("发送次数过多，请1小时后再试")
        
        # 3. 生成验证码
        code = self.generate_verification_code()
        
        # 4. 存储验证码到MongoDB
        verification_code = {
            "email": email,
            "code": code,
            "purpose": purpose,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "created_at": datetime.utcnow(),
            "attempts": 0,
            "is_valid": True,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        await mongodb.verification_codes.insert_one(verification_code)
        
        # 5. 发送验证码
        try:
            self.email_service.send_verification_code(email, code, purpose)
            self.logger.info(f"验证码发送成功: {email}")
            return True
        except Exception as e:
            self.logger.error(f"验证码发送失败: {str(e)}")
            # 发送失败，删除验证码记录
            await mongodb.verification_codes.delete_one({"_id": verification_code["_id"]})
            raise Exception("验证码发送失败，请稍后重试")
    
    async def verify_verification_code(self, email: str, code: str, purpose: str = "login") -> bool:
        """
        验证验证码
        
        Args:
            email: 邮箱
            code: 验证码
            purpose: 验证码用途
            
        Returns:
            bool: 是否验证成功
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            self.logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 1. 查询验证码
        verification_code = await mongodb.verification_codes.find_one({
            "email": email,
            "purpose": purpose,
            "is_valid": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not verification_code:
            self.logger.warning(f"验证码无效或已过期: {email}")
            return False
        
        # 2. 验证验证码
        if verification_code["code"] != code:
            # 增加尝试次数
            await mongodb.verification_codes.update_one(
                {"_id": verification_code["_id"]},
                {"$inc": {"attempts": 1}}
            )
            
            # 检查尝试次数
            if verification_code["attempts"] + 1 >= 3:
                # 超过尝试次数，标记为无效
                await mongodb.verification_codes.update_one(
                    {"_id": verification_code["_id"]},
                    {"$set": {"is_valid": False}}
                )
            self.logger.warning(f"验证码错误: {email}")
            return False
        
        # 3. 验证通过，标记验证码为无效
        await mongodb.verification_codes.update_one(
            {"_id": verification_code["_id"]},
            {"$set": {"is_valid": False}}
        )
        
        self.logger.info(f"验证码验证成功: {email}")
        return True
    
    async def login_with_code(self, email: str, code: str, ip_address: str = None, user_agent: str = None) -> Optional[User]:
        """
        使用验证码登录
        
        Args:
            email: 邮箱
            code: 验证码
            ip_address: 登录IP地址
            user_agent: 登录用户代理
            
        Returns:
            Optional[User]: 用户对象或None
        """
        self._lazy_import()
        
        # 1. 验证验证码
        if not await self.verify_verification_code(email, code, "login"):
            return None
        
        # 2. 查询用户
        user = await self.user_repository.find_by_email(email)
        if not user:
            self.logger.warning(f"验证码登录失败，用户不存在: {email}")
            return None
        
        # 3. 记录登录尝试
        mongodb = await self.db_service.get_mongodb()
        if mongodb is not None:
            await mongodb.login_attempts.insert_one({
                "email": email,
                "success": True,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow(),
                "login_method": "code"
            })
        
        self.logger.info(f"验证码登录成功: {email}")
        return user
    
    async def record_login_attempt(self, email: str, success: bool, ip_address: str, user_agent: str, login_method: str = "password") -> None:
        """
        记录登录尝试
        
        Args:
            email: 邮箱
            success: 是否成功
            ip_address: IP地址
            user_agent: 用户代理
            login_method: 登录方式
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is not None:
            await mongodb.login_attempts.insert_one({
                "email": email,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow(),
                "login_method": login_method
            })
    
    def generate_mfa_secret(self) -> str:
        """
        生成TOTP密钥
        
        Returns:
            str: 生成的TOTP密钥
        """
        return pyotp.random_base32()
    
    def get_mfa_uri(self, email: str, secret: str) -> str:
        """
        获取MFA URI，用于生成二维码
        
        Args:
            email: 用户邮箱
            secret: TOTP密钥
            
        Returns:
            str: MFA URI
        """
        issuer_name = "Lingtu_Zhipu"
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer_name)
    
    def verify_mfa_code(self, secret: str, code: str) -> bool:
        """
        验证TOTP代码
        
        Args:
            secret: TOTP密钥
            code: 用户输入的TOTP代码
            
        Returns:
            bool: 验证是否成功
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """
        生成恢复码
        
        Args:
            count: 恢复码数量
            
        Returns:
            List[str]: 生成的恢复码列表
        """
        recovery_codes = []
        for _ in range(count):
            # 生成8位大写字母和数字的恢复码
            code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
            recovery_codes.append(code)
        return recovery_codes
    
    def verify_recovery_code(self, user: User, recovery_code: str) -> bool:
        """
        验证恢复码
        
        Args:
            user: 用户对象
            recovery_code: 用户输入的恢复码
            
        Returns:
            bool: 验证是否成功
        """
        if not user.mfa_recovery_codes or recovery_code not in user.mfa_recovery_codes:
            return False
        
        # 移除已使用的恢复码
        user.mfa_recovery_codes.remove(recovery_code)
        return True
    
    async def enable_mfa(self, user: User, secret: str, code: str) -> bool:
        """
        启用多因素认证
        
        Args:
            user: 用户对象
            secret: TOTP密钥
            code: 用户输入的TOTP代码
            
        Returns:
            bool: 是否启用成功
        """
        # 验证TOTP代码
        if not self.verify_mfa_code(secret, code):
            return False
        
        # 生成恢复码
        recovery_codes = self.generate_recovery_codes()
        
        # 更新用户信息
        user.mfa_enabled = True
        user.mfa_secret = secret
        user.mfa_recovery_codes = recovery_codes
        
        # 保存到数据库
        self._lazy_import()
        await self.user_repository.update(user.id, {
            "mfa_enabled": True,
            "mfa_secret": secret,
            "mfa_recovery_codes": recovery_codes
        })
        
        return True
    
    async def disable_mfa(self, user: User) -> bool:
        """
        禁用多因素认证
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否禁用成功
        """
        # 更新用户信息
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_recovery_codes = None
        
        # 保存到数据库
        self._lazy_import()
        await self.user_repository.update(user.id, {
            "mfa_enabled": False,
            "mfa_secret": None,
            "mfa_recovery_codes": None
        })
        
        return True
    
    async def reset_mfa(self, user: User) -> Dict[str, Any]:
        """
        重置多因素认证
        
        Args:
            user: 用户对象
            
        Returns:
            Dict[str, Any]: 包含新密钥和URI的字典
        """
        # 生成新的TOTP密钥
        new_secret = self.generate_mfa_secret()
        mfa_uri = self.get_mfa_uri(user.email, new_secret)
        
        # 更新用户信息（仅更新密钥，不启用MFA）
        user.mfa_secret = new_secret
        user.mfa_recovery_codes = None
        
        # 保存到数据库
        self._lazy_import()
        await self.user_repository.update(user.id, {
            "mfa_secret": new_secret,
            "mfa_recovery_codes": None
        })
        
        return {
            "secret": new_secret,
            "uri": mfa_uri
        }


# 创建全局认证服务实例
auth_service = AuthService()