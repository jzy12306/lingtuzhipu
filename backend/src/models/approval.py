from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    """审批状态枚举"""
    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    EXPIRED = "expired"  # 已过期


class ApprovalType(str, Enum):
    """审批类型枚举"""
    KNOWLEDGE_CONFLICT = "knowledge_conflict"  # 知识冲突
    RESOURCE_ACCESS = "resource_access"  # 资源访问
    ROLE_ASSIGNMENT = "role_assignment"  # 角色分配
    DATA_EXPORT = "data_export"  # 数据导出
    SYSTEM_CONFIG = "system_config"  # 系统配置
    EXTENSION_INSTALL = "extension_install"  # 扩展安装


class ApprovalRequest(BaseModel):
    """审批请求模型"""
    id: str = Field(..., description="审批请求ID")
    requester_id: str = Field(..., description="请求者ID")
    approver_id: Optional[str] = Field(None, description="审批者ID")
    type: ApprovalType = Field(..., description="审批类型")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="审批状态")
    title: str = Field(..., description="审批标题")
    description: str = Field(..., description="审批描述")
    resource_id: Optional[str] = Field(None, description="关联资源ID")
    resource_type: Optional[str] = Field(None, description="关联资源类型")
    metadata: Optional[dict] = Field(default={}, description="附加元数据")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    approved_at: Optional[datetime] = Field(None, description="审批通过时间")
    rejected_at: Optional[datetime] = Field(None, description="审批拒绝时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ApprovalRequestCreate(BaseModel):
    """创建审批请求模型"""
    type: ApprovalType = Field(..., description="审批类型")
    title: str = Field(..., description="审批标题")
    description: str = Field(..., description="审批描述")
    resource_id: Optional[str] = Field(None, description="关联资源ID")
    resource_type: Optional[str] = Field(None, description="关联资源类型")
    metadata: Optional[dict] = Field(default={}, description="附加元数据")
    approver_id: Optional[str] = Field(None, description="审批者ID")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ApprovalRequestUpdate(BaseModel):
    """更新审批请求模型"""
    status: Optional[ApprovalStatus] = Field(None, description="审批状态")
    approver_id: Optional[str] = Field(None, description="审批者ID")
    metadata: Optional[dict] = Field(None, description="附加元数据")


class ApprovalAction(str, Enum):
    """审批操作枚举"""
    APPROVE = "approve"  # 通过
    REJECT = "reject"  # 拒绝
    CANCEL = "cancel"  # 取消


class ApprovalActionRequest(BaseModel):
    """审批操作请求模型"""
    action: ApprovalAction = Field(..., description="审批操作")
    comment: Optional[str] = Field(None, description="审批意见")


class ApprovalHistory(BaseModel):
    """审批历史记录模型"""
    id: str = Field(..., description="历史记录ID")
    approval_id: str = Field(..., description="审批请求ID")
    action: ApprovalAction = Field(..., description="操作类型")
    operator_id: str = Field(..., description="操作者ID")
    comment: Optional[str] = Field(None, description="操作意见")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="操作时间")


class ApprovalRequestResponse(BaseModel):
    """审批请求响应模型"""
    id: str = Field(..., description="审批请求ID")
    requester_id: str = Field(..., description="请求者ID")
    requester_name: str = Field(..., description="请求者名称")
    approver_id: Optional[str] = Field(None, description="审批者ID")
    approver_name: Optional[str] = Field(None, description="审批者名称")
    type: ApprovalType = Field(..., description="审批类型")
    status: ApprovalStatus = Field(..., description="审批状态")
    title: str = Field(..., description="审批标题")
    description: str = Field(..., description="审批描述")
    resource_id: Optional[str] = Field(None, description="关联资源ID")
    resource_type: Optional[str] = Field(None, description="关联资源类型")
    metadata: Optional[dict] = Field(default={}, description="附加元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    approved_at: Optional[datetime] = Field(None, description="审批通过时间")
    rejected_at: Optional[datetime] = Field(None, description="审批拒绝时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    history: List[ApprovalHistory] = Field(default=[], description="审批历史记录")
