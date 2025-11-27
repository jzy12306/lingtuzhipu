import logging
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from datetime import datetime
import re


from src.repositories.query_history_repository import QueryHistoryRepository
from src.schemas.analyst import QueryComplexity

logger = logging.getLogger(__name__)


class AnalystAgent:
    """分析师智能体服务，处理自然语言查询和代码执行"""
    
    def __init__(self):
        self.query_history_repo = QueryHistoryRepository()
        self.code_sandbox = None
        self.is_initialized = False
    
    async def initialize(self):
        """初始化分析师智能体"""
        try:
            logger.info("正在初始化分析师智能体...")
            # 初始化代码沙箱（如果需要）
            # self.code_sandbox = CodeSandbox()
            self.is_initialized = True
            logger.info("分析师智能体初始化成功")
        except Exception as e:
            logger.error(f"初始化分析师智能体失败: {str(e)}")
            raise
    
    async def analyze_query_complexity(self, query: str) -> QueryComplexity:
        """分析查询复杂度"""
        try:
            # 基于查询长度和复杂度关键词判断
            query_len = len(query)
            
            # 简单规则判断复杂度
            if query_len < 20:
                return QueryComplexity.SIMPLE
            elif query_len < 50:
                return QueryComplexity.MODERATE
            elif query_len < 100:
                return QueryComplexity.COMPLEX
            else:
                return QueryComplexity.ADVANCED
                
        except Exception as e:
            logger.error(f"分析查询复杂度失败: {str(e)}")
            return QueryComplexity.MODERATE  # 默认返回中等复杂度
    
    async def process_query(self, query: str, user_context: Dict[str, Any], 
                          document_ids: Optional[List[str]] = None,
                          include_code: bool = True) -> Dict[str, Any]:
        """处理自然语言查询"""
        start_time = time.time()
        
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            logger.info(f"收到查询请求: {query}")
            logger.info(f"用户上下文: {user_context}")
            
            # 构建查询上下文
            context = await self._build_query_context(query, document_ids)
            logger.info(f"构建的查询上下文: {context}")
            
            # 调用LLM进行查询处理
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个智能知识图谱分析助手。基于提供的上下文信息，回答用户的查询。"
                    },
                    {
                        "role": "user",
                        "content": f"上下文信息：\n{json.dumps(context, ensure_ascii=False)}\n\n用户查询：{query}\n\n请提供详细且准确的回答。"
                    }
                ],
                temperature=0.1
            )
            
            logger.info(f"LLM响应: {llm_response}")
            
            # 提取答案
            answer = llm_response.get("content", "")
            logger.info(f"提取的答案: {answer}")
            
            # 生成代码（如果需要）
            generated_code = None
            if include_code:
                generated_code = await self._generate_query_code(query, context)
            
            # 获取相关实体
            related_entities = await self._extract_related_entities(query, context)
            
            # 构建可视化数据
            visualization_data = await self._generate_visualization_data(query, answer)
            
            result = {
                "id": f"query_{int(time.time())}_{user_context.get('user_id', 'anonymous')}",
                "summary": self._extract_summary(answer),
                "detailed_answer": answer,
                "generated_code": generated_code,
                "visualization_data": visualization_data,
                "related_entities": related_entities,
                "confidence": 0.85,  # 模拟置信度
                "execution_time": time.time() - start_time
            }
            
            logger.info(f"返回的查询结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"处理查询失败: {str(e)}", exc_info=True)
            # 抛出异常，让上层处理
            raise
    
    async def stream_query_processing(self, query: str, user_context: Dict[str, Any],
                                    document_ids: Optional[List[str]] = None) -> AsyncGenerator[Dict[str, Any], None]:

        """流式处理查询"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 流式返回处理步骤
            yield {"type": "processing", "message": "正在分析查询..."}
            
            # 获取上下文信息
            context = await self._build_query_context(query, document_ids)
            yield {"type": "processing", "message": "正在获取相关知识..."}
            
            # 模拟处理延迟
            await asyncio.sleep(0.5)
            yield {"type": "processing", "message": "正在生成答案..."}
            
            # 调用LLM获取结果
            llm_stream = service_factory.llm_service.stream_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个智能知识图谱分析助手。"
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.1
            )
            
            # 流式返回LLM结果
            full_answer = ""
            async for chunk in llm_stream:
                content = chunk.get("content", "")
                full_answer += content
                yield {"type": "content", "content": content}
            
            # 返回完成信息
            yield {"type": "complete", "summary": self._extract_summary(full_answer)}
            
        except Exception as e:
            logger.error(f"流式处理查询失败: {str(e)}")
            yield {"type": "error", "error": str(e)}
    
    async def execute_code(self, code: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """安全执行代码"""
        start_time = time.time()
        
        try:
            # 模拟代码执行
            # 在实际实现中，应该使用沙箱环境
            
            # 简单的模拟执行结果
            if "import" in code:
                output = "代码执行成功: 已导入模块"
            elif "print" in code:
                output = "代码执行成功: 输出内容"
            elif "error" in code.lower():
                raise Exception("模拟代码执行错误")
            else:
                output = "代码执行成功"
            
            return {
                "success": True,
                "output": output,
                "error": None,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def validate_code_safety(self, code: str) -> bool:
        """验证代码安全性"""
        # 简单的安全检查
        dangerous_patterns = [
            r"os\.(system|popen|exec)",
            r"subprocess\.",
            r"__import__\(",
            r"eval\(",
            r"exec\(",
            r"compile\(",
            r"globals\(",
            r"locals\(",
            r"open\(",
            r"file\(",
            r"pickle\.",
            r"socket\.",
            r"threading\.",
            r"multiprocessing\."
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                logger.warning(f"检测到潜在危险代码: {pattern}")
                return False
        
        return True
    
    async def analyze_document(self, document: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """分析文档"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 调用LLM进行文档分析
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个文档分析专家。请对提供的文档进行{analysis_type}分析。"
                    },
                    {
                        "role": "user",
                        "content": f"文档标题：{document.get('title', '未知')}\n文档内容：{document.get('content', '').strip()[:2000]}..."
                    }
                ],
                temperature=0.1
            )
            
            # 解析分析结果
            analysis_text = llm_response.get("content", "")
            
            # 模拟分析结果
            return {
                "summary": analysis_text,
                "key_findings": ["发现1", "发现2", "发现3"],
                "entities": [{"name": "实体1", "type": "类型1"}],
                "relationships": [{"source": "实体1", "target": "实体2", "type": "相关"}],
                "sentiment": {"positive": 0.7, "negative": 0.1, "neutral": 0.2},
                "topics": [{"name": "主题1", "score": 0.8}],
                "recommendations": ["建议1", "建议2"]
            }
            
        except Exception as e:
            logger.error(f"分析文档失败: {str(e)}")
            raise
    
    async def analyze_knowledge_graph(self, graph_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """分析知识图谱"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 调用LLM分析图谱数据
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个知识图谱分析专家。请对提供的图谱数据进行{analysis_type}分析。"
                    },
                    {
                        "role": "user",
                        "content": f"图谱数据：\n{json.dumps(graph_data, ensure_ascii=False)}"
                    }
                ],
                temperature=0.1
            )
            
            return {
                "summary": llm_response.get("content", ""),
                "patterns": ["模式1", "模式2"],
                "insights": ["洞察1", "洞察2"],
                "recommendations": ["建议1", "建议2"]
            }
            
        except Exception as e:
            logger.error(f"分析知识图谱失败: {str(e)}")
            raise
    
    async def save_query_history(self, user_id: str, query: str, result_summary: str,
                               execution_time: float, complexity: QueryComplexity):
        """保存查询历史"""
        try:
            await self.query_history_repo.create({
                "user_id": user_id,
                "query": query,
                "result_summary": result_summary,
                "execution_time": execution_time,
                "complexity": complexity,
                "timestamp": datetime.now()
            })
        except Exception as e:
            logger.error(f"保存查询历史失败: {str(e)}")
    
    async def get_user_query_history(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户查询历史"""
        try:
            return await self.query_history_repo.find_by_user_id(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"获取用户查询历史失败: {str(e)}")
            return []
    
    async def delete_query_history(self, history_id: str, user_id: str) -> bool:
        """删除查询历史"""
        try:
            result = await self.query_history_repo.delete_by_id_and_user_id(
                history_id=history_id,
                user_id=user_id
            )
            return result > 0
        except Exception as e:
            logger.error(f"删除查询历史失败: {str(e)}")
            return False
    
    async def get_query_suggestions(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取查询建议"""
        try:
            # 基于用户历史和当前查询生成建议
            suggestions = [
                {"text": f"{query}的详细分析", "relevance_score": 0.9, "category": "扩展"},
                {"text": f"与{query}相关的实体", "relevance_score": 0.85, "category": "相关"},
                {"text": f"{query}的统计数据", "relevance_score": 0.8, "category": "统计"},
                {"text": f"{query}的关系图谱", "relevance_score": 0.75, "category": "可视化"},
                {"text": f"{query}的最新研究", "relevance_score": 0.7, "category": "研究"}
            ]
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"获取查询建议失败: {str(e)}")
            return []
    
    async def _build_query_context(self, query: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """构建查询上下文"""
        context = {}
        
        # 使用延迟导入避免循环依赖
        from src.services.service_factory import service_factory
        
        # 获取相关文档
        if document_ids:
            documents = []
            for doc_id in document_ids[:5]:  # 限制数量
                try:
                    doc = await service_factory.document_service.get_document(doc_id)
                    if doc:
                        documents.append({
                            "id": doc.id,
                            "title": doc.title,
                            "content": doc.content[:500] + "..."
                        })
                except Exception as e:
                    logger.error(f"获取文档失败 {doc_id}: {str(e)}")
            context["documents"] = documents
        
        # 获取相关知识图谱数据
        graph_entities = await service_factory.knowledge_graph_service.search_entities(query)
        context["graph_data"] = {
            "entities": graph_entities[:10]
        }
        
        return context
    
    async def _generate_query_code(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """为查询生成代码"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 调用LLM生成代码
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个代码生成助手。基于用户查询和上下文，生成相关的Python分析代码。"
                    },
                    {
                        "role": "user",
                        "content": f"查询：{query}\n上下文：{json.dumps(context, ensure_ascii=False)}\n请生成Python代码来分析这个查询。"
                    }
                ],
                temperature=0.2
            )
            
            return llm_response.get("content", None)
            
        except Exception as e:
            logger.error(f"生成代码失败: {str(e)}")
            return None
    
    async def _extract_related_entities(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取相关实体"""
        # 从上下文的图谱数据中提取实体
        entities = context.get("graph_data", {}).get("entities", [])
        
        # 转换实体格式，确保前端需要的字段存在
        result_entities = []
        for entity in entities[:5]:  # 限制返回数量
            result_entities.append({
                "name": entity.name if hasattr(entity, 'name') else entity.get('name', ''),
                "type": entity.type if hasattr(entity, 'type') else entity.get('type', '未知')
            })
        
        return result_entities
    
    async def _generate_visualization_data(self, query: str, answer: str) -> Optional[Dict[str, Any]]:
        """生成可视化数据"""
        # 简单的模拟可视化数据
        return {
            "type": "chart",
            "chartType": "bar",
            "data": {
                "labels": ["类别1", "类别2", "类别3"],
                "datasets": [{
                    "label": "数值",
                    "data": [10, 20, 30]
                }]
            }
        }
    
    def _extract_summary(self, text: str, max_length: int = 100) -> str:
        """提取文本摘要"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    async def close(self):
        """关闭服务"""
        logger.info("正在关闭分析师智能体...")
        self.is_initialized = False


