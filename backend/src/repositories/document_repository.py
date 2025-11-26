import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.services.db_service import db_service
from src.models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentRepository:
    """文档仓库"""
    
    def __init__(self):
        self.collection_name = "documents"
        self.logger = logger.getChild("DocumentRepository")
    
    async def get_collection(self):
        """获取MongoDB集合"""
        mongodb = await db_service.get_mongodb()
        return mongodb[self.collection_name]
    
    async def create(self, document_data: Dict[str, Any]) -> Document:
        """创建文档记录"""
        try:
            collection = await self.get_collection()
            
            # 确保必要字段存在
            if "created_at" not in document_data:
                document_data["created_at"] = datetime.utcnow()
            if "updated_at" not in document_data:
                document_data["updated_at"] = datetime.utcnow()
            if "status" not in document_data:
                document_data["status"] = DocumentStatus.UPLOADED
            if "entities_count" not in document_data:
                document_data["entities_count"] = 0
            if "relations_count" not in document_data:
                document_data["relations_count"] = 0
            
            result = await collection.insert_one(document_data)
            document_data["_id"] = str(result.inserted_id)
            
            # 移除MongoDB的_id字段
            if "_id" in document_data:
                del document_data["_id"]
            
            return Document(**document_data)
        except Exception as e:
            self.logger.error(f"创建文档记录失败: {str(e)}")
            raise
    
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID查找文档"""
        try:
            collection = await self.get_collection()
            document_data = await collection.find_one({"id": document_id})
            
            if document_data:
                # 移除MongoDB的_id字段
                if "_id" in document_data:
                    del document_data["_id"]
                return Document(**document_data)
            return None
        except Exception as e:
            self.logger.error(f"查找文档失败: {str(e)}")
            raise
    
    async def find_by_user_id(self, user_id: str) -> List[Document]:
        """查找用户的所有文档"""
        try:
            collection = await self.get_collection()
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1)
            documents = []
            
            async for document_data in cursor:
                # 移除MongoDB的_id字段
                if "_id" in document_data:
                    del document_data["_id"]
                documents.append(Document(**document_data))
            
            return documents
        except Exception as e:
            self.logger.error(f"查找用户文档失败: {str(e)}")
            raise
    
    async def update(self, document_id: str, update_data: Dict[str, Any]) -> Optional[Document]:
        """更新文档信息"""
        try:
            collection = await self.get_collection()
            
            # 更新时间戳
            update_data["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"id": document_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.find_by_id(document_id)
            return None
        except Exception as e:
            self.logger.error(f"更新文档失败: {str(e)}")
            raise
    
    async def update_status(self, document_id: str, status: DocumentStatus) -> Optional[Document]:
        """更新文档状态"""
        update_data = {"status": status}
        
        # 如果是处理完成状态，记录处理时间
        if status == DocumentStatus.PROCESSED:
            update_data["processed_at"] = datetime.utcnow()
        
        return await self.update(document_id, update_data)
    
    async def update_entity_counts(
        self,
        document_id: str,
        entities_count: int,
        relations_count: int
    ) -> Optional[Document]:
        """更新实体和关系计数"""
        return await self.update(document_id, {
            "entities_count": entities_count,
            "relations_count": relations_count
        })
    
    async def delete(self, document_id: str) -> bool:
        """删除文档"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_one({"id": document_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"删除文档失败: {str(e)}")
            raise
    
    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_criteria: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending, 1 for ascending
    ) -> List[Document]:
        """列出文档"""
        try:
            collection = await self.get_collection()
            filter_criteria = filter_criteria or {}
            
            cursor = collection.find(filter_criteria)
            cursor = cursor.sort(sort_by, sort_order)
            cursor = cursor.skip(skip).limit(limit)
            
            documents = []
            async for document_data in cursor:
                # 移除MongoDB的_id字段
                if "_id" in document_data:
                    del document_data["_id"]
                documents.append(Document(**document_data))
            
            return documents
        except Exception as e:
            self.logger.error(f"列出文档失败: {str(e)}")
            raise
    
    async def count_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """统计文档数量"""
        try:
            collection = await self.get_collection()
            filter_criteria = filter_criteria or {}
            return await collection.count_documents(filter_criteria)
        except Exception as e:
            self.logger.error(f"统计文档数量失败: {str(e)}")
            raise
    
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """根据状态查找文档"""
        return await self.list_documents(filter_criteria={"status": status})
    
    async def find_by_industry(self, industry: str) -> List[Document]:
        """根据行业查找文档"""
        return await self.list_documents(filter_criteria={"industry": industry})
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """搜索文档（简化实现）"""
        try:
            filter_criteria = {}
            
            # 添加用户筛选
            if user_id:
                filter_criteria["user_id"] = user_id
            
            # 简单的文本搜索（实际项目中可能需要使用全文索引）
            filter_criteria["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
            
            return await self.list_documents(
                filter_criteria=filter_criteria,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"搜索文档失败: {str(e)}")
            raise
    
    async def get_document_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            collection = await self.get_collection()
            
            # 构建查询条件
            filter_criteria = {}
            if user_id:
                filter_criteria["user_id"] = user_id
            
            # 总文档数
            total_count = await collection.count_documents(filter_criteria)
            
            # 各状态文档数
            status_counts = {}
            pipeline = [
                {"$match": filter_criteria},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            
            cursor = collection.aggregate(pipeline)
            async for doc in cursor:
                status_counts[doc["_id"]] = doc["count"]
            
            # 最近7天上传的文档数
            from datetime import datetime, timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            recent_filter = filter_criteria.copy()
            recent_filter["created_at"] = {"$gte": seven_days_ago}
            recent_count = await collection.count_documents(recent_filter)
            
            return {
                "total_documents": total_count,
                "status_breakdown": status_counts,
                "recent_uploads": recent_count,
                "by_industry": {}  # 可选：按行业统计
            }
        except Exception as e:
            self.logger.error(f"获取文档统计信息失败: {str(e)}")
            # 返回默认统计信息而不是抛出异常
            return {
                "total_documents": 0,
                "status_breakdown": {},
                "recent_uploads": 0,
                "by_industry": {}
            }