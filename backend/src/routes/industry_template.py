from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from src.models.industry_template import (
    IndustryTemplateCreate, 
    IndustryTemplateUpdate, 
    IndustryTemplateResponse
)
from src.services.service_factory import ServiceFactory
from src.core.security import get_current_user
from src.models.user import User

router = APIRouter(prefix="/industry-templates", tags=["行业模板"])


@router.post("/", response_model=IndustryTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_industry_template(
    template: IndustryTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """创建行业模板"""
    # 只有管理员可以创建模板
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建行业模板"
        )
    
    try:
        service_factory = ServiceFactory()
        # 这里需要实现具体的业务逻辑
        # 暂时返回模拟数据
        return IndustryTemplateResponse(
            id="temp_id",
            name=template.name,
            industry=template.industry,
            description=template.description,
            is_active=template.is_active,
            config=template.config,
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建行业模板失败: {str(e)}"
        )


@router.get("/{template_id}", response_model=IndustryTemplateResponse)
async def get_industry_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取行业模板详情"""
    try:
        service_factory = ServiceFactory()
        # 这里需要实现具体的业务逻辑
        # 暂时返回模拟数据
        return IndustryTemplateResponse(
            id=template_id,
            name="金融行业模板",
            industry="finance",
            description="金融行业的实体和关系模板",
            is_active=True,
            config={},
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取行业模板失败: {str(e)}"
        )


@router.get("/", response_model=List[IndustryTemplateResponse])
async def list_industry_templates(
    industry: Optional[str] = Query(None, description="行业类型"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user)
):
    """列出行业模板"""
    try:
        service_factory = ServiceFactory()
        # 这里需要实现具体的业务逻辑
        # 暂时返回模拟数据
        return [
            IndustryTemplateResponse(
                id="1",
                name="金融行业模板",
                industry="finance",
                description="金融行业的实体和关系模板",
                is_active=True,
                config={},
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00"
            ),
            IndustryTemplateResponse(
                id="2",
                name="医疗行业模板",
                industry="medical",
                description="医疗行业的实体和关系模板",
                is_active=True,
                config={},
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00"
            ),
            IndustryTemplateResponse(
                id="3",
                name="法律行业模板",
                industry="legal",
                description="法律行业的实体和关系模板",
                is_active=True,
                config={},
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00"
            )
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取行业模板列表失败: {str(e)}"
        )


@router.put("/{template_id}", response_model=IndustryTemplateResponse)
async def update_industry_template(
    template_id: str,
    template_update: IndustryTemplateUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新行业模板"""
    # 只有管理员可以更新模板
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新行业模板"
        )
    
    try:
        service_factory = ServiceFactory()
        # 这里需要实现具体的业务逻辑
        # 暂时返回模拟数据
        return IndustryTemplateResponse(
            id=template_id,
            name=template_update.name or "金融行业模板",
            industry="finance",
            description=template_update.description or "金融行业的实体和关系模板",
            is_active=template_update.is_active if template_update.is_active is not None else True,
            config=template_update.config or {},
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新行业模板失败: {str(e)}"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_industry_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除行业模板"""
    # 只有管理员可以删除模板
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除行业模板"
        )
    
    try:
        service_factory = ServiceFactory()
        # 这里需要实现具体的业务逻辑
        # 暂时不做任何操作
        return
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除行业模板失败: {str(e)}"
        )