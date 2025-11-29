from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List

from src.models.approval import (
    ApprovalRequest, ApprovalRequestCreate, ApprovalRequestUpdate,
    ApprovalStatus, ApprovalAction, ApprovalActionRequest,
    ApprovalRequestResponse
)
from src.models.user import User
from src.services.approval_service import approval_service
from src.routes.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/approval", tags=["approval"])


@router.post("/requests", response_model=ApprovalRequest)
async def create_approval_request(
    request_data: ApprovalRequestCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建审批请求"""
    try:
        approval_request = await approval_service.create_approval_request(
            request_data=request_data,
            requester_id=current_user.id
        )
        return approval_request
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建审批请求失败: {str(e)}"
        )


@router.get("/requests/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    approval_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取审批请求详情"""
    approval_response = await approval_service.get_approval_request_response(approval_id)
    if not approval_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审批请求不存在"
        )
    
    # 检查权限：只有请求者、审批者或管理员可以查看
    if (
        approval_response.requester_id != current_user.id and 
        approval_response.approver_id != current_user.id and 
        not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此审批请求"
        )
    
    return approval_response


@router.get("/requests", response_model=List[ApprovalRequestResponse])
async def get_approval_requests(
    status: Optional[ApprovalStatus] = Query(None, description="审批状态过滤"),
    type: Optional[str] = Query(None, description="审批类型过滤"),
    requester_id: Optional[str] = Query(None, description="请求者ID过滤"),
    approver_id: Optional[str] = Query(None, description="审批者ID过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_active_user)
):
    """获取审批请求列表"""
    # 普通用户只能查看自己的请求或需要自己审批的请求
    if not current_user.is_admin:
        # 如果没有指定请求者ID和审批者ID，则默认查看自己的请求和需要自己审批的请求
        if not requester_id and not approver_id:
            # 获取自己的请求
            my_requests = await approval_service.get_approval_request_responses(
                status=status,
                type=type,
                requester_id=current_user.id,
                skip=0,
                limit=100
            )
            
            # 获取需要自己审批的请求
            my_approvals = await approval_service.get_approval_request_responses(
                status=status,
                type=type,
                approver_id=current_user.id,
                skip=0,
                limit=100
            )
            
            # 合并结果并去重
            all_requests = {req.id: req for req in my_requests + my_approvals}
            result = list(all_requests.values())
            
            # 排序并分页
            result.sort(key=lambda x: x.created_at, reverse=True)
            result = result[skip:skip+limit]
            
            return result
        else:
            # 如果指定了请求者ID或审批者ID，则检查权限
            if requester_id and requester_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他用户的请求"
                )
                
            if approver_id and approver_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他用户的审批请求"
                )
    
    # 管理员或有权限的用户可以查看指定的请求
    approval_requests = await approval_service.get_approval_request_responses(
        status=status,
        type=type,
        requester_id=requester_id,
        approver_id=approver_id,
        skip=skip,
        limit=limit
    )
    
    return approval_requests


@router.put("/requests/{approval_id}", response_model=ApprovalRequest)
async def update_approval_request(
    approval_id: str,
    update_data: ApprovalRequestUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新审批请求"""
    # 检查权限：只有请求者可以更新
    approval_request = await approval_service.get_approval_request(approval_id)
    if not approval_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审批请求不存在"
        )
    
    if approval_request.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新此审批请求"
        )
    
    # 只有待审批的请求可以更新
    if approval_request.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批的请求可以更新"
        )
    
    updated_request = await approval_service.update_approval_request(approval_id, update_data)
    if not updated_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="更新审批请求失败"
        )
    
    return updated_request


@router.post("/requests/{approval_id}/action")
async def process_approval_action(
    approval_id: str,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """处理审批操作"""
    try:
        approval_request = await approval_service.process_approval_action(
            approval_id=approval_id,
            action=action_request.action,
            operator_id=current_user.id,
            comment=action_request.comment
        )
        
        if not approval_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审批请求不存在"
            )
        
        return {
            "message": "审批操作成功",
            "approval_id": approval_id,
            "status": approval_request.status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"审批操作失败: {str(e)}"
        )


@router.get("/requests/{approval_id}/history")
async def get_approval_history(
    approval_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取审批历史记录"""
    # 检查权限：只有请求者、审批者或管理员可以查看
    approval_response = await approval_service.get_approval_request_response(approval_id)
    if not approval_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审批请求不存在"
        )
    
    if (
        approval_response.requester_id != current_user.id and 
        approval_response.approver_id != current_user.id and 
        not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此审批请求的历史记录"
        )
    
    history = await approval_service.get_approval_history(approval_id)
    return {
        "approval_id": approval_id,
        "history": history
    }


@router.get("/my-requests", response_model=List[ApprovalRequestResponse])
async def get_my_approval_requests(
    status: Optional[ApprovalStatus] = Query(None, description="审批状态过滤"),
    type: Optional[str] = Query(None, description="审批类型过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的审批请求"""
    approval_requests = await approval_service.get_approval_request_responses(
        status=status,
        type=type,
        requester_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return approval_requests


@router.get("/my-approvals", response_model=List[ApprovalRequestResponse])
async def get_my_approvals(
    status: Optional[ApprovalStatus] = Query(None, description="审批状态过滤"),
    type: Optional[str] = Query(None, description="审批类型过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户需要审批的请求"""
    approval_requests = await approval_service.get_approval_request_responses(
        status=status,
        type=type,
        approver_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return approval_requests


@router.post("/check-expired")
async def check_expired_requests(
    current_user: User = Depends(get_current_admin_user)
):
    """检查并处理过期的审批请求（管理员专用）"""
    try:
        count = await approval_service.check_expired_requests()
        return {
            "message": "处理过期审批请求成功",
            "expired_count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理过期审批请求失败: {str(e)}"
        )
