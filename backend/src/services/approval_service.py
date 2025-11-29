import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from src.models.approval import (
    ApprovalRequest, ApprovalRequestCreate, ApprovalRequestUpdate,
    ApprovalStatus, ApprovalAction, ApprovalHistory,
    ApprovalRequestResponse
)
from src.repositories.user_repository import UserRepository
from src.services.db_service import db_service

logger = logging.getLogger(__name__)


class ApprovalService:
    """审批服务"""
    
    def __init__(self):
        self.db_service = None
        self.user_repository = None
    
    def _lazy_import(self):
        """延迟导入依赖"""
        if self.db_service is None:
            self.db_service = db_service
        
        if self.user_repository is None:
            self.user_repository = UserRepository()
    
    async def create_approval_request(self, request_data: ApprovalRequestCreate, requester_id: str) -> ApprovalRequest:
        """
        创建审批请求
        
        Args:
            request_data: 审批请求数据
            requester_id: 请求者ID
            
        Returns:
            ApprovalRequest: 创建的审批请求
        """
        self._lazy_import()
        
        # 生成审批请求ID
        approval_id = str(uuid.uuid4())
        
        # 创建审批请求
        approval_request = ApprovalRequest(
            id=approval_id,
            requester_id=requester_id,
            approver_id=request_data.approver_id,
            type=request_data.type,
            status=ApprovalStatus.PENDING,
            title=request_data.title,
            description=request_data.description,
            resource_id=request_data.resource_id,
            resource_type=request_data.resource_type,
            metadata=request_data.metadata,
            expires_at=request_data.expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 保存到数据库
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        await mongodb.approval_requests.insert_one(approval_request.dict())
        
        # 创建初始历史记录
        await self._create_approval_history(
            approval_id=approval_id,
            action=ApprovalAction.APPROVE,  # 初始创建视为待审批
            operator_id=requester_id,
            comment="创建审批请求"
        )
        
        logger.info(f"创建审批请求成功: {approval_id}")
        return approval_request
    
    async def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """
        获取审批请求
        
        Args:
            approval_id: 审批请求ID
            
        Returns:
            Optional[ApprovalRequest]: 审批请求或None
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        approval_data = await mongodb.approval_requests.find_one({"id": approval_id})
        if not approval_data:
            return None
        
        return ApprovalRequest(**approval_data)
    
    async def get_approval_requests(
        self, 
        status: Optional[ApprovalStatus] = None,
        type: Optional[str] = None,
        requester_id: Optional[str] = None,
        approver_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[ApprovalRequest]:
        """
        获取审批请求列表
        
        Args:
            status: 审批状态过滤
            type: 审批类型过滤
            requester_id: 请求者ID过滤
            approver_id: 审批者ID过滤
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            List[ApprovalRequest]: 审批请求列表
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 构建查询条件
        query = {}
        if status:
            query["status"] = status
        if type:
            query["type"] = type
        if requester_id:
            query["requester_id"] = requester_id
        if approver_id:
            query["approver_id"] = approver_id
        
        # 查询审批请求
        approval_requests = []
        async for approval_data in mongodb.approval_requests.find(query).skip(skip).limit(limit).sort("created_at", -1):
            approval_requests.append(ApprovalRequest(**approval_data))
        
        return approval_requests
    
    async def update_approval_request(self, approval_id: str, update_data: ApprovalRequestUpdate) -> Optional[ApprovalRequest]:
        """
        更新审批请求
        
        Args:
            approval_id: 审批请求ID
            update_data: 更新数据
            
        Returns:
            Optional[ApprovalRequest]: 更新后的审批请求或None
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 构建更新内容
        update_dict = update_data.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()
        
        # 更新审批请求
        result = await mongodb.approval_requests.update_one(
            {"id": approval_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        # 返回更新后的审批请求
        return await self.get_approval_request(approval_id)
    
    async def process_approval_action(
        self, 
        approval_id: str, 
        action: ApprovalAction, 
        operator_id: str, 
        comment: Optional[str] = None
    ) -> Optional[ApprovalRequest]:
        """
        处理审批操作
        
        Args:
            approval_id: 审批请求ID
            action: 审批操作
            operator_id: 操作者ID
            comment: 操作意见
            
        Returns:
            Optional[ApprovalRequest]: 处理后的审批请求或None
        """
        self._lazy_import()
        
        # 获取审批请求
        approval_request = await self.get_approval_request(approval_id)
        if not approval_request:
            return None
        
        # 检查操作权限
        if action in [ApprovalAction.APPROVE, ApprovalAction.REJECT]:
            # 只有审批者或管理员可以审批
            if approval_request.approver_id != operator_id:
                # 检查操作者是否为管理员
                operator = await self.user_repository.find_by_id(operator_id)
                if not operator or not operator.is_admin:
                    logger.warning(f"用户 {operator_id} 无权限审批请求 {approval_id}")
                    raise Exception("无权限执行此操作")
        elif action == ApprovalAction.CANCEL:
            # 只有请求者可以取消
            if approval_request.requester_id != operator_id:
                logger.warning(f"用户 {operator_id} 无权限取消请求 {approval_id}")
                raise Exception("无权限执行此操作")
        
        # 检查审批请求状态
        if approval_request.status != ApprovalStatus.PENDING:
            logger.warning(f"审批请求 {approval_id} 已处理，无法重复操作")
            raise Exception("审批请求已处理，无法重复操作")
        
        # 更新审批状态
        update_dict = {
            "updated_at": datetime.utcnow()
        }
        
        if action == ApprovalAction.APPROVE:
            update_dict["status"] = ApprovalStatus.APPROVED
            update_dict["approved_at"] = datetime.utcnow()
        elif action == ApprovalAction.REJECT:
            update_dict["status"] = ApprovalStatus.REJECTED
            update_dict["rejected_at"] = datetime.utcnow()
        elif action == ApprovalAction.CANCEL:
            update_dict["status"] = ApprovalStatus.CANCELLED
        
        # 更新数据库
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        await mongodb.approval_requests.update_one(
            {"id": approval_id},
            {"$set": update_dict}
        )
        
        # 创建审批历史记录
        await self._create_approval_history(
            approval_id=approval_id,
            action=action,
            operator_id=operator_id,
            comment=comment
        )
        
        # 返回更新后的审批请求
        return await self.get_approval_request(approval_id)
    
    async def _create_approval_history(
        self, 
        approval_id: str, 
        action: ApprovalAction, 
        operator_id: str, 
        comment: Optional[str] = None
    ) -> ApprovalHistory:
        """
        创建审批历史记录
        
        Args:
            approval_id: 审批请求ID
            action: 操作类型
            operator_id: 操作者ID
            comment: 操作意见
            
        Returns:
            ApprovalHistory: 创建的历史记录
        """
        self._lazy_import()
        
        # 生成历史记录ID
        history_id = str(uuid.uuid4())
        
        # 创建历史记录
        history = ApprovalHistory(
            id=history_id,
            approval_id=approval_id,
            action=action,
            operator_id=operator_id,
            comment=comment,
            created_at=datetime.utcnow()
        )
        
        # 保存到数据库
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        await mongodb.approval_history.insert_one(history.dict())
        
        return history
    
    async def get_approval_history(self, approval_id: str) -> List[ApprovalHistory]:
        """
        获取审批历史记录
        
        Args:
            approval_id: 审批请求ID
            
        Returns:
            List[ApprovalHistory]: 审批历史记录列表
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 查询历史记录
        history_list = []
        async for history_data in mongodb.approval_history.find({
            "approval_id": approval_id
        }).sort("created_at", 1):
            history_list.append(ApprovalHistory(**history_data))
        
        return history_list
    
    async def get_approval_request_response(self, approval_id: str) -> Optional[ApprovalRequestResponse]:
        """
        获取审批请求响应
        
        Args:
            approval_id: 审批请求ID
            
        Returns:
            Optional[ApprovalRequestResponse]: 审批请求响应或None
        """
        self._lazy_import()
        
        # 获取审批请求
        approval_request = await self.get_approval_request(approval_id)
        if not approval_request:
            return None
        
        # 获取请求者信息
        requester = await self.user_repository.find_by_id(approval_request.requester_id)
        requester_name = requester.username if requester else "未知用户"
        
        # 获取审批者信息
        approver_name = None
        if approval_request.approver_id:
            approver = await self.user_repository.find_by_id(approval_request.approver_id)
            approver_name = approver.username if approver else "未知用户"
        
        # 获取审批历史
        history = await self.get_approval_history(approval_id)
        
        # 构建响应
        response = ApprovalRequestResponse(
            id=approval_request.id,
            requester_id=approval_request.requester_id,
            requester_name=requester_name,
            approver_id=approval_request.approver_id,
            approver_name=approver_name,
            type=approval_request.type,
            status=approval_request.status,
            title=approval_request.title,
            description=approval_request.description,
            resource_id=approval_request.resource_id,
            resource_type=approval_request.resource_type,
            metadata=approval_request.metadata,
            created_at=approval_request.created_at,
            updated_at=approval_request.updated_at,
            approved_at=approval_request.approved_at,
            rejected_at=approval_request.rejected_at,
            expires_at=approval_request.expires_at,
            history=history
        )
        
        return response
    
    async def get_approval_request_responses(
        self, 
        status: Optional[ApprovalStatus] = None,
        type: Optional[str] = None,
        requester_id: Optional[str] = None,
        approver_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[ApprovalRequestResponse]:
        """
        获取审批请求响应列表
        
        Args:
            status: 审批状态过滤
            type: 审批类型过滤
            requester_id: 请求者ID过滤
            approver_id: 审批者ID过滤
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            List[ApprovalRequestResponse]: 审批请求响应列表
        """
        # 获取审批请求列表
        approval_requests = await self.get_approval_requests(
            status=status,
            type=type,
            requester_id=requester_id,
            approver_id=approver_id,
            skip=skip,
            limit=limit
        )
        
        # 构建响应列表
        responses = []
        for approval_request in approval_requests:
            response = await self.get_approval_request_response(approval_request.id)
            if response:
                responses.append(response)
        
        return responses
    
    async def check_expired_requests(self) -> int:
        """
        检查并处理过期的审批请求
        
        Returns:
            int: 处理的过期请求数量
        """
        self._lazy_import()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            logger.error("MongoDB连接失败")
            raise Exception("数据库连接失败")
        
        # 查询过期的待审批请求
        now = datetime.utcnow()
        result = await mongodb.approval_requests.update_many(
            {
                "status": ApprovalStatus.PENDING,
                "expires_at": {"$lt": now}
            },
            {
                "$set": {
                    "status": ApprovalStatus.EXPIRED,
                    "updated_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"处理了 {result.modified_count} 个过期的审批请求")
        
        return result.modified_count


# 创建全局审批服务实例
approval_service = ApprovalService()
