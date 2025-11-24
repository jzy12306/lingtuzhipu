from pydantic_settings import BaseSettings
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
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "knowledge_graph")
    
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
    ALLOWED_EXTENSIONS: List[str] = [
        ".txt", ".md", ".pdf", ".doc", ".docx", ".csv", ".json", ".xml"
    ]
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # LLM设置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "False").lower() == "true"
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")
    
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
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
