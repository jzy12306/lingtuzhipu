import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


class DatabaseService:
    """
    数据库服务类
    管理数据库连接和会话
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.async_session = None
        self.is_connected = False
    
    async def connect(self):
        """
        连接到数据库
        """
        try:
            # 这里使用SQLite作为开发数据库
            # 在实际生产环境中，应该从配置文件或环境变量中获取数据库URL
            DATABASE_URL = "sqlite+aiosqlite:///./test.db"
            
            self.logger.info(f"正在连接数据库: {DATABASE_URL}")
            
            # 创建异步引擎
            self.engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                future=True
            )
            
            # 创建异步会话工厂
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 测试连接
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    self.is_connected = True
                    self.logger.info("数据库连接成功")
                    return True
                else:
                    self.logger.error("数据库连接测试失败")
                    return False
                    
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """
        断开数据库连接
        """
        if self.engine:
            await self.engine.dispose()
            self.logger.info("数据库连接已断开")
        self.is_connected = False
    
    async def get_db(self):
        """
        获取数据库会话
        """
        if not self.is_connected:
            await self.connect()
        
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_db(self):
        """
        获取同步数据库会话（用于特定场景）
        """
        # 实现同步数据库会话逻辑（如果需要）
        pass