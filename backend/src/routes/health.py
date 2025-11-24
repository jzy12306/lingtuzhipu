from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio
import time

from src.services.db_service import db_service
from src.services.knowledge_graph_service import knowledge_graph_service
from src.services.document_service import document_service
from src.services.llm_service import llm_service
from src.core.security import get_current_user_optional
from src.models.user import User

router = APIRouter()


@router.get("/check")
async def health_check(
    current_user: User | None = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """综合健康检查端点，检查所有核心服务状态"""
    start_time = time.time()
    
    # 并行执行所有检查
    checks = await asyncio.gather(
        check_database(),
        check_knowledge_graph(),
        check_document_service(),
        check_llm_service(),
        return_exceptions=True
    )
    
    # 汇总结果
    database_status, kg_status, doc_status, llm_status = checks
    
    # 计算总体状态
    all_healthy = (
        isinstance(database_status, dict) and database_status["status"] == "healthy"
    )
    
    response = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "response_time_ms": round((time.time() - start_time) * 1000, 2),
        "services": {
            "database": handle_check_result(database_status, "database"),
            "knowledge_graph": handle_check_result(kg_status, "knowledge_graph"),
            "document_service": handle_check_result(doc_status, "document_service"),
            "llm_service": handle_check_result(llm_status, "llm_service")
        }
    }
    
    # 如果用户已认证，添加用户信息
    if current_user:
        response["user"] = {
            "username": current_user.username,
            "is_admin": current_user.is_admin
        }
    
    # 根据状态返回适当的HTTP状态码
    status_code = 200 if all_healthy else 503
    return JSONResponse(content=response, status_code=status_code)


async def check_database() -> Dict[str, Any]:
    """检查数据库连接状态"""
    try:
        result = await db_service.health_check()
        return {
            "status": "healthy",
            "details": result
        }
    except Exception as e:
        raise Exception(f"数据库检查失败: {str(e)}")


async def check_knowledge_graph() -> Dict[str, Any]:
    """检查知识图谱服务状态"""
    try:
        stats = await knowledge_graph_service.get_stats()
        return {
            "status": "healthy",
            "stats": stats,
            "is_initialized": knowledge_graph_service.is_initialized
        }
    except Exception as e:
        raise Exception(f"知识图谱服务检查失败: {str(e)}")


async def check_document_service() -> Dict[str, Any]:
    """检查文档服务状态"""
    try:
        stats = await document_service.get_stats()
        return {
            "status": "healthy",
            "stats": stats
        }
    except Exception as e:
        raise Exception(f"文档服务检查失败: {str(e)}")


async def check_llm_service() -> Dict[str, Any]:
    """检查LLM服务状态"""
    try:
        model_info = await llm_service.get_model_info()
        return {
            "status": "healthy",
            "model_info": model_info,
            "is_connected": llm_service.is_connected
        }
    except Exception as e:
        # LLM服务可能不可用，但不应影响整体系统状态
        return {
            "status": "degraded",
            "error": str(e)
        }


def handle_check_result(result: Any, service_name: str) -> Dict[str, Any]:
    """处理检查结果，格式化异常信息"""
    if isinstance(result, Exception):
        return {
            "status": "unhealthy",
            "error": str(result)
        }
    return result if isinstance(result, dict) else {"status": "unknown"}


@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """获取系统性能指标"""
    try:
        # 获取数据库指标
        db_metrics = await db_service.get_metrics() if hasattr(db_service, 'get_metrics') else {}
        
        # 获取知识图谱指标
        kg_metrics = await knowledge_graph_service.get_metrics() if hasattr(knowledge_graph_service, 'get_metrics') else {}
        
        # 获取文档服务指标
        doc_metrics = await document_service.get_metrics() if hasattr(document_service, 'get_metrics') else {}
        
        return {
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": {
                "database": db_metrics,
                "knowledge_graph": kg_metrics,
                "document_service": doc_metrics
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/version")
async def get_version() -> Dict[str, str]:
    """获取系统版本信息"""
    return {
        "system_version": "1.0.0",
        "api_version": "1.0.0",
        "build_timestamp": "2024-01-01T00:00:00Z",
        "environment": "production"
    }