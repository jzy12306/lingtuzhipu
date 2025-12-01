from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from src.services.service_factory import service_factory
from src.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/status")
async def get_agents_status(
    current_user: Any = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取所有智能体的状态"""
    # 从服务工厂获取智能体管理器服务
    agent_manager = service_factory.agent_manager
    
    # 获取各智能体状态
    agents_status = {
        "builder": {
            "status": "processing",
            "progress": agent_manager.get_builder_status().get("progress", 0),
            "processed": agent_manager.get_builder_status().get("processed", 0),
            "total": agent_manager.get_builder_status().get("total", 0)
        },
        "auditor": {
            "status": "checking",
            "progress": agent_manager.get_auditor_status().get("progress", 0),
            "quality": agent_manager.get_auditor_status().get("quality", 0)
        },
        "analyst": {
            "status": "waiting",
            "progress": agent_manager.get_analyst_status().get("progress", 0),
            "responseTime": agent_manager.get_analyst_status().get("response_time", 0)
        },
        "extension": {
            "status": "loading",
            "progress": agent_manager.get_extension_status().get("progress", 0),
            "loaded": agent_manager.get_extension_status().get("loaded", 0),
            "total": agent_manager.get_extension_status().get("total", 0)
        }
    }
    
    return {
        "status": "success",
        "data": agents_status
    }
