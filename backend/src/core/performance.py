"""性能优化配置模块"""
import os
from typing import Dict, Any
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
        self.db_pool = DatabasePoolConfig()
        self.rate_limit = RateLimitConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        
        # 其他性能相关配置
        self.enable_compression = os.getenv("ENABLE_COMPRESSION", "True").lower() == "true"
        self.max_concurrent_llm_calls = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "5"))
        self.enable_response_caching = os.getenv("ENABLE_RESPONSE_CACHING", "True").lower() == "true"
    
    def log_config(self):
        """记录当前性能配置"""
        logger.info(f"数据库连接池配置: {self.db_pool.get_config()}")
        logger.info(f"API限流配置: 启用={self.rate_limit.enabled}, 默认每分钟={self.rate_limit.per_minute}次")
        logger.info(f"缓存配置: 启用={self.cache.enabled}, 默认TTL={self.cache.default_ttl}秒")
        logger.info(f"压缩配置: 启用={self.enable_compression}")
        logger.info(f"LLM并发调用限制: {self.max_concurrent_llm_calls}")


# 创建全局性能配置实例
performance_config = PerformanceConfig()