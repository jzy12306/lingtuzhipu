import logging
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from src.services.db_service import db_service
from src.models.config import SystemConfig

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
    async def count_documents(self, filter_dict):
        count = 0
        for d in self.docs:
            match = True
            for k, v in filter_dict.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count


class ConfigRepository:
    """配置仓库"""
    
    def __init__(self):
        self.collection_name = "system_config"
        self.logger = logger.getChild("ConfigRepository")
        self.db = None
    
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
    
    async def get_config(self) -> SystemConfig:
        """获取当前系统配置"""
        try:
            collection = await self.get_collection()
            
            # 查找配置文档（系统配置只有一个）
            config_data = await collection.find_one({})
            
            # 如果没有配置文档，创建默认配置
            if not config_data:
                self.logger.info("未找到系统配置，创建默认配置")
                default_config = {
                    "max_concurrent": 100,
                    "timeout_seconds": 30,
                    "cache_size_mb": 512,
                    "enable_compression": True,
                    "max_concurrent_llm_calls": 5,
                    "enable_response_caching": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                result = await collection.insert_one(default_config)
                config_data = await collection.find_one({"_id": result.inserted_id})
            
            # 转换MongoDB的_id为id
            if "_id" in config_data:
                config_data["id"] = str(config_data.pop("_id"))
            
            return SystemConfig(**config_data)
        except Exception as e:
            self.logger.error(f"获取系统配置失败: {str(e)}")
            raise
    
    async def update_config(self, update_data: Dict[str, Any]) -> SystemConfig:
        """更新系统配置"""
        try:
            collection = await self.get_collection()
            
            # 更新时间戳
            update_data["updated_at"] = datetime.utcnow()
            
            # 更新配置文档
            result = await collection.update_one(
                {},
                {"$set": update_data},
                upsert=True  # 如果不存在则插入
            )
            
            # 获取更新后的配置
            config_data = await collection.find_one({})
            
            # 转换MongoDB的_id为id
            if "_id" in config_data:
                config_data["id"] = str(config_data.pop("_id"))
            
            return SystemConfig(**config_data)
        except Exception as e:
            self.logger.error(f"更新系统配置失败: {str(e)}")
            raise
    
    async def create_config(self, config_data: Dict[str, Any]) -> SystemConfig:
        """创建系统配置"""
        try:
            collection = await self.get_collection()
            
            # 确保时间戳存在
            if "created_at" not in config_data:
                config_data["created_at"] = datetime.utcnow()
            if "updated_at" not in config_data:
                config_data["updated_at"] = datetime.utcnow()
            
            # 插入配置数据
            result = await collection.insert_one(config_data)
            config_data["id"] = str(result.inserted_id)
            
            # 移除MongoDB的_id字段
            if "_id" in config_data:
                del config_data["_id"]
            
            return SystemConfig(**config_data)
        except Exception as e:
            self.logger.error(f"创建系统配置失败: {str(e)}")
            raise
