from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import psutil
import platform

router = APIRouter(prefix="/api/system", tags=["system"])


def get_system_resources() -> Dict[str, Any]:
    """获取系统资源使用情况"""
    try:
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 获取内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 获取磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # 获取系统信息
        system_info = {
            "os": platform.system(),
            "version": platform.version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True)
        }
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "system_info": system_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统资源失败: {str(e)}"
        )


@router.get("/resources", response_model=Dict[str, Any])
async def get_resources():
    """获取系统资源使用情况"""
    return get_system_resources()
