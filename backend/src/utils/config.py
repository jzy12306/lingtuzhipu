from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """应用程序配置设置"""
    
    # 应用程序设置
    APP_NAME: str = "知识图谱构建与查询系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 服务器设置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 数据库设置
    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "knowledge_graph")
    
    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # JWT设置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS设置
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173"
    ).split(",")
    
    # 文件上传设置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    # 从环境变量获取允许的文件扩展名列表，如果没有则使用默认值
    ALLOWED_EXTENSIONS: List[str] = Field(
        default_factory=lambda: [
            ext.strip() if ext.strip().startswith('.') else f".{ext.strip()}" 
            for ext in os.getenv(
                "ALLOWED_EXTENSIONS", 
                ".txt,.md,.pdf,.doc,.docx,.csv,.json,.xml"
            ).split(",")
        ],
        validate_default=False
    )
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # LLM设置
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "False").lower() == "true"
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")
    
    # Kimi设置
    API_KEY: str = os.getenv("API_KEY", "")
    API_BASE: str = os.getenv("API_BASE", "https://api.moonshot.cn/v1")
    LLM_MODEL: str = os.getenv("MODEL", "moonshot-v1-32k")
    
    # 知识图谱设置
    EMBEDDING_DIMENSION: int = 768
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_ENTITIES_PER_DOCUMENT: int = 1000
    MAX_RELATIONS_PER_DOCUMENT: int = 2000
    
    # 智能体设置
    BUILDER_AGENT_ENABLED: bool = True
    ANALYZER_AGENT_ENABLED: bool = True
    AUDITOR_AGENT_ENABLED: bool = True
    
    class Config:
        # 不使用.env文件，直接使用代码中的默认值和os.getenv获取的环境变量
        case_sensitive = True


# 创建全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
