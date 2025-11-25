from typing import Dict, List, Any, Optional
import logging
from agents.analyst.analyst_agent import AnalystAgent
from agents.analyst.llm_analyst_agent import LLMAnalystAgent
from repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


def create_analyst_agent(
    agent_type: str = "llm", 
    knowledge_repository: Optional[KnowledgeRepository] = None
) -> AnalystAgent:
    """
    创建分析师智能体实例的工厂函数
    
    Args:
        agent_type: 智能体类型，默认为"llm"
        knowledge_repository: 知识仓库实例
        
    Returns:
        AnalystAgent: 分析师智能体实例
    """
    if knowledge_repository is None:
        knowledge_repository = KnowledgeRepository()
    
    if agent_type.lower() == "llm":
        return LLMAnalystAgent(knowledge_repository)
    else:
        raise ValueError(f"不支持的分析师智能体类型: {agent_type}")


class AnalystAgentService:
    """
    分析师智能体服务类（单例模式）
    提供统一的接口来使用分析师智能体
    """
    _instance = None
    _lock = False
    
    def __new__(cls, knowledge_repository: Optional[KnowledgeRepository] = None):
        if cls._instance is None:
            # 简单的线程安全实现
            while cls._lock:
                pass
            
            cls._lock = True
            try:
                if cls._instance is None:
                    cls._instance = super(AnalystAgentService, cls).__new__(cls)
                    # 初始化服务
                    cls._instance._initialize(knowledge_repository)
            finally:
                cls._lock = False
        
        return cls._instance
    
    def _initialize(self, knowledge_repository: Optional[KnowledgeRepository] = None):
        """
        初始化服务
        """
        self.knowledge_repository = knowledge_repository or KnowledgeRepository()
        self.agent = create_analyst_agent("llm", self.knowledge_repository)
        logger.info("AnalystAgentService初始化完成")
    
    @classmethod
    def get_instance(cls, knowledge_repository: Optional[KnowledgeRepository] = None) -> "AnalystAgentService":
        """
        获取服务实例
        
        Args:
            knowledge_repository: 知识仓库实例
            
        Returns:
            AnalystAgentService: 服务实例
        """
        if cls._instance is None:
            cls._instance = cls(knowledge_repository)
        return cls._instance
    
    async def analyze_query(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        分析用户查询
        
        Args:
            query: 用户查询
            user_id: 用户ID
            
        Returns:
            Dict: 分析结果
        """
        try:
            logger.info(f"分析查询: {query[:50]}... 用户: {user_id}")
            result = await self.agent.process_query(query, user_id)
            logger.info(f"查询分析完成，成功: {result['success']}")
            return result
        except Exception as e:
            logger.exception(f"分析查询时出错")
            return {
                "success": False,
                "error": f"查询分析失败: {str(e)}"
            }
    
    async def execute_code(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行代码片段
        
        Args:
            code: 代码内容
            language: 编程语言
            context: 执行上下文
            
        Returns:
            Dict: 执行结果
        """
        try:
            logger.info(f"执行代码: {language} 长度: {len(code)} 用户: {context.get('user_id') if context else None}")
            result = await self.agent.execute_code(code, language, context)
            logger.info(f"代码执行完成，成功: {result['success']}")
            return result
        except Exception as e:
            logger.exception(f"执行代码时出错")
            return {
                "success": False,
                "error": f"代码执行失败: {str(e)}"
            }
    
    async def get_query_suggestions(self, current_query: str, user_id: Optional[str] = None) -> List[str]:
        """
        获取查询建议
        
        Args:
            current_query: 当前查询
            user_id: 用户ID
            
        Returns:
            List: 查询建议列表
        """
        try:
            logger.info(f"获取查询建议: {current_query[:50]}... 用户: {user_id}")
            
            # 这里可以从OpenAIService获取建议，或基于历史记录生成
            # 为简化实现，返回一些通用建议
            suggestions = [
                f"{current_query} 的详细信息",
                f"与 {current_query} 相关的实体",
                f"{current_query} 的关系网络",
                f"{current_query} 的统计分析",
                f"{current_query} 的历史趋势"
            ]
            
            return suggestions
        except Exception as e:
            logger.exception(f"获取查询建议时出错")
            return []
    
    async def create_dashboard(self, queries: List[str], title: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        创建数据仪表盘
        
        Args:
            queries: 查询列表
            title: 仪表盘标题
            user_id: 用户ID
            
        Returns:
            Dict: 仪表盘信息
        """
        try:
            logger.info(f"创建仪表盘: {title} 查询数: {len(queries)} 用户: {user_id}")
            
            # 分析每个查询
            query_results = []
            for query in queries:
                result = await self.analyze_query(query, user_id)
                if result['success']:
                    query_results.append({
                        "query": query,
                        "results": result['data']
                    })
            
            dashboard = {
                "title": title,
                "created_at": "2025-11-24T17:45:00Z",  # 实际应使用当前时间
                "query_count": len(query_results),
                "queries": query_results
            }
            
            return {
                "success": True,
                "data": dashboard
            }
        except Exception as e:
            logger.exception(f"创建仪表盘时出错")
            return {
                "success": False,
                "error": f"仪表盘创建失败: {str(e)}"
            }
    
    def get_available_features(self) -> List[Dict[str, Any]]:
        """
        获取可用功能列表
        
        Returns:
            List: 功能列表
        """
        return [
            {
                "name": "query_analysis",
                "description": "自然语言查询分析与执行",
                "parameters": ["query", "user_id"]
            },
            {
                "name": "code_execution",
                "description": "安全的代码执行环境",
                "parameters": ["code", "language", "context"]
            },
            {
                "name": "query_suggestions",
                "description": "智能查询建议",
                "parameters": ["current_query", "user_id"]
            },
            {
                "name": "dashboard_creation",
                "description": "创建数据仪表盘",
                "parameters": ["queries", "title", "user_id"]
            }
        ]