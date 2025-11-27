from typing import Optional, Dict, Any, List
from src.repositories.knowledge_repository import KnowledgeRepository
from src.services.document_service import DocumentService


class AnalystAgentService:
    """
    分析师代理服务
    处理与分析师代理相关的业务逻辑
    """
    
    def __init__(self, knowledge_repository: KnowledgeRepository, document_service: DocumentService):
        self.knowledge_repository = knowledge_repository
        self.document_service = document_service
        # 不再直接导入analyst_agent，改为在需要时通过service_factory获取
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        分析查询复杂度
        """
        # 使用延迟导入避免循环依赖
        from src.services.service_factory import service_factory
        
        # 调用分析师代理进行查询分析
        result = await service_factory.analyst_agent.analyze_query_complexity(query)
        return result
    
    async def generate_answer(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成查询答案
        """
        # 这里可以添加更多的业务逻辑
        # 比如基于用户上下文提供个性化的回答
        return f"Answer to: {query}"
    
    async def get_query_history(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取查询历史
        """
        # 实现查询历史获取逻辑
        return []