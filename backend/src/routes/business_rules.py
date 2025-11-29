from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from src.models.business_rule import (
    BusinessRuleCreate, 
    BusinessRuleUpdate, 
    BusinessRuleResponse
)
from src.services.service_factory import ServiceFactory
from src.core.security import get_current_user
from src.models.user import User

router = APIRouter(prefix="/business-rules", tags=["业务规则"])

@router.post("/", response_model=BusinessRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule: BusinessRuleCreate,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(ServiceFactory)
):
    """创建业务规则"""
    # 只有管理员可以创建规则
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建业务规则"
        )
    
    try:
        rule_service = service_factory.business_rule_service
        created_rule = await rule_service.create_rule(rule)
        return created_rule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建业务规则失败: {str(e)}"
        )

@router.get("/{rule_id}", response_model=BusinessRuleResponse)
async def get_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(ServiceFactory)
):
    """获取业务规则详情"""
    try:
        rule_service = service_factory.business_rule_service
        rule = await rule_service.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="业务规则不存在"
            )
        return rule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取业务规则失败: {str(e)}"
        )

@router.get("/", response_model=List[BusinessRuleResponse])
async def list_rules(
    rule_type: Optional[str] = Query(None, description="规则类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(ServiceFactory)
):
    """获取业务规则列表"""
    try:
        rule_service = service_factory.business_rule_service
        rules = await rule_service.get_rules(rule_type, is_active, skip, limit)
        return rules
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取业务规则列表失败: {str(e)}"
        )

@router.put("/{rule_id}", response_model=BusinessRuleResponse)
async def update_rule(
    rule_id: str,
    rule_update: BusinessRuleUpdate,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(ServiceFactory)
):
    """更新业务规则"""
    # 只有管理员可以更新规则
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新业务规则"
        )
    
    try:
        rule_service = service_factory.business_rule_service
        updated_rule = await rule_service.update_rule(rule_id, rule_update)
        if not updated_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="业务规则不存在"
            )
        return updated_rule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新业务规则失败: {str(e)}"
        )

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(ServiceFactory)
):
    """删除业务规则"""
    # 只有管理员可以删除规则
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除业务规则"
        )
    
    try:
        rule_service = service_factory.business_rule_service
        success = await rule_service.delete_rule(rule_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="业务规则不存在"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除业务规则失败: {str(e)}"
        )