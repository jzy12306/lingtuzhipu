from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class AnalystAgent(ABC):
    """
    分析师智能体抽象基类
    负责处理用户查询，生成数据库查询，执行查询并解释结果
    """
    
    @abstractmethod
    async def process_query(self, query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户自然语言查询
        
        Args:
            query: 用户的自然语言查询
            user_id: 用户ID（可选）
            context: 上下文信息（可选）
            
        Returns:
            Dict: 包含查询结果和解释的字典
        """
        pass
    
    @abstractmethod
    async def generate_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        将自然语言查询转换为数据库查询
        
        Args:
            natural_language_query: 自然语言查询
            
        Returns:
            Dict: 包含数据库查询和元数据的字典
        """
        pass
    
    @abstractmethod
    async def execute_query(self, query: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行生成的数据库查询
        
        Args:
            query: 要执行的查询
            user_id: 用户ID（可选）
            
        Returns:
            Dict: 查询执行结果
        """
        pass
    
    @abstractmethod
    async def explain_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        解释查询结果
        
        Args:
            query: 原始查询
            results: 查询结果
            
        Returns:
            Dict: 包含解释的结果
        """
        pass
    
    @abstractmethod
    async def execute_code(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行代码片段（代码解释器功能）
        
        Args:
            code: 要执行的代码
            language: 代码语言
            context: 上下文数据（可选）
            
        Returns:
            Dict: 代码执行结果
        """
        pass
    
    @abstractmethod
    async def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        分析查询复杂度
        
        Args:
            query: 自然语言查询
            
        Returns:
            Dict: 复杂度分析结果
        """
        pass
    
    def format_response(self, success: bool, data: Any, error: Optional[str] = None) -> Dict[str, Any]:
        """
        格式化响应
        
        Args:
            success: 是否成功
            data: 响应数据
            error: 错误信息（可选）
            
        Returns:
            Dict: 格式化的响应
        """
        response = {
            "success": success,
            "data": data
        }
        if not success and error:
            response["error"] = error
        return response