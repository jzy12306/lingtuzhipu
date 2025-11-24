from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """智能体类型枚举"""
    BUILDER = "builder"  # 构建者智能体
    ANALYZER = "analyzer"  # 分析师智能体
    AUDITOR = "auditor"  # 审计智能体


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class AgentTask(BaseModel):
    """智能体任务模型"""
    task_id: str = Field(..., description="任务ID")
    agent_type: AgentType = Field(..., description="智能体类型")
    task_type: str = Field(..., description="任务类型")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    priority: int = Field(default=0, description="优先级")
    user_id: Optional[str] = Field(None, description="用户ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True


class AgentResult(BaseModel):
    """智能体结果模型"""
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(default_factory=dict, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time_ms: float = Field(default=0.0, description="执行时间(毫秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        from_attributes = True


class AgentInfo(BaseModel):
    """智能体信息模型"""
    agent_id: str = Field(..., description="智能体ID")
    agent_type: AgentType = Field(..., description="智能体类型")
    name: str = Field(..., description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    capabilities: List[str] = Field(default_factory=list, description="智能体能力")
    status: str = Field(default="active", description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class WorkflowTask(BaseModel):
    """工作流任务模型"""
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="执行历史")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        from_attributes = True