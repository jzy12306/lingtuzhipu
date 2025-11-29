from typing import Optional, List
from datetime import datetime
import logging

from src.models.business_rule import BusinessRuleCreate, BusinessRuleUpdate, BusinessRule
from src.repositories.business_rule_repository import BusinessRuleRepository

logger = logging.getLogger(__name__)


class BusinessRuleService:
    def __init__(self, business_rule_repository: BusinessRuleRepository):
        self.business_rule_repository = business_rule_repository
        self.logger = logger.getChild("BusinessRuleService")
    
    async def create_rule(self, rule_data: BusinessRuleCreate) -> BusinessRule:
        """创建业务规则"""
        try:
            rule = await self.business_rule_repository.create_rule(rule_data)
            self.logger.info(f"创建业务规则成功: {rule.id}")
            return rule
        except Exception as e:
            self.logger.error(f"创建业务规则失败: {str(e)}")
            raise
    
    async def get_rule_by_id(self, rule_id: str) -> Optional[BusinessRule]:
        """根据ID获取业务规则"""
        try:
            rule = await self.business_rule_repository.get_rule(rule_id)
            return rule
        except Exception as e:
            self.logger.error(f"获取业务规则失败: {rule_id}, 错误: {str(e)}")
            raise
    
    async def get_rules(self, rule_type: Optional[str] = None, is_active: Optional[bool] = None, 
                       skip: int = 0, limit: int = 20) -> List[BusinessRule]:
        """获取业务规则列表"""
        try:
            rules = await self.business_rule_repository.list_rules(skip, limit, rule_type)
            return rules
        except Exception as e:
            self.logger.error(f"获取业务规则列表失败: {str(e)}")
            raise
    
    async def update_rule(self, rule_id: str, rule_update: BusinessRuleUpdate) -> Optional[BusinessRule]:
        """更新业务规则"""
        try:
            rule = await self.business_rule_repository.update_rule(rule_id, rule_update)
            if rule:
                self.logger.info(f"更新业务规则成功: {rule_id}")
            return rule
        except Exception as e:
            self.logger.error(f"更新业务规则失败: {rule_id}, 错误: {str(e)}")
            raise
    
    async def delete_rule(self, rule_id: str) -> bool:
        """删除业务规则"""
        try:
            result = await self.business_rule_repository.delete_rule(rule_id)
            if result:
                self.logger.info(f"删除业务规则成功: {rule_id}")
            return result
        except Exception as e:
            self.logger.error(f"删除业务规则失败: {rule_id}, 错误: {str(e)}")
            raise