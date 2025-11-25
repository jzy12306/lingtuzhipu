from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.db_service import db_service
from schemas.analyst import QueryComplexity

logger = logging.getLogger(__name__)


class QueryHistoryRepository:
    """查询历史仓库，处理查询历史的CRUD操作"""
    
    def __init__(self):
        self.collection_name = "query_history"
    
    async def create(self, data: Dict[str, Any]) -> str:
        """创建查询历史记录"""
        try:
            # 确保包含必要字段
            history_data = {
                "user_id": data.get("user_id", "anonymous"),
                "query": data.get("query", ""),
                "result_summary": data.get("result_summary", ""),
                "execution_time": data.get("execution_time", 0.0),
                "complexity": data.get("complexity", QueryComplexity.MODERATE),
                "timestamp": data.get("timestamp", datetime.now()),
                "created_at": datetime.now()
            }
            
            # 插入数据库
            result = await db_service.insert_one(
                collection=self.collection_name,
                document=history_data
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"创建查询历史失败: {str(e)}")
            raise
    
    async def find_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找查询历史"""
        try:
            result = await db_service.find_one(
                collection=self.collection_name,
                filter_criteria={"_id": history_id}
            )
            
            if result:
                # 转换_id为字符串
                result["id"] = str(result.pop("_id"))
            
            return result
            
        except Exception as e:
            logger.error(f"查找查询历史失败: {str(e)}")
            return None
    
    async def find_by_user_id(self, user_id: str, limit: int = 10, 
                            offset: int = 0) -> List[Dict[str, Any]]:
        """查找用户的查询历史"""
        try:
            results = await db_service.find(
                collection=self.collection_name,
                filter_criteria={"user_id": user_id},
                sort_criteria={"timestamp": -1},  # 最新的在前
                limit=limit,
                skip=offset
            )
            
            # 转换_id为字符串
            for result in results:
                result["id"] = str(result.pop("_id"))
            
            return results
            
        except Exception as e:
            logger.error(f"查找用户查询历史失败: {str(e)}")
            return []
    
    async def find_by_query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """根据查询内容查找历史记录"""
        try:
            # 使用模糊匹配
            results = await db_service.find(
                collection=self.collection_name,
                filter_criteria={"query": {"$regex": query, "$options": "i"}},
                sort_criteria={"timestamp": -1},
                limit=limit
            )
            
            # 转换_id为字符串
            for result in results:
                result["id"] = str(result.pop("_id"))
            
            return results
            
        except Exception as e:
            logger.error(f"根据查询内容查找历史失败: {str(e)}")
            return []
    
    async def update(self, history_id: str, data: Dict[str, Any]) -> bool:
        """更新查询历史记录"""
        try:
            update_data = {
                "$set": {
                    **data,
                    "updated_at": datetime.now()
                }
            }
            
            result = await db_service.update_one(
                collection=self.collection_name,
                filter_criteria={"_id": history_id},
                update=update_data
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新查询历史失败: {str(e)}")
            return False
    
    async def delete_by_id(self, history_id: str) -> bool:
        """根据ID删除查询历史"""
        try:
            result = await db_service.delete_one(
                collection=self.collection_name,
                filter_criteria={"_id": history_id}
            )
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"删除查询历史失败: {str(e)}")
            return False
    
    async def delete_by_id_and_user_id(self, history_id: str, user_id: str) -> bool:
        """根据ID和用户ID删除查询历史（确保权限）"""
        try:
            result = await db_service.delete_one(
                collection=self.collection_name,
                filter_criteria={
                    "_id": history_id,
                    "user_id": user_id
                }
            )
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"删除查询历史失败: {str(e)}")
            return False
    
    async def delete_by_user_id(self, user_id: str) -> int:
        """删除用户的所有查询历史"""
        try:
            result = await db_service.delete_many(
                collection=self.collection_name,
                filter_criteria={"user_id": user_id}
            )
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"删除用户查询历史失败: {str(e)}")
            return 0
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户查询统计信息"""
        try:
            # 获取总查询次数
            total_queries = await db_service.count_documents(
                collection=self.collection_name,
                filter_criteria={"user_id": user_id}
            )
            
            # 获取按复杂度统计
            complexity_stats = {}
            for complexity in QueryComplexity.__dict__.values():
                if isinstance(complexity, str):
                    count = await db_service.count_documents(
                        collection=self.collection_name,
                        filter_criteria={
                            "user_id": user_id,
                            "complexity": complexity
                        }
                    )
                    complexity_stats[complexity] = count
            
            # 获取最近查询时间
            latest_query = await db_service.find_one(
                collection=self.collection_name,
                filter_criteria={"user_id": user_id},
                sort_criteria={"timestamp": -1}
            )
            
            return {
                "total_queries": total_queries,
                "complexity_stats": complexity_stats,
                "latest_query_time": latest_query.get("timestamp") if latest_query else None
            }
            
        except Exception as e:
            logger.error(f"获取用户查询统计失败: {str(e)}")
            return {
                "total_queries": 0,
                "complexity_stats": {},
                "latest_query_time": None
            }
    
    async def get_global_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取全局查询统计信息"""
        try:
            # 计算时间范围
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            
            # 总查询次数
            total_queries = await db_service.count_documents(
                collection=self.collection_name,
                filter_criteria={"timestamp": {"$gte": start_date}}
            )
            
            # 活跃用户数
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_date}}},
                {"$group": {"_id": "$user_id"}},
                {"$count": "active_users"}
            ]
            active_users_result = await db_service.aggregate(
                collection=self.collection_name,
                pipeline=pipeline
            )
            
            active_users = active_users_result[0].get("active_users", 0) if active_users_result else 0
            
            # 按复杂度统计
            complexity_stats = {}
            for complexity in QueryComplexity.__dict__.values():
                if isinstance(complexity, str):
                    count = await db_service.count_documents(
                        collection=self.collection_name,
                        filter_criteria={
                            "timestamp": {"$gte": start_date},
                            "complexity": complexity
                        }
                    )
                    complexity_stats[complexity] = count
            
            return {
                "total_queries": total_queries,
                "active_users": active_users,
                "complexity_stats": complexity_stats,
                "time_range_days": days
            }
            
        except Exception as e:
            logger.error(f"获取全局查询统计失败: {str(e)}")
            return {
                "total_queries": 0,
                "active_users": 0,
                "complexity_stats": {},
                "time_range_days": days
            }
    
    async def cleanup_old_history(self, days_to_keep: int = 90) -> int:
        """清理旧的查询历史记录"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = await db_service.delete_many(
                collection=self.collection_name,
                filter_criteria={"timestamp": {"$lt": cutoff_date}}
            )
            
            deleted_count = result.deleted_count
            logger.info(f"清理了 {deleted_count} 条旧查询历史记录")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧查询历史失败: {str(e)}")
            return 0