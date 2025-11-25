from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
import re
from datetime import datetime

from agents.analyst.analyst_agent import AnalystAgent
from repositories.knowledge_repository import KnowledgeRepository
from utils.config import settings
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class LLMAnalystAgent(AnalystAgent):
    """
    基于LLM的分析师智能体实现
    使用大语言模型处理自然语言查询，生成数据库查询，执行代码等
    """
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        self.knowledge_repository = knowledge_repository
        self.openai_service = OpenAIService()
        self.max_complexity_level = 5  # 最大查询复杂度级别
        logger.info("LLMAnalystAgent初始化完成")
    
    async def process_query(self, query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户自然语言查询的完整流程
        """
        try:
            logger.info(f"处理查询: {query[:50]}... 用户: {user_id}")
            
            # 1. 分析查询复杂度
            complexity_result = await self.analyze_query_complexity(query)
            if complexity_result['level'] > self.max_complexity_level:
                return self.format_response(
                    False, 
                    None, 
                    f"查询过于复杂，请简化查询或拆分为多个简单查询。复杂度级别: {complexity_result['level']}"
                )
            
            # 2. 生成数据库查询
            query_result = await self.generate_query(query)
            if not query_result['success']:
                return query_result
            
            # 3. 执行查询
            execute_result = await self.execute_query(query_result['data'], user_id)
            if not execute_result['success']:
                return execute_result
            
            # 4. 解释结果
            explain_result = await self.explain_results(query, execute_result['data'])
            
            # 5. 组合结果
            final_result = {
                'query': query,
                'database_query': query_result['data'],
                'complexity': complexity_result,
                'results': execute_result['data'],
                'explanation': explain_result['data']['explanation'],
                'visualization_suggestions': explain_result['data'].get('visualization_suggestions', []),
                'timestamp': datetime.now().isoformat()
            }
            
            return self.format_response(True, final_result)
            
        except Exception as e:
            logger.exception(f"处理查询时出错: {query}")
            return self.format_response(False, None, f"查询处理失败: {str(e)}")
    
    async def generate_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        将自然语言查询转换为数据库查询
        """
        try:
            # 获取知识图谱的元数据
            schema_info = await self.knowledge_repository.get_graph_schema()
            
            # 构建提示词
            prompt = f"""
            你是一个知识图谱查询生成器，需要将自然语言查询转换为Neo4j Cypher查询。
            
            知识图谱结构信息:
            {json.dumps(schema_info, ensure_ascii=False, indent=2)}
            
            请将以下自然语言查询转换为有效的Cypher查询:
            {natural_language_query}
            
            输出格式要求:
            {
                "query": "生成的Cypher查询语句",
                "query_type": "查询类型(如节点查询、关系查询、路径查询等)",
                "description": "查询功能描述"
            }
            
            请注意:
            1. 查询必须安全，避免删除或修改操作
            2. 使用参数化查询防止注入
            3. 确保查询效率，避免全图扫描
            4. 只返回必要的字段
            """
            
            # 调用LLM生成查询
            response = await self.openai_service.chat_completion(
                messages=[{"role": "system", "content": "你是一个专业的知识图谱查询生成器。"},
                         {"role": "user", "content": prompt}],
                model=settings.LLM_MODEL,
                response_format={"type": "json_object"}
            )
            
            query_data = json.loads(response)
            return self.format_response(True, query_data)
            
        except Exception as e:
            logger.exception(f"生成查询时出错: {natural_language_query}")
            return self.format_response(False, None, f"生成查询失败: {str(e)}")
    
    async def execute_query(self, query: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行生成的数据库查询
        """
        try:
            cypher_query = query.get('query', '')
            
            # 安全检查
            if await self._is_unsafe_query(cypher_query):
                return self.format_response(False, None, "查询包含不安全操作，已拒绝执行")
            
            # 执行查询
            results = await self.knowledge_repository.execute_query(
                cypher_query,
                user_id=user_id
            )
            
            # 格式化结果
            formatted_results = {
                'records': results,
                'record_count': len(results),
                'query_executed': cypher_query,
                'query_type': query.get('query_type', 'unknown')
            }
            
            return self.format_response(True, formatted_results)
            
        except Exception as e:
            logger.exception(f"执行查询时出错: {query.get('query', '')}")
            return self.format_response(False, None, f"查询执行失败: {str(e)}")
    
    async def explain_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        解释查询结果
        """
        try:
            prompt = f"""
            你是一个数据分析师，需要解释知识图谱查询结果并提供见解。
            
            用户查询:
            {query}
            
            执行的查询:
            {results.get('query_executed', '')}
            
            查询结果:
            {json.dumps(results.get('records', []), ensure_ascii=False, indent=2)}
            
            请提供:
            1. 对查询结果的清晰解释
            2. 从数据中获得的见解
            3. 可能的可视化建议
            
            输出格式:
            {
                "explanation": "对结果的解释",
                "insights": ["见解1", "见解2", ...],
                "visualization_suggestions": ["可视化建议1", "可视化建议2", ...]
            }
            """
            
            response = await self.openai_service.chat_completion(
                messages=[{"role": "system", "content": "你是一个专业的数据分析师。"},
                         {"role": "user", "content": prompt}],
                model=settings.LLM_MODEL,
                response_format={"type": "json_object"}
            )
            
            explanation = json.loads(response)
            return self.format_response(True, explanation)
            
        except Exception as e:
            logger.exception(f"解释结果时出错")
            return self.format_response(False, None, f"结果解释失败: {str(e)}")
    
    async def execute_code(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行代码片段（代码解释器功能）
        """
        try:
            logger.info(f"执行代码: {language} 代码长度: {len(code)} 字符")
            
            # 安全检查
            if await self._contains_dangerous_code(code):
                return self.format_response(False, None, "代码包含潜在危险操作，已拒绝执行")
            
            # 构建执行环境
            execution_context = {
                'results': context.get('results', {}),
                'query': context.get('query', ''),
                'knowledge_repository': self.knowledge_repository,
                'available_libraries': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'networkx'],
                'language': language
            }
            
            # 对于简单的Python代码，可以在沙箱中执行
            if language.lower() == 'python' and len(code) < 1000:
                # 这里可以集成一个安全的代码执行环境
                # 为了安全，我们先使用LLM模拟执行结果
                prompt = f"""
                请模拟执行以下Python代码，并返回执行结果。代码是在分析知识图谱数据：
                
                {code}
                
                执行上下文数据:
                {json.dumps(execution_context['results'], ensure_ascii=False, indent=2)}
                
                请提供:
                1. 执行结果的详细描述
                2. 输出内容（如果有）
                3. 任何图表或可视化的描述（如果有）
                
                输出格式:
                {
                    "output": "代码执行输出",
                    "result_description": "结果描述",
                    "visualization": "可视化描述（如果有）"
                }
                """
                
                response = await self.openai_service.chat_completion(
                    messages=[{"role": "system", "content": "你是一个Python代码执行模拟器。"},
                             {"role": "user", "content": prompt}],
                    model=settings.LLM_MODEL,
                    response_format={"type": "json_object"}
                )
                
                execution_result = json.loads(response)
                return self.format_response(True, execution_result)
            else:
                # 对于其他语言或复杂代码，返回受限信息
                return self.format_response(
                    False, 
                    None, 
                    f"当前仅支持简单Python代码的模拟执行，其他语言或复杂代码暂不支持。"
                )
                
        except Exception as e:
            logger.exception(f"执行代码时出错")
            return self.format_response(False, None, f"代码执行失败: {str(e)}")
    
    async def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        分析查询复杂度
        """
        try:
            prompt = f"""
            请分析以下自然语言查询的复杂度，并返回复杂度级别(1-10)和理由。
            复杂度考虑因素：查询的实体数量、关系深度、计算复杂度、数据量预估等。
            
            查询:
            {query}
            
            输出格式:
            {
                "level": 复杂度级别(1-10),
                "reason": "复杂度评估理由",
                "estimated_execution_time": "预估执行时间(毫秒)",
                "optimization_suggestions": ["优化建议1", "优化建议2"]
            }
            """
            
            response = await self.openai_service.chat_completion(
                messages=[{"role": "system", "content": "你是一个查询复杂度分析师。"},
                         {"role": "user", "content": prompt}],
                model=settings.LLM_MODEL,
                response_format={"type": "json_object"}
            )
            
            complexity = json.loads(response)
            return complexity
            
        except Exception as e:
            logger.exception(f"分析查询复杂度时出错")
            # 返回默认复杂度
            return {
                "level": 3,
                "reason": "复杂度分析失败，使用默认值",
                "estimated_execution_time": "unknown",
                "optimization_suggestions": []
            }
    
    async def _is_unsafe_query(self, query: str) -> bool:
        """
        检查查询是否安全
        """
        unsafe_patterns = [
            r'\b(DELETE|REMOVE|SET|CREATE|MERGE|DROP)\b',
            r'\b(FOR EACH|WHILE)\b',
            r'\b(LOAD CSV)\b',
            r'\b(START)\b',
            r'\b(STOP)\b',
            r'\b(KILL)\b',
            r'\b(SLEEP)\b'
        ]
        
        query_lower = query.lower()
        for pattern in unsafe_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(f"检测到不安全查询模式: {pattern}")
                return True
        
        # 检查嵌套深度
        if query_lower.count('match') > 3:
            logger.warning(f"查询嵌套过深: {query_lower.count('match')}个MATCH语句")
            return True
        
        return False
    
    async def _contains_dangerous_code(self, code: str) -> bool:
        """
        检查代码是否包含危险操作
        """
        dangerous_patterns = [
            r'\bos\.',
            r'\bsys\.',
            r'\bsubprocess\.',
            r'\bos\s*\[\s*\'\w+\'\s*\]',
            r'\bopen\s*\(',
            r'\bexec\s*\(',
            r'\beval\s*\(',
            r'\bcompile\s*\(',
            r'\bglobals\s*\(',
            r'\blocals\s*\(',
            r'\b__[a-zA-Z0-9_]+__\b',
            r'\bimport\s+(os|sys|subprocess|shutil|ctypes)',
            r'\bfrom\s+(os|sys|subprocess|shutil|ctypes)\s+import',
            r'\bsocket\.',
            r'\bthreading\.',
            r'\bmultiprocessing\.',
            r'\btime\s*\.sleep'
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, code_lower, re.IGNORECASE):
                logger.warning(f"检测到危险代码模式: {pattern}")
                return True
        
        return False