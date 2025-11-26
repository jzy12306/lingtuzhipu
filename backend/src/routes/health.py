from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio
import time

from src.services.service_factory import ServiceFactory
from src.core.security import get_current_user_optional
from src.models.user import User

router = APIRouter()


@router.get("/check")
async def health_check(
    current_user: User | None = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """综合健康检查端点，检查所有核心服务状态"""
    start_time = time.time()
    
    # 获取服务工厂实例
    service_factory = ServiceFactory()
    
    # 并行执行所有检查
    checks = await asyncio.gather(
        check_database(service_factory),
        check_knowledge_graph(service_factory),
        check_document_service(service_factory),
        check_llm_service(service_factory),
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


async def check_database(service_factory: ServiceFactory) -> Dict[str, Any]:
    """检查数据库连接状态"""
    try:
        db_service = service_factory.db_service
        result = await db_service.get_stats()
        return {
            "status": "healthy" if result.get("healthy", False) else "unhealthy",
            "details": result
        }
    except Exception as e:
        raise Exception(f"数据库检查失败: {str(e)}")


async def check_knowledge_graph(service_factory: ServiceFactory) -> Dict[str, Any]:
    """检查知识图谱服务状态"""
    try:
        kg_service = service_factory.knowledge_graph_service
        # 检查服务是否已初始化
        if kg_service is None or not getattr(kg_service, 'is_initialized', False):
            return {
                "status": "unhealthy",
                "error": "知识图谱服务未初始化"
            }
            
        # 获取统计信息
        stats = await kg_service.get_stats() if hasattr(kg_service, 'get_stats') else {}
        return {
            "status": "healthy",
            "stats": stats,
            "is_initialized": getattr(kg_service, 'is_initialized', False)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"知识图谱服务检查失败: {str(e)}"
        }


async def check_document_service(service_factory: ServiceFactory) -> Dict[str, Any]:
    """检查文档服务状态"""
    try:
        doc_service = service_factory.document_service
        # 检查文档服务是否已初始化
        if doc_service is None or not getattr(doc_service, 'initialized', False):
            return {
                "status": "unhealthy",
                "error": "文档服务未初始化"
            }
        
        # 尝试获取文档统计信息
        try:
            stats = await doc_service.get_document_statistics() if hasattr(doc_service, 'get_document_statistics') else {}
            return {
                "status": "healthy",
                "stats": stats
            }
        except Exception as stats_error:
            # 如果获取统计信息失败，但仍处于初始化状态，则标记为降级
            return {
                "status": "degraded",
                "initialized": True,
                "error": f"获取统计信息失败: {str(stats_error)}"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"文档服务检查失败: {str(e)}"
        }


async def check_llm_service(service_factory: ServiceFactory) -> Dict[str, Any]:
    """检查LLM服务状态"""
    try:
        llm_service = service_factory.llm_service
        # 检查LLM服务是否已初始化
        if llm_service is None or not getattr(llm_service, 'initialized', False):
            return {
                "status": "unhealthy",
                "error": "LLM服务未初始化"
            }
        
        # 检查本地LLM配置
        service_info = {
            "local_llm_enabled": getattr(llm_service, 'local_llm_enabled', False),
            "local_llm_url": getattr(llm_service, 'local_llm_url', None),
            "local_llm_model": getattr(llm_service, 'local_llm_model', None)
        }
        
        # 如果启用了本地LLM，检查配置是否完整
        if getattr(llm_service, 'local_llm_enabled', False):
            if not getattr(llm_service, 'local_llm_url', None) or not getattr(llm_service, 'local_llm_model', None):
                return {
                    "status": "degraded",
                    "info": service_info,
                    "error": "本地LLM配置不完整"
                }
        
        return {
            "status": "healthy",
            "info": service_info
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
        # 获取服务工厂实例
        service_factory = ServiceFactory()
        
        # 获取数据库指标
        db_service = service_factory.db_service
        db_metrics = await db_service.get_stats() if hasattr(db_service, 'get_stats') else {}
        
        # 获取知识图谱指标
        kg_service = service_factory.knowledge_graph_service
        kg_metrics = await kg_service.get_metrics() if hasattr(kg_service, 'get_metrics') else {}
        
        # 获取文档服务指标
        doc_service = service_factory.document_service
        doc_metrics = await doc_service.get_document_statistics() if hasattr(doc_service, 'get_document_statistics') else {}
        
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