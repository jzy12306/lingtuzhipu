from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.models.business_rule import BusinessRule, BusinessRuleCreate, BusinessRuleUpdate
from src.services.db_service import DatabaseService

logger = logging.getLogger(__name__)


class BusinessRuleRepository:
    """业务规则数据访问层"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.collection_name = "business_rules"
        self.logger = logger.getChild("BusinessRuleRepository")
    
    async def create_rule(self, rule_data: BusinessRuleCreate) -> BusinessRule:
        """创建业务规则"""
        rule_dict = rule_data.dict()
        rule_dict["created_at"] = datetime.now()
        rule_dict["updated_at"] = datetime.now()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        result = await mongodb[self.collection_name].insert_one(rule_dict)
        
        rule_dict["_id"] = str(result.inserted_id)
        return BusinessRule(**rule_dict)
    
    async def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """根据ID获取业务规则"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        rule_data = await mongodb[self.collection_name].find_one({"_id": rule_id})
        
        if rule_data:
            rule_data["id"] = str(rule_data.pop("_id"))
            return BusinessRule(**rule_data)
        return None
    
    async def get_rule_by_type(self, rule_type: str) -> Optional[BusinessRule]:
        """根据类型获取规则"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        rule_data = await mongodb[self.collection_name].find_one({"rule_type": rule_type, "is_active": True})
        
        if rule_data:
            rule_data["id"] = str(rule_data.pop("_id"))
            return BusinessRule(**rule_data)
        return None
    
    async def list_rules(self, skip: int = 0, limit: int = 100, 
                         rule_type: Optional[str] = None) -> List[BusinessRule]:
        """列出业务规则"""
        filters: Dict[str, Any] = {"is_active": True}
        if rule_type is not None:
            filters["rule_type"] = rule_type
            
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        rules_cursor = mongodb[self.collection_name].find(filters).skip(skip).limit(limit)
        rules_data = []
        async for rule in rules_cursor:
            rules_data.append(rule)
        
        rules = []
        for rule_data in rules_data:
            rule_data["id"] = str(rule_data.pop("_id"))
            rules.append(BusinessRule(**rule_data))
            
        return rules
    
    async def update_rule(self, rule_id: str, 
                          rule_update: BusinessRuleUpdate) -> Optional[BusinessRule]:
        """更新业务规则"""
        update_data = rule_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now()
            
            mongodb = await self.db_service.get_mongodb()
            if mongodb is None:
                raise RuntimeError("数据库未初始化")
            result = await mongodb[self.collection_name].update_one(
                {"_id": rule_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_rule(rule_id)
        return None
    
    async def delete_rule(self, rule_id: str) -> bool:
        """删除业务规则"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        result = await mongodb[self.collection_name].delete_one({"_id": rule_id})
        
        return result.deleted_count > 0