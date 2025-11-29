from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.models.industry_template import IndustryTemplate, IndustryTemplateCreate, IndustryTemplateUpdate
from src.services.db_service import DatabaseService

logger = logging.getLogger(__name__)


class IndustryTemplateRepository:
    """行业模板数据访问层"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.collection_name = "industry_templates"
        self.logger = logger.getChild("IndustryTemplateRepository")
    
    async def create_template(self, template_data: IndustryTemplateCreate) -> IndustryTemplate:
        """创建行业模板"""
        template_dict = template_data.dict()
        template_dict["created_at"] = datetime.now()
        template_dict["updated_at"] = datetime.now()
        
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        result = await mongodb[self.collection_name].insert_one(template_dict)
        
        template_dict["_id"] = str(result.inserted_id)
        return IndustryTemplate(**template_dict)
    
    async def get_template(self, template_id: str) -> Optional[IndustryTemplate]:
        """根据ID获取行业模板"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        template_data = await mongodb[self.collection_name].find_one({"_id": template_id})
        
        if template_data:
            template_data["id"] = str(template_data.pop("_id"))
            return IndustryTemplate(**template_data)
        return None
    
    async def get_template_by_industry(self, industry: str) -> Optional[IndustryTemplate]:
        """根据行业获取模板"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        template_data = await mongodb[self.collection_name].find_one({"industry": industry, "is_active": True})
        
        if template_data:
            template_data["id"] = str(template_data.pop("_id"))
            return IndustryTemplate(**template_data)
        return None
    
    async def list_templates(self, skip: int = 0, limit: int = 100, 
                           industry: Optional[str] = None) -> List[IndustryTemplate]:
        """列出行业模板"""
        filters = {"is_active": True}
        if industry is not None:
            filters["industry"] = industry
            
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        templates_cursor = mongodb[self.collection_name].find(filters).skip(skip).limit(limit)
        templates_data = []
        async for template in templates_cursor:
            templates_data.append(template)
        
        templates = []
        for template_data in templates_data:
            template_data["id"] = str(template_data.pop("_id"))
            templates.append(IndustryTemplate(**template_data))
            
        return templates
    
    async def update_template(self, template_id: str, 
                            template_update: IndustryTemplateUpdate) -> Optional[IndustryTemplate]:
        """更新行业模板"""
        update_data = template_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now()
            
            mongodb = await self.db_service.get_mongodb()
            if mongodb is None:
                raise RuntimeError("数据库未初始化")
            result = await mongodb[self.collection_name].update_one(
                {"_id": template_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_template(template_id)
        return None
    
    async def delete_template(self, template_id: str) -> bool:
        """删除行业模板"""
        mongodb = await self.db_service.get_mongodb()
        if mongodb is None:
            raise RuntimeError("数据库未初始化")
        result = await mongodb[self.collection_name].delete_one({"_id": template_id})
        
        return result.deleted_count > 0