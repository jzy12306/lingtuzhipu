import asyncio
import logging
from typing import Optional
import motor.motor_asyncio
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from src.utils.config import settings

logger = logging.getLogger(__name__)

# MongoDB客户端实例
_mongodb_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_mongodb_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

# Neo4j驱动实例
_neo4j_driver: Optional[AsyncGraphDatabase.driver] = None


async def init_mongodb():
    """初始化MongoDB连接"""
    global _mongodb_client, _mongodb_db
    
    try:
        logger.info(f"正在连接MongoDB: {settings.MONGODB_URI}")
        _mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        
        # 验证连接
        await _mongodb_client.admin.command('ping')
        _mongodb_db = _mongodb_client[settings.MONGODB_DB_NAME]
        
        # 创建必要的集合和索引
        await _create_mongodb_indices()
        
        logger.info(f"MongoDB连接成功: {settings.MONGODB_DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"MongoDB连接失败: {str(e)}")
        return False


async def _create_mongodb_indices():
    """创建MongoDB索引"""
    if not _mongodb_db:
        return
    
    try:
        # 用户集合索引
        await _mongodb_db.users.create_index("username", unique=True)
        await _mongodb_db.users.create_index("email", unique=True)
        await _mongodb_db.users.create_index("created_at")
        
        # 文档集合索引
        await _mongodb_db.documents.create_index("title")
        await _mongodb_db.documents.create_index("user_id")
        await _mongodb_db.documents.create_index("created_at")
        await _mongodb_db.documents.create_index("type")
        await _mongodb_db.documents.create_index("status")
        
        # 实体集合索引
        await _mongodb_db.entities.create_index("name")
        await _mongodb_db.entities.create_index("type")
        await _mongodb_db.entities.create_index("user_id")
        await _mongodb_db.entities.create_index("document_id")
        await _mongodb_db.entities.create_index("created_at")
        
        # 关系集合索引
        await _mongodb_db.relations.create_index("type")
        await _mongodb_db.relations.create_index("source_entity_id")
        await _mongodb_db.relations.create_index("target_entity_id")
        await _mongodb_db.relations.create_index("user_id")
        await _mongodb_db.relations.create_index("document_id")
        await _mongodb_db.relations.create_index("created_at")
        
        # 创建复合索引以加速查询
        await _mongodb_db.relations.create_index([
            ("source_entity_id", 1), 
            ("target_entity_id", 1)
        ])
        
        logger.info("MongoDB索引创建成功")
    except Exception as e:
        logger.error(f"MongoDB索引创建失败: {str(e)}")


async def init_neo4j():
    """初始化Neo4j连接"""
    global _neo4j_driver
    
    try:
        logger.info(f"正在连接Neo4j: {settings.NEO4J_URI}")
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=5
        )
        
        # 验证连接
        async with _neo4j_driver.session() as session:
            result = await session.run("RETURN 'Neo4j connection successful' AS message")
            record = await result.single()
            logger.info(f"Neo4j连接成功: {record['message']}")
        
        # 创建必要的约束和索引
        await _create_neo4j_constraints()
        
        return True
    except ServiceUnavailable as e:
        logger.error(f"Neo4j服务不可用: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Neo4j连接失败: {str(e)}")
        return False


async def _create_neo4j_constraints():
    """创建Neo4j约束和索引"""
    if not _neo4j_driver:
        return
    
    try:
        async with _neo4j_driver.session() as session:
            # 创建实体节点的唯一约束
            await session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE
            """)
            
            # 创建关系节点的唯一约束
            await session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (r:Relation) REQUIRE r.id IS UNIQUE
            """)
            
            # 创建文档节点的唯一约束
            await session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
            """)
            
            # 创建用户节点的唯一约束
            await session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE
            """)
            
            # 创建实体类型索引
            await session.run("""
                CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)
            """)
            
            # 创建关系类型索引
            await session.run("""
                CREATE INDEX IF NOT EXISTS FOR (r:Relation) ON (r.type)
            """)
            
            logger.info("Neo4j约束和索引创建成功")
    except Exception as e:
        logger.error(f"Neo4j约束和索引创建失败: {str(e)}")


async def init_db():
    """初始化所有数据库连接"""
    logger.info("开始初始化数据库连接...")
    
    # 并行初始化MongoDB和Neo4j
    mongodb_success, neo4j_success = await asyncio.gather(
        init_mongodb(),
        init_neo4j(),
        return_exceptions=True
    )
    
    # 检查结果
    mongodb_status = isinstance(mongodb_success, bool) and mongodb_success
    neo4j_status = isinstance(neo4j_success, bool) and neo4j_success
    
    # 如果MongoDB连接失败，抛出异常（必需数据库）
    if not mongodb_status:
        raise Exception("MongoDB连接失败，应用无法启动")
    
    # Neo4j连接失败只记录警告，不阻止应用启动
    if not neo4j_status:
        logger.warning("Neo4j连接失败，知识图谱可视化和高级查询功能将不可用")
    
    logger.info("数据库初始化完成")
    return {
        "mongodb": mongodb_status,
        "neo4j": neo4j_status
    }


async def close_db_connections():
    """关闭所有数据库连接"""
    logger.info("开始关闭数据库连接...")
    
    if _mongodb_client:
        try:
            _mongodb_client.close()
            logger.info("MongoDB连接已关闭")
        except Exception as e:
            logger.error(f"关闭MongoDB连接失败: {str(e)}")
    
    if _neo4j_driver:
        try:
            await _neo4j_driver.close()
            logger.info("Neo4j连接已关闭")
        except Exception as e:
            logger.error(f"关闭Neo4j连接失败: {str(e)}")
    
    logger.info("数据库连接关闭完成")


# 获取MongoDB数据库实例
def get_mongodb_db():
    """获取MongoDB数据库实例"""
    if not _mongodb_db:
        raise Exception("MongoDB未初始化")
    return _mongodb_db


# 获取MongoDB集合
def get_mongodb_collection(collection_name: str):
    """获取MongoDB集合"""
    db = get_mongodb_db()
    return db[collection_name]


# 获取Neo4j驱动实例
def get_neo4j_driver():
    """获取Neo4j驱动实例"""
    if not _neo4j_driver:
        logger.warning("Neo4j未初始化，返回None")
    return _neo4j_driver


# 健康检查
async def check_db_health():
    """检查数据库健康状态"""
    health_status = {
        "mongodb": {"status": "unhealthy", "details": None},
        "neo4j": {"status": "unhealthy", "details": None}
    }
    
    # 检查MongoDB
    if _mongodb_client:
        try:
            await _mongodb_client.admin.command('ping')
            health_status["mongodb"]["status"] = "healthy"
        except Exception as e:
            health_status["mongodb"]["details"] = str(e)
    
    # 检查Neo4j
    if _neo4j_driver:
        try:
            async with _neo4j_driver.session() as session:
                await session.run("RETURN 1")
                health_status["neo4j"]["status"] = "healthy"
        except Exception as e:
            health_status["neo4j"]["details"] = str(e)
    
    return health_status
