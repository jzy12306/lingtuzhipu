from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from src.models.config import SystemConfigResponse, SystemConfigUpdate
from src.repositories.config_repository import ConfigRepository
from src.core.performance import performance_config
from src.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/api/config", tags=["config"])


async def get_config_repository() -> ConfigRepository:
    """获取配置仓库实例"""
    return ConfigRepository()


@router.get("", response_model=SystemConfigResponse)
async def get_config(
    config_repo: ConfigRepository = Depends(get_config_repository),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统配置"""
    try:
        config = await config_repo.get_config()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统配置失败: {str(e)}"
        )


@router.put("", response_model=SystemConfigResponse)
async def update_config(
    update_data: SystemConfigUpdate,
    config_repo: ConfigRepository = Depends(get_config_repository),
    current_user: dict = Depends(get_current_admin_user)
):
    """更新系统配置"""
    try:
        # 转换为字典，过滤掉None值
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        # 更新配置
        updated_config = await config_repo.update_config(update_dict)
        
        # 更新全局配置实例
        performance_config.max_concurrent = updated_config.max_concurrent
        performance_config.timeout_seconds = updated_config.timeout_seconds
        performance_config.cache_size_mb = updated_config.cache_size_mb
        performance_config.enable_compression = updated_config.enable_compression
        performance_config.max_concurrent_llm_calls = updated_config.max_concurrent_llm_calls
        performance_config.enable_response_caching = updated_config.enable_response_caching
        
        return updated_config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统配置失败: {str(e)}"
        )
