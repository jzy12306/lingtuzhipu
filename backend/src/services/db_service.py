import logging
import os
from typing import Optional
import motor.motor_asyncio
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis
import asyncio
import atexit
from pymongo import ASCENDING
from pymongo.errors import PyMongoError
from src.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务"""
    
    def __init__(self):
        self.logger = logger.getChild("DatabaseService")
        self.mongo_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.mongo_db = None
        self.neo4j_driver: Optional[AsyncGraphDatabase] = None
        self.redis_client: Optional[redis.Redis] = None
        self.initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """
        初始化数据库连接
        """
        async with self._lock:
            if self.initialized:
                self.logger.warning("数据库服务已经初始化")
                return
            
            try:
                # 初始化MongoDB - 尝试连接，如果失败不阻止继续
                try:
                    await self._init_mongodb()
                except Exception as e:
                    self.logger.warning(f"MongoDB连接失败 (开发环境可忽略): {str(e)}")
                
                # 初始化Neo4j - 尝试连接，如果失败记录警告但继续
                try:
                    await self._init_neo4j()
                except Exception as e:
                    self.logger.warning(f"Neo4j连接失败 (开发环境可忽略): {str(e)}")
                
                # 初始化Redis - 尝试连接，如果失败记录警告但继续
                try:
                    await self._init_redis()
                except Exception as e:
                    self.logger.warning(f"Redis连接失败 (开发环境可忽略): {str(e)}")
                
                # 尝试创建索引，但失败不阻止
                try:
                    if hasattr(self, 'mongo_db') and self.mongo_db:
                        await self._create_indexes()
                except Exception as e:
                    self.logger.warning(f"创建索引失败: {str(e)}")
                
                # 在开发环境中，即使部分数据库连接失败，我们也将初始化标记为成功
                # 这样应用程序可以启动进行开发和测试
                self.initialized = True
                self.logger.info("数据库服务初始化完成 (部分连接可能失败，但开发环境可继续使用)")
                
                # 注册清理函数
                atexit.register(self._cleanup_sync)
                
            except Exception as e:
                self.logger.error(f"数据库服务初始化过程发生意外错误: {str(e)}")
                await self._cleanup()
                # 在开发环境中，我们不抛出异常，允许应用程序继续运行
                self.initialized = True
                self.logger.info("尽管有错误，应用程序仍将继续运行 (开发模式)")
    
    async def _init_mongodb(self):
        """初始化MongoDB连接"""
        try:
            # 使用settings中的配置
            mongo_uri = settings.MONGO_URI
            mongo_db_name = settings.MONGO_DB_NAME
            
            self.logger.info(f"连接MongoDB: {mongo_uri}, 数据库: {mongo_db_name}")
            
            # 创建MongoDB客户端
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                mongo_uri,
                maxPoolSize=20,
                minPoolSize=5,
                waitQueueTimeoutMS=5000
            )
            
            # 获取数据库
            self.mongo_db = self.mongo_client[mongo_db_name]
            
            # 测试连接
            await self.mongo_client.admin.command('ping')
            self.logger.info("MongoDB连接成功")
            
        except PyMongoError as e:
            self.logger.error(f"MongoDB连接失败: {str(e)}")
            raise
    
    async def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            # 使用settings中的配置
            neo4j_uri = settings.NEO4J_URI
            neo4j_user = settings.NEO4J_USER
            neo4j_password = settings.NEO4J_PASSWORD
            
            self.logger.info(f"连接Neo4j: {neo4j_uri}")
            
            # 创建Neo4j驱动
            self.neo4j_driver = AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=20
            )
            
            # 测试连接
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            self.logger.info("Neo4j连接成功")
            
        except Exception as e:
            self.logger.error(f"Neo4j连接失败: {str(e)}")
            raise
    
    async def _init_redis(self):
        """初始化Redis连接"""
        try:
            redis_url = settings.REDIS_URL
            
            self.logger.info(f"连接Redis: {redis_url}")
            
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # 测试连接
            await self.redis_client.ping()
            self.logger.info("Redis连接成功")
            
        except Exception as e:
            self.logger.error(f"Redis连接失败: {str(e)}")
            raise
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # MongoDB索引
            if self.mongo_db:
                # 用户集合索引
                await self.mongo_db.users.create_index("email", unique=True)
                await self.mongo_db.users.create_index("username", unique=True)
                await self.mongo_db.users.create_index("created_at")
                
                # 文档集合索引
                await self.mongo_db.documents.create_index("title")
                await self.mongo_db.documents.create_index("type")
                await self.mongo_db.documents.create_index("status")
                await self.mongo_db.documents.create_index("created_at")
                await self.mongo_db.documents.create_index("user_id")
                await self.mongo_db.documents.create_index([("content", "text")])
                
                # 复合索引
                await self.mongo_db.documents.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
                
                self.logger.info("MongoDB索引创建成功")
                
        except Exception as e:
            self.logger.error(f"创建数据库索引失败: {str(e)}")
            raise
    
    def get_mongo_db(self):
        """获取MongoDB数据库实例"""
        if not self.initialized or not self.mongo_db:
            raise RuntimeError("数据库服务未初始化")
        return self.mongo_db
    
    async def get_mongodb(self):
        """
        获取MongoDB数据库连接（兼容方法）
        """
        if not self.initialized:
            await self.initialize()
        return self.mongo_db
    
    def get_mongo_client(self):
        """获取MongoDB客户端实例"""
        if not self.initialized or not self.mongo_client:
            raise RuntimeError("数据库服务未初始化")
        return self.mongo_client
    
    def get_neo4j_driver(self):
        """获取Neo4j驱动实例"""
        if not self.initialized or not self.neo4j_driver:
            raise RuntimeError("数据库服务未初始化")
        return self.neo4j_driver
    
    def get_redis_client(self):
        """获取Redis客户端实例"""
        if not self.initialized or not self.redis_client:
            raise RuntimeError("数据库服务未初始化")
        return self.redis_client
    
    async def _cleanup(self):
        """清理数据库连接"""
        try:
            tasks = []
            
            if self.neo4j_driver:
                tasks.append(self.neo4j_driver.close())
                self.neo4j_driver = None
            
            if self.redis_client:
                tasks.append(self.redis_client.close())
                self.redis_client = None
            
            if self.mongo_client:
                self.mongo_client.close()
                self.logger.info("MongoDB连接已关闭")
                self.mongo_client = None
                self.mongo_db = None
            
            if tasks:
                await asyncio.gather(*tasks)
            
            self.initialized = False
            self.logger.info("数据库连接已清理")
            
        except Exception as e:
            self.logger.error(f"清理数据库连接失败: {str(e)}")
    
    def _cleanup_sync(self):
        """同步清理函数（用于atexit）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._cleanup())
            loop.close()
        except Exception as e:
            self.logger.error(f"同步清理数据库连接失败: {str(e)}")
    
    async def is_healthy(self):
        """检查数据库健康状态"""
        if not self.initialized:
            return False
        
        try:
            # 检查MongoDB
            if self.mongo_client:
                await self.mongo_client.admin.command('ping')
            else:
                return False
            
            # 检查Neo4j
            if self.neo4j_driver:
                async with self.neo4j_driver.session() as session:
                    await session.run("RETURN 1")
            else:
                return False
            
            # 检查Redis
            if self.redis_client:
                await self.redis_client.ping()
            else:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据库健康检查失败: {str(e)}")
            return False
    
    async def get_stats(self):
        """获取数据库统计信息"""
        stats = {
            "mongodb": None,
            "neo4j": None,
            "redis": None,
            "initialized": self.initialized,
            "healthy": await self.is_healthy()
        }
        
        try:
            # 获取MongoDB统计信息
            if self.mongo_db and self.initialized:
                coll_stats = {}
                
                # 获取集合列表
                collections = await self.mongo_db.list_collection_names()
                
                # 获取每个集合的统计信息
                for coll_name in collections:
                    coll_stats[coll_name] = {
                        "count": await self.mongo_db[coll_name].count_documents({})
                    }
                
                stats["mongodb"] = {
                    "collections": coll_stats,
                    "total_collections": len(collections)
                }
            
            # 获取Neo4j统计信息
            if self.neo4j_driver and self.initialized:
                async with self.neo4j_driver.session() as session:
                    # 获取节点数
                    node_result = await session.run("MATCH (n) RETURN count(n) as count")
                    node_record = await node_result.single()
                    node_count = node_record["count"] if node_record else 0
                    
                    # 获取关系数
                    rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                    rel_record = await rel_result.single()
                    rel_count = rel_record["count"] if rel_record else 0
                    
                    stats["neo4j"] = {
                        "node_count": node_count,
                        "relation_count": rel_count
                    }
            
            # 获取Redis统计信息
            if self.redis_client and self.initialized:
                redis_info = await self.redis_client.info()
                stats["redis"] = {
                    "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0)
                }
            
        except Exception as e:
            self.logger.error(f"获取数据库统计信息失败: {str(e)}")
            
        return stats


# 创建全局数据库服务实例
db_service = DatabaseService()

# 兼容性函数，保持原有接口
def get_neo4j_driver() -> AsyncGraphDatabase:
    """获取Neo4j驱动实例（兼容旧接口）"""
    return db_service.get_neo4j_driver()


def get_mongo_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    """获取MongoDB客户端实例（兼容旧接口）"""
    return db_service.get_mongo_client()


def get_mongo_db():
    """获取MongoDB数据库实例（兼容旧接口）"""
    return db_service.get_mongo_db()


def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例（兼容旧接口）"""
    return db_service.get_redis_client()


async def init_db():
    """初始化所有数据库连接（兼容旧接口）"""
    await db_service.initialize()


async def close_db():
    """关闭所有数据库连接（兼容旧接口）"""
    await db_service._cleanup()