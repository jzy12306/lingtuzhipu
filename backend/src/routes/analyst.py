from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
import asyncio
import json
import logging
import time
from datetime import datetime
from src.config.settings import settings

from src.core.security import get_current_user
from src.models.user import User
from src.services.analyst_agent_service import AnalystAgentService
from src.repositories.knowledge_repository import KnowledgeRepository
from src.schemas.analyst import (
    QueryRequest, QueryResponse, QueryHistory, 
    CodeExecutionRequest, CodeExecutionResult,
    AnalysisRequest, AnalysisResult,
    SuggestionItem
)

router = APIRouter()
logger = logging.getLogger(__name__)


# 请求和响应模型
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    context: Optional[Dict[str, Any]] = None


class DashboardRequest(BaseModel):
    title: str
    queries: List[str]


class QuerySuggestionResponse(BaseModel):
    suggestions: List[str]


class FeatureListResponse(BaseModel):
    features: List[Dict[str, Any]]


# 创建知识仓库和服务依赖
async def get_knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository()


async def get_analyst_service(
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
) -> AnalystAgentService:
    return AnalystAgentService.get_instance(knowledge_repo)


@router.post("/query", response_model=Dict[str, Any])
async def analyze_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    使用分析师智能体处理自然语言查询
    """
    try:
        # 验证查询长度
        if len(request.query) > 1000:
            raise HTTPException(status_code=400, detail="查询长度不能超过1000个字符")
        
        # 处理查询
        result = await analyst_service.analyze_query(
            query=request.query,
            user_id=current_user.id
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "查询处理失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询处理时出现错误: {str(e)}")


@router.post("/execute-code", response_model=Dict[str, Any])
async def execute_code(
    request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    执行代码片段（代码解释器功能）
    """
    try:
        # 验证代码长度
        if len(request.code) > 5000:
            raise HTTPException(status_code=400, detail="代码长度不能超过5000个字符")
        
        # 验证语言支持
        supported_languages = ["python"]
        if request.language.lower() not in supported_languages:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的编程语言，当前仅支持: {', '.join(supported_languages)}"
            )
        
        # 添加用户上下文
        context = request.context or {}
        context["user_id"] = current_user.id
        
        # 执行代码
        result = await analyst_service.execute_code(
            code=request.code,
            language=request.language,
            context=context
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "代码执行失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码执行时出现错误: {str(e)}")


@router.get("/suggestions", response_model=QuerySuggestionResponse)
async def get_query_suggestions(
    query: str = Query(..., min_length=1, max_length=500, description="当前查询"),
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    获取查询建议
    """
    try:
        suggestions = await analyst_service.get_query_suggestions(
            current_query=query,
            user_id=current_user.id
        )
        return QuerySuggestionResponse(suggestions=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询建议时出现错误: {str(e)}")


@router.post("/dashboard", response_model=Dict[str, Any])
async def create_dashboard(
    request: DashboardRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    创建数据仪表盘（异步）
    """
    try:
        # 验证参数
        if len(request.title) > 200:
            raise HTTPException(status_code=400, detail="仪表盘标题不能超过200个字符")
        
        if len(request.queries) == 0 or len(request.queries) > 10:
            raise HTTPException(status_code=400, detail="查询数量必须在1-10之间")
        
        # 验证每个查询长度
        for q in request.queries:
            if len(q) > 1000:
                raise HTTPException(status_code=400, detail="每个查询长度不能超过1000个字符")
        
        # 异步创建仪表盘
        # 注意：这里返回一个任务ID，实际创建过程在后台进行
        # 为简化实现，我们直接执行并返回结果
        result = await analyst_service.create_dashboard(
            queries=request.queries,
            title=request.title,
            user_id=current_user.id
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "仪表盘创建失败"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建仪表盘时出现错误: {str(e)}")


@router.get("/features", response_model=FeatureListResponse)
async def get_available_features(
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    获取分析师智能体可用功能列表
    """
    try:
        features = analyst_service.get_available_features()
        return FeatureListResponse(features=features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能列表时出现错误: {str(e)}")


@router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    分析师智能体健康检查
    """
    try:
        # 执行一个简单的健康检查查询
        test_result = await analyst_service.analyze_query(
            query="健康检查",
            user_id=current_user.id
        )
        
        return {
            "status": "healthy",
            "agent_status": "online",
            "service_info": {
                "version": "1.0.0",
                "llm_model": settings.LLM_MODEL,
                "use_local_llm": settings.USE_LOCAL_LLM
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"分析师智能体服务不可用: {str(e)}"
        )


@router.post("/test-query")
async def test_query(
    request: QueryRequest
):
    """
    测试查询端点（无需认证）
    用于测试分析师智能体的查询功能
    """
    try:
        # 使用延迟导入避免循环依赖
        from src.services.service_factory import service_factory
        
        # 通过service_factory获取analyst_agent实例处理查询
        result = await service_factory.analyst_agent.process_query(
            query=request.query,
            user_context={"user_id": "test_user"}
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 批量操作端点
@router.post("/batch/query", response_model=List[Dict[str, Any]])
async def batch_analyze_queries(
    queries: List[QueryRequest],
    current_user: User = Depends(get_current_user),
    analyst_service: AnalystAgentService = Depends(get_analyst_service)
):
    """
    批量处理多个查询
    """
    try:
        # 验证批量大小
        if len(queries) == 0 or len(queries) > 5:
            raise HTTPException(status_code=400, detail="批量查询数量必须在1-5之间")
        
        # 处理每个查询
        results = []
        for i, query_request in enumerate(queries):
            try:
                result = await analyst_service.analyze_query(
                    query=query_request.query,
                    user_id=current_user.id
                )
                results.append({
                    "index": i,
                    **result
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": f"查询处理失败: {str(e)}"
                })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询处理时出现错误: {str(e)}")