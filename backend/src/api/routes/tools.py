from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from models.agent import AgentTask, AgentResult, WorkflowTask
from repositories.document_repository import document_repository
from agents import process_query_with_workflow
from utils.dependencies import get_current_user

router = APIRouter()


@router.post("/query/process", response_model=Dict[str, Any])
async def process_query(
    query_text: str = Query(..., description="查询文本"),
    document_ids: Optional[List[str]] = Query(None, description="指定文档ID列表"),
    include_code: bool = Query(False, description="是否包含代码解释"),
    current_user: dict = Depends(get_current_user)
):
    """处理用户查询，返回基于知识图谱的回答"""
    try:
        # 验证文档权限
        if document_ids:
            for doc_id in document_ids:
                document = await document_repository.find_by_id(doc_id)
                if not document:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"文档 {doc_id} 不存在"
                    )
                
                # 检查权限
                if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"无权访问文档 {doc_id}"
                    )
        else:
            # 默认使用用户自己的所有文档
            user_documents = await document_repository.find_documents(
                filters={"created_by": current_user["id"]},
                limit=1000
            )
            if user_documents:
                document_ids = [doc["id"] for doc in user_documents]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="您还没有上传任何文档，请先上传文档再进行查询"
                )
        
        # 处理查询
        result = await process_query_with_workflow(
            query_text=query_text,
            document_ids=document_ids,
            user_id=current_user["id"],
            include_code=include_code
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理查询失败: {str(e)}"
        )


@router.post("/agents/tasks", response_model=AgentTask)
async def create_agent_task(
    task: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """创建智能体任务"""
    try:
        # 验证参数
        if "task_type" not in task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少任务类型"
            )
        
        # 验证文档权限
        if "document_id" in task:
            document = await document_repository.find_by_id(task["document_id"])
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )
            
            # 检查权限
            if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权为此文档创建任务"
                )
        
        # 创建任务
        # 在实际生产环境中，应该使用任务队列进行异步处理
        agent_task = AgentTask(
            id=f"task_{current_user['id']}_{hash(str(task))}",
            task_type=task["task_type"],
            input_data=task.get("input_data", {}),
            status="pending",
            created_by=current_user["id"],
            created_at="2023-01-01T00:00:00Z"  # 实际应该使用当前时间
        )
        
        # 这里应该将任务添加到任务队列
        # 暂时直接返回任务信息
        return agent_task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建智能体任务失败: {str(e)}"
        )


@router.get("/agents/tasks", response_model=List[AgentTask])
async def get_agent_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """获取智能体任务列表"""
    try:
        # 在实际生产环境中，应该从任务队列或数据库中获取任务
        # 暂时返回空列表
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体任务列表失败: {str(e)}"
        )


@router.get("/agents/tasks/{task_id}", response_model=AgentResult)
async def get_agent_task_result(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取智能体任务结果"""
    try:
        # 在实际生产环境中，应该从任务队列或数据库中获取任务结果
        # 暂时返回模拟结果
        return AgentResult(
            task_id=task_id,
            status="completed",
            result={"message": "任务执行成功"},
            created_at="2023-01-01T00:00:00Z",
            completed_at="2023-01-01T00:01:00Z"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体任务结果失败: {str(e)}"
        )


@router.post("/workflows/execute", response_model=WorkflowTask)
async def execute_workflow(
    workflow_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """执行工作流任务"""
    try:
        # 验证参数
        if "workflow_type" not in workflow_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少工作流类型"
            )
        
        # 验证文档权限
        if "document_id" in workflow_data:
            document = await document_repository.find_by_id(workflow_data["document_id"])
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )
            
            # 检查权限
            if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权为此文档执行工作流"
                )
        
        # 创建工作流任务
        # 在实际生产环境中，应该使用任务队列进行异步处理
        workflow_task = WorkflowTask(
            id=f"workflow_{current_user['id']}_{hash(str(workflow_data))}",
            workflow_type=workflow_data["workflow_type"],
            parameters=workflow_data.get("parameters", {}),
            status="running",
            created_by=current_user["id"]
        )
        
        # 执行工作流
        # 根据工作流类型执行不同的处理
        if workflow_data["workflow_type"] == "document_processing" and "document_id" in workflow_data:
            # 重新处理文档
            document = await document_repository.find_by_id(workflow_data["document_id"])
            if document and "content" in document:
                from agents import process_document_with_workflow
                await process_document_with_workflow(
                    document["id"],
                    document["content"]
                )
        
        return workflow_task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工作流失败: {str(e)}"
        )


@router.post("/code/interpret", response_model=Dict[str, Any])
async def interpret_code(
    code: str = Query(..., description="要解释的代码"),
    language: str = Query(..., description="代码语言"),
    current_user: dict = Depends(get_current_user)
):
    """解释代码，生成详细说明"""
    try:
        # 在实际生产环境中，应该调用代码解释器智能体
        # 暂时返回模拟结果
        return {
            "code": code,
            "language": language,
            "explanation": "代码解释示例",
            "key_components": ["组件1", "组件2"],
            "complexity": "medium",
            "potential_improvements": ["建议1", "建议2"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解释代码失败: {str(e)}"
        )


@router.get("/stats/usage")
async def get_usage_stats(
    current_user: dict = Depends(get_current_user)
):
    """获取使用统计信息"""
    try:
        # 在实际生产环境中，应该从数据库中获取真实的使用统计
        # 暂时返回模拟数据
        return {
            "queries_count": 100,
            "documents_processed": 10,
            "knowledge_extracted": {
                "entities": 1000,
                "relations": 500
            },
            "usage_by_date": [
                {"date": "2023-01-01", "queries": 10},
                {"date": "2023-01-02", "queries": 15}
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取使用统计失败: {str(e)}"
        )