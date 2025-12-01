"""性能优化配置模块"""
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DatabasePoolConfig:
    """数据库连接池配置"""
    
    def __init__(self):
        # 从环境变量读取配置，提供默认值
        self.min_pool_size = int(os.getenv("DB_MIN_POOL_SIZE", "5"))
        self.max_pool_size = int(os.getenv("DB_MAX_POOL_SIZE", "20"))
        self.max_idle_time = int(os.getenv("DB_MAX_IDLE_TIME", "300"))  # 秒
        self.connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "5"))  # 秒
        self.max_lifetime = int(os.getenv("DB_MAX_LIFETIME", "3600"))  # 秒
    
    def get_config(self) -> Dict[str, Any]:
        """获取连接池配置字典"""
        return {
            "min_size": self.min_pool_size,
            "max_size": self.max_pool_size,
            "max_idle_time": self.max_idle_time,
            "connect_timeout": self.connection_timeout,
            "max_lifetime": self.max_lifetime
        }


class RateLimitConfig:
    """API请求限流配置"""
    
    def __init__(self):
        # 从环境变量读取配置，提供默认值
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
        self.per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))  # 每分钟请求数
        self.per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))  # 每小时请求数
        self.burst = int(os.getenv("RATE_LIMIT_BURST", "10"))  # 突发请求数
        self.block_duration = int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "300"))  # 封禁时长（秒）
        
        # 特殊路由的限流配置
        self.special_routes = {
            "login": {
                "per_minute": int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "10")),
                "block_duration": int(os.getenv("RATE_LIMIT_LOGIN_BLOCK_DURATION", "600"))
            },
            "register": {
                "per_minute": int(os.getenv("RATE_LIMIT_REGISTER_PER_MINUTE", "5")),
                "block_duration": int(os.getenv("RATE_LIMIT_REGISTER_BLOCK_DURATION", "600"))
            },
            "documents": {
                "per_minute": int(os.getenv("RATE_LIMIT_DOCUMENTS_PER_MINUTE", "200")),
                "per_hour": int(os.getenv("RATE_LIMIT_DOCUMENTS_PER_HOUR", "5000")),
                "block_duration": int(os.getenv("RATE_LIMIT_DOCUMENTS_BLOCK_DURATION", "300"))
            }
        }
    
    def get_config_for_route(self, route: str) -> Dict[str, Any]:
        """获取特定路由的限流配置"""
        # 默认配置
        default_config = {
            "enabled": self.enabled,
            "per_minute": self.per_minute,
            "per_hour": self.per_hour,
            "burst": self.burst,
            "block_duration": self.block_duration
        }
        
        # 如果是特殊路由，合并特殊配置（特殊配置会覆盖默认值）
        if route in self.special_routes:
            default_config.update(self.special_routes[route])
        
        return default_config


class CacheConfig:
    """缓存配置"""
    
    def __init__(self):
        # 从环境变量读取配置，提供默认值
        self.enabled = os.getenv("CACHE_ENABLED", "True").lower() == "true"
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # 秒
        self.max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # 最大缓存项数
        
        # 特定缓存键的TTL配置
        self.special_ttls = {
            "user_profile": int(os.getenv("CACHE_TTL_USER_PROFILE", "600")),
            "knowledge_graph_metadata": int(os.getenv("CACHE_TTL_KG_METADATA", "1800")),
            "document_list": int(os.getenv("CACHE_TTL_DOCUMENT_LIST", "300")),
            "query_history": int(os.getenv("CACHE_TTL_QUERY_HISTORY", "60")),
        }
    
    def get_ttl_for_key(self, key_type: str) -> int:
        """获取特定类型缓存键的TTL"""
        return self.special_ttls.get(key_type, self.default_ttl)


class LoggingConfig:
    """日志配置优化"""
    
    def __init__(self):
        # 从环境变量读取配置，提供默认值
        self.level = os.getenv("LOG_LEVEL", "INFO")
        self.format = os.getenv(
            "LOG_FORMAT", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.enable_json_logging = os.getenv("ENABLE_JSON_LOGGING", "False").lower() == "true"
        self.max_log_size = int(os.getenv("MAX_LOG_SIZE", "100"))  # MB
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))


class PerformanceConfig:
    """综合性能配置"""
    
    def __init__(self):
        # 初始化基础配置
        self.db_pool = DatabasePoolConfig()
        self.rate_limit = RateLimitConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        
        # 从环境变量读取默认配置
        self._max_concurrent = int(os.getenv("MAX_CONCURRENT", "100"))
        self._timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "30"))
        self._cache_size_mb = int(os.getenv("CACHE_SIZE_MB", "512"))
        self._enable_compression = os.getenv("ENABLE_COMPRESSION", "True").lower() == "true"
        self._max_concurrent_llm_calls = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "5"))
        self._enable_response_caching = os.getenv("ENABLE_RESPONSE_CACHING", "True").lower() == "true"
        
        # 标记配置是否已从数据库加载
        self._config_loaded = False
    
    @property
    def max_concurrent(self) -> int:
        """最大并发数"""
        return self._max_concurrent
    
    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        self._max_concurrent = value
    
    @property
    def timeout_seconds(self) -> int:
        """超时时间(秒)"""
        return self._timeout_seconds
    
    @timeout_seconds.setter
    def timeout_seconds(self, value: int) -> None:
        self._timeout_seconds = value
    
    @property
    def cache_size_mb(self) -> int:
        """缓存大小(MB)"""
        return self._cache_size_mb
    
    @cache_size_mb.setter
    def cache_size_mb(self, value: int) -> None:
        self._cache_size_mb = value
    
    @property
    def enable_compression(self) -> bool:
        """是否启用压缩"""
        return self._enable_compression
    
    @enable_compression.setter
    def enable_compression(self, value: bool) -> None:
        self._enable_compression = value
    
    @property
    def max_concurrent_llm_calls(self) -> int:
        """LLM最大并发调用数"""
        return self._max_concurrent_llm_calls
    
    @max_concurrent_llm_calls.setter
    def max_concurrent_llm_calls(self, value: int) -> None:
        self._max_concurrent_llm_calls = value
    
    @property
    def enable_response_caching(self) -> bool:
        """是否启用响应缓存"""
        return self._enable_response_caching
    
    @enable_response_caching.setter
    def enable_response_caching(self, value: bool) -> None:
        self._enable_response_caching = value
    
    @property
    def config_loaded(self) -> bool:
        """配置是否已从数据库加载"""
        return self._config_loaded
    
    async def load_from_database(self) -> None:
        """从数据库加载配置"""
        try:
            # 延迟导入，避免循环依赖
            from src.repositories.config_repository import ConfigRepository
            
            config_repo = ConfigRepository()
            config = await config_repo.get_config()
            
            # 更新配置属性
            self._max_concurrent = config.max_concurrent
            self._timeout_seconds = config.timeout_seconds
            self._cache_size_mb = config.cache_size_mb
            self._enable_compression = config.enable_compression
            self._max_concurrent_llm_calls = config.max_concurrent_llm_calls
            self._enable_response_caching = config.enable_response_caching
            
            self._config_loaded = True
            logger.info("成功从数据库加载系统配置")
        except Exception as e:
            logger.warning(f"从数据库加载配置失败，使用默认配置: {str(e)}")
    
    def log_config(self):
        """记录当前性能配置"""
        logger.info(f"数据库连接池配置: {self.db_pool.get_config()}")
        logger.info(f"API限流配置: 启用={self.rate_limit.enabled}, 默认每分钟={self.rate_limit.per_minute}次")
        logger.info(f"缓存配置: 启用={self.cache.enabled}, 默认TTL={self.cache.default_ttl}秒")
        logger.info(f"压缩配置: 启用={self.enable_compression}")
        logger.info(f"LLM并发调用限制: {self.max_concurrent_llm_calls}")
        logger.info(f"最大并发数: {self.max_concurrent}")
        logger.info(f"超时时间: {self.timeout_seconds}秒")
        logger.info(f"缓存大小: {self.cache_size_mb}MB")
        logger.info(f"响应缓存: {'启用' if self.enable_response_caching else '禁用'}")


# 创建全局性能配置实例
performance_config = PerformanceConfig()


async def initialize_config():
    """初始化配置，从数据库加载配置"""
    await performance_config.load_from_database()
    performance_config.log_config()