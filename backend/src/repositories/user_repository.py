import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from src.services.db_service import db_service
from src.models.user import User
from src.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)

# 全局内存集合存储（在MongoDB不可用时降级使用，跨仓库实例共享）
_GLOBAL_MEMORY_COLLECTIONS = {}


class MemoryInsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class MemoryUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count

class MemoryCollection:
    def __init__(self):
        self.docs = []
        self._id_counter = 1
    async def insert_one(self, doc):
        _id = str(self._id_counter)
        self._id_counter += 1
        d = dict(doc)
        d["_id"] = _id
        self.docs.append(d)
        return MemoryInsertOneResult(_id)
    async def find_one(self, filter_dict):
        for d in self.docs:
            match = True
            for k, v in filter_dict.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                return dict(d)
        return None
    async def update_one(self, filter_dict, update_dict):
        modified = 0
        for d in self.docs:
            match = True
            for k, v in filter_dict.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update_dict:
                    for k, v in update_dict["$set"].items():
                        d[k] = v
                modified += 1
                break
        return MemoryUpdateResult(modified)

class UserRepository:
    """用户仓库"""
    
    def __init__(self):
        self.collection_name = "users"
        self.logger = logger.getChild("UserRepository")
        self.db = None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希值"""
        return get_password_hash(password)
    
    async def get_collection(self):
        """获取MongoDB集合，数据库不可用时使用内存集合作为降级。"""
        if self.db is not None:
            return self.db[self.collection_name]
        try:
            mongodb = await db_service.get_mongodb()
            if mongodb is not None:
                return mongodb[self.collection_name]
        except Exception as e:
            self.logger.warning(f"获取MongoDB集合失败，启用内存集合: {str(e)}")
        # 内存集合降级（全局共享）
        global _GLOBAL_MEMORY_COLLECTIONS
        if '_GLOBAL_MEMORY_COLLECTIONS' not in globals():
            _GLOBAL_MEMORY_COLLECTIONS = {}
        if self.collection_name not in _GLOBAL_MEMORY_COLLECTIONS:
            _GLOBAL_MEMORY_COLLECTIONS[self.collection_name] = MemoryCollection()
        return _GLOBAL_MEMORY_COLLECTIONS[self.collection_name]
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        try:
            collection = await self.get_collection()
            
            # 确保时间戳存在
            if "created_at" not in user_data:
                user_data["created_at"] = datetime.utcnow()
            if "updated_at" not in user_data:
                user_data["updated_at"] = datetime.utcnow()
            
            # 处理密码加密
            if "password" in user_data:
                # 如果包含密码字段，进行加密
                if not user_data["password"].startswith("$2b$"):
                    user_data["hashed_password"] = self.get_password_hash(user_data["password"])
                # 移除明文密码
                del user_data["password"]
            elif "hashed_password" not in user_data:
                # 如果没有提供密码或哈希密码，使用默认密码
                user_data["hashed_password"] = self.get_password_hash("default_password")
            
            result = await collection.insert_one(user_data)
            user_data["id"] = str(result.inserted_id)
            
            # 移除MongoDB的_id字段
            if "_id" in user_data:
                del user_data["_id"]
            
            # 处理role字段
            if "role" not in user_data:
                # 根据is_superuser或is_admin设置角色
                if user_data.get("is_superuser", False):
                    user_data["role"] = "admin"
                elif user_data.get("is_admin", False):
                    user_data["role"] = "admin"
                else:
                    user_data["role"] = "user"
            # 处理密码哈希字段（兼容不同的字段名）
            if "password_hash" not in user_data:
                # 检查是否有其他密码哈希字段名
                if "hashed_password" in user_data:
                    user_data["password_hash"] = user_data["hashed_password"]
                elif "password" in user_data:
                    # 如果是明文密码，进行加密
                    if not user_data["password"].startswith("$2b$"):
                        user_data["password_hash"] = self.get_password_hash(user_data["password"])
                    else:
                        user_data["password_hash"] = user_data["password"]
                else:
                    # 如果没有密码哈希，设置为None
                    user_data["password_hash"] = None
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
            
            user_data = None
            
            # 先尝试用字符串id查找（适用于内存集合）
            user_data = await collection.find_one({"id": user_id})
            
            # 如果找不到，尝试用ObjectId查找（适用于MongoDB）
            if not user_data:
                try:
                    # 将字符串转换为ObjectId对象
                    from bson import ObjectId
                    user_data = await collection.find_one({"_id": ObjectId(user_id)})
                    if user_data:
                        # 转换MongoDB的_id为id
                        user_data["id"] = str(user_data.pop("_id"))
                except Exception as e:
                    # 对于内存集合，继续尝试其他方式
                    self.logger.warning(f"尝试用ObjectId查找用户失败: {str(e)}")
                    pass
            
            # 最后尝试用_id字段的字符串形式查找（兼容各种情况）
            if not user_data:
                user_data = await collection.find_one({"_id": user_id})
                if user_data:
                    # 转换_id为id
                    if "_id" in user_data:
                        user_data["id"] = str(user_data["_id"])
                        del user_data["_id"]
            
            if user_data:
                # 确保必要字段存在
                if "created_at" not in user_data:
                    user_data["created_at"] = datetime.utcnow()
                if "updated_at" not in user_data:
                    user_data["updated_at"] = datetime.utcnow()
                if "is_active" not in user_data:
                    user_data["is_active"] = True
                if "is_admin" not in user_data:
                    user_data["is_admin"] = False
                if "is_superuser" not in user_data:
                    user_data["is_superuser"] = False
                if "email_verified" not in user_data:
                    user_data["email_verified"] = False
                # 处理role字段
                if "role" not in user_data:
                    # 根据is_superuser或is_admin设置角色
                    if user_data.get("is_superuser", False):
                        user_data["role"] = "admin"
                    elif user_data.get("is_admin", False):
                        user_data["role"] = "admin"
                    else:
                        user_data["role"] = "user"
                # 处理密码哈希字段（兼容不同的字段名）
                if "password_hash" not in user_data:
                    # 检查是否有其他密码哈希字段名
                    if "hashed_password" in user_data:
                        user_data["password_hash"] = user_data["hashed_password"]
                    elif "password" in user_data:
                        # 如果是明文密码，进行加密
                        if not user_data["password"].startswith("$2b$"):
                            user_data["password_hash"] = self.get_password_hash(user_data["password"])
                        else:
                            user_data["password_hash"] = user_data["password"]
                    else:
                        # 如果没有密码哈希，设置为None
                        user_data["password_hash"] = None
                return User(**user_data)
            
            self.logger.warning(f"[UserRepository] 未找到用户，ID: {user_id}")
            return None
        except Exception as e:
            self.logger.error(f"[UserRepository] 查找用户失败: {str(e)}")
            raise
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找用户"""
        try:
            collection = await self.get_collection()
            user_data = await collection.find_one({"email": email})
            
            if user_data:
                # 转换MongoDB的_id为id
                if "_id" in user_data:
                    user_data["id"] = str(user_data["_id"])
                    del user_data["_id"]
                # 添加默认字段如果没有
                if "created_at" not in user_data:
                    user_data["created_at"] = datetime.utcnow()
                if "updated_at" not in user_data:
                    user_data["updated_at"] = datetime.utcnow()
                if "is_active" not in user_data:
                    user_data["is_active"] = True
                if "is_admin" not in user_data:
                    user_data["is_admin"] = False
                if "is_superuser" not in user_data:
                    user_data["is_superuser"] = False
                if "email_verified" not in user_data:
                    user_data["email_verified"] = False
                # 处理role字段
                if "role" not in user_data:
                    # 根据is_superuser或is_admin设置角色
                    if user_data.get("is_superuser", False):
                        user_data["role"] = "admin"
                    elif user_data.get("is_admin", False):
                        user_data["role"] = "admin"
                    else:
                        user_data["role"] = "user"
                # 处理密码哈希字段（兼容不同的字段名）
                if "password_hash" not in user_data:
                    # 检查是否有其他密码哈希字段名
                    if "hashed_password" in user_data:
                        user_data["password_hash"] = user_data["hashed_password"]
                    elif "password" in user_data:
                        # 如果是明文密码，进行加密
                        if not user_data["password"].startswith("$2b$"):
                            user_data["password_hash"] = self.get_password_hash(user_data["password"])
                        else:
                            user_data["password_hash"] = user_data["password"]
                    else:
                        # 如果没有密码哈希，设置为None
                        user_data["password_hash"] = None
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
                # 转换MongoDB的_id为id
                if "_id" in user_data:
                    user_data["id"] = str(user_data["_id"])
                    del user_data["_id"]
                # 添加默认字段如果没有
                if "created_at" not in user_data:
                    user_data["created_at"] = datetime.utcnow()
                if "updated_at" not in user_data:
                    user_data["updated_at"] = datetime.utcnow()
                if "is_active" not in user_data:
                    user_data["is_active"] = True
                if "is_admin" not in user_data:
                    user_data["is_admin"] = False
                if "is_superuser" not in user_data:
                    user_data["is_superuser"] = False
                if "email_verified" not in user_data:
                    user_data["email_verified"] = False
                # 处理role字段
                if "role" not in user_data:
                    # 根据is_superuser或is_admin设置角色
                    if user_data.get("is_superuser", False):
                        user_data["role"] = "admin"
                    elif user_data.get("is_admin", False):
                        user_data["role"] = "admin"
                    else:
                        user_data["role"] = "user"
                # 处理密码哈希字段（兼容不同的字段名）
                if "password_hash" not in user_data:
                    # 检查是否有其他密码哈希字段名
                    if "hashed_password" in user_data:
                        user_data["password_hash"] = user_data["hashed_password"]
                    elif "password" in user_data:
                        # 如果是明文密码，进行加密
                        if not user_data["password"].startswith("$2b$"):
                            user_data["password_hash"] = self.get_password_hash(user_data["password"])
                        else:
                            user_data["password_hash"] = user_data["password"]
                    else:
                        # 如果没有密码哈希，设置为None
                        user_data["password_hash"] = None
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
                # 将MongoDB的_id字段转换为id字段
                if "_id" in user_data:
                    user_data["id"] = str(user_data.pop("_id"))
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
    
    async def find_all(self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[User]:
        """查找所有用户（兼容方法）"""
        return await self.list_users(skip=skip, limit=limit, filter_criteria=filters)
    
    async def count_all(self) -> int:
        """统计所有用户数量"""
        return await self.count_users()
    
    async def count_active_users(self) -> int:
        """统计活跃用户数量"""
        return await self.count_users({"is_active": True})
    
    async def count_admin_users(self) -> int:
        """统计管理员用户数量"""
        return await self.count_users({"is_admin": True})
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息（兼容方法）"""
        user = await self.update(user_id, update_data)
        if user:
            return user.dict()
        return None
    
    async def delete_user(self, user_id: str) -> None:
        """删除用户（兼容方法）"""
        await self.delete(user_id)