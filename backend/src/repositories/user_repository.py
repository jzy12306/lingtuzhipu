import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from passlib.context import CryptContext
from bson import ObjectId
from services.db_service import db_service
from models.user import User

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


class UserRepository:
    """用户仓库"""
    
    def __init__(self):
        self.collection_name = "users"
        self.logger = logger.getChild("UserRepository")
        self.mongo_client = db_service.mongo_client
        self.db = self.mongo_client.get_database() if self.mongo_client else None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希值"""
        return pwd_context.hash(password)
    
    async def get_collection(self):
        """获取MongoDB集合"""
        if self.db:
            return self.db[self.collection_name]
        mongodb = await db_service.get_mongodb()
        return mongodb[self.collection_name]
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        try:
            collection = await self.get_collection()
            
            # 确保时间戳存在
            if "created_at" not in user_data:
                user_data["created_at"] = datetime.utcnow()
            if "updated_at" not in user_data:
                user_data["updated_at"] = datetime.utcnow()
            
            # 如果包含密码，进行加密
            if "password" in user_data and not user_data["password"].startswith("$2b$"):
                user_data["password"] = self.get_password_hash(user_data["password"])
            
            result = await collection.insert_one(user_data)
            user_data["id"] = str(result.inserted_id)
            
            # 移除MongoDB的_id字段
            if "_id" in user_data:
                del user_data["_id"]
            
            return User(**user_data)
        except Exception as e:
            self.logger.error(f"创建用户失败: {str(e)}")
            raise
    
    async def create_user(self, user_data: Dict[str, Any], is_admin: bool = False) -> Dict[str, Any]:
        """创建新用户（兼容方法）"""
        # 密码加密
        user_data["password"] = self.get_password_hash(user_data["password"])
        
        # 设置用户基本信息
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["is_active"] = True
        user_data["is_admin"] = is_admin
        user_data["last_login"] = None
        
        # 插入用户数据
        collection = await self.get_collection()
        result = await collection.insert_one(user_data)
        
        # 获取创建的用户
        user = await collection.find_one({"_id": result.inserted_id})
        
        # 转换ObjectId为字符串
        if user:
            user["id"] = str(user.pop("_id"))
            
        return user
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """根据ID查找用户"""
        try:
            collection = await self.get_collection()
            
            # 先尝试用字符串id查找
            user_data = await collection.find_one({"id": user_id})
            
            # 如果找不到，尝试用ObjectId查找
            if not user_data:
                try:
                    user_data = await collection.find_one({"_id": ObjectId(user_id)})
                    if user_data:
                        user_data["id"] = str(user_data.pop("_id"))
                except Exception:
                    pass
            
            if user_data:
                # 移除MongoDB的_id字段
                if "_id" in user_data:
                    del user_data["_id"]
                return User(**user_data)
            return None
        except Exception as e:
            self.logger.error(f"查找用户失败: {str(e)}")
            raise
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找用户"""
        try:
            collection = await self.get_collection()
            user_data = await collection.find_one({"email": email})
            
            if user_data:
                # 移除MongoDB的_id字段
                if "_id" in user_data:
                    del user_data["_id"]
                return User(**user_data)
            return None
        except Exception as e:
            self.logger.error(f"根据邮箱查找用户失败: {str(e)}")
            raise
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户"""
        try:
            collection = await self.get_collection()
            user_data = await collection.find_one({"username": username})
            
            if user_data:
                # 移除MongoDB的_id字段
                if "_id" in user_data:
                    del user_data["_id"]
                return User(**user_data)
            return None
        except Exception as e:
            self.logger.error(f"根据用户名查找用户失败: {str(e)}")
            raise
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """更新用户信息"""
        try:
            collection = await self.get_collection()
            
            # 如果包含密码，需要先加密
            if "password" in update_data and not update_data["password"].startswith("$2b$"):
                update_data["password"] = self.get_password_hash(update_data["password"])
            
            # 更新时间戳
            update_data["updated_at"] = datetime.utcnow()
            
            # 尝试用字符串id更新
            result = await collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            # 如果没更新成功，尝试用ObjectId更新
            if result.modified_count == 0:
                try:
                    result = await collection.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": update_data}
                    )
                except Exception:
                    pass
            
            if result.modified_count > 0:
                return await self.find_by_id(user_id)
            return None
        except Exception as e:
            self.logger.error(f"更新用户失败: {str(e)}")
            raise
    
    async def update_last_login(self, user_id: str) -> None:
        """更新用户最后登录时间"""
        try:
            collection = await self.get_collection()
            
            # 尝试用字符串id更新
            await collection.update_one(
                {"id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # 如果不成功，尝试用ObjectId更新
            try:
                await collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"更新最后登录时间失败: {str(e)}")
    
    async def delete(self, user_id: str) -> bool:
        """删除用户"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_one({"id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"删除用户失败: {str(e)}")
            raise
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """列出用户"""
        try:
            collection = await self.get_collection()
            filter_criteria = filter_criteria or {}
            
            cursor = collection.find(filter_criteria).skip(skip).limit(limit)
            users = []
            
            async for user_data in cursor:
                # 移除MongoDB的_id字段
                if "_id" in user_data:
                    del user_data["_id"]
                users.append(User(**user_data))
            
            return users
        except Exception as e:
            self.logger.error(f"列出用户失败: {str(e)}")
            raise
    
    async def count_users(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """统计用户数量"""
        try:
            collection = await self.get_collection()
            filter_criteria = filter_criteria or {}
            return await collection.count_documents(filter_criteria)
        except Exception as e:
            self.logger.error(f"统计用户数量失败: {str(e)}")
            raise
    
    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        try:
            collection = await self.get_collection()
            count = await collection.count_documents({"email": email})
            return count > 0
        except Exception as e:
            self.logger.error(f"检查邮箱是否存在失败: {str(e)}")
            raise
    
    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在"""
        try:
            collection = await self.get_collection()
            count = await collection.count_documents({"username": username})
            return count > 0
        except Exception as e:
            self.logger.error(f"检查用户名是否存在失败: {str(e)}")
            raise