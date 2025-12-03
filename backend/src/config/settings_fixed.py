from typing import List, Union
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 服务器配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 数据库配置 - Neo4j
    NEO4J_URI: str = "neo4j://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # 数据库配置 - MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "knowledge_graph"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM配置 - 本地LM Studio
    LOCAL_LLM_ENABLED: bool = False
    LOCAL_LLM_URL: str = "http://192.168.56.1:1234"
    LOCAL_LLM_MODEL: str = "qwen2.5-7b-instruct-1m"
    LOCAL_LLM_TIMEOUT: int = 120
    
    # LLM配置 - Kimi
    API_KEY: str = ""
    API_BASE: str = "https://api.moonshot.cn/v1"
    MODEL: str = "moonshot-v1-32k"
    
    # CORS配置 - 关键修复：使用字符串存储，避免pydantic JSON解析错误
    _cors_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:8080,http://127.0.0.1:5173,http://localhost,http://127.0.0.1"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """将字符串转换为列表，避免pydantic JSON解析错误"""
        return [origin.strip() for origin in self._cors_origins.split(",") if origin.strip()]
    
    # 安全配置
    SECRET_KEY: str = "development_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: Union[str, List[str]] = "pdf,docx,doc,txt,md,html,jpg,jpeg,png,xlsx,xls,csv"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        extensions = self.ALLOWED_EXTENSIONS
        if isinstance(extensions, str):
            return [f".{ext.strip()}" if not ext.strip().startswith(".") else ext.strip() 
                    for ext in extensions.split(",")]
        return extensions
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()