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
            
            # 获取相关关系
            related_relationships = await self._extract_related_relationships(query, context, related_entities)
            
            # 构建可视化数据
            visualization_data = await self._generate_visualization_data(query, answer)
            
            result = {
                "id": f"query_{int(time.time())}_{user_context.get('user_id', 'anonymous')}",
                "summary": self._extract_summary(answer),
                "detailed_answer": answer,
                "generated_code": generated_code,
                "visualization_data": visualization_data,
                "related_entities": related_entities,
                "related_relationships": related_relationships,
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
        """使用大模型提取相关实体"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 从文档内容中获取文本
            documents = context.get("documents", [])
            doc_texts = [doc.get("content", "") for doc in documents]
            full_text = "\n".join(doc_texts)
            
            # 构建提示词，使用大模型提取实体
            prompt = f"""请从以下文本中提取相关实体，包括公司、产品、人物、概念、事件等。
            请确保提取至少5个相关实体，实体名称准确，类型正确。
            请按照以下JSON格式返回：
            [
                {{"name": "实体名称", "type": "实体类型"}}
            ]
            
            文本内容：
            {full_text}
            
            查询内容：
            {query}
            """
            
            logger.info(f"实体提取提示词: {prompt}")
            
            # 调用大模型提取实体
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个实体提取专家，能够从文本中准确提取各种类型的实体。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            logger.info(f"大模型实体提取响应: {llm_response}")
            
            # 解析大模型返回的结果
            entities_json = llm_response.get("content", "[]")
            entities = json.loads(entities_json)
            
            # 转换实体格式，确保前端需要的字段存在
            result_entities = []
            seen_entities = set()  # 用于去重
            
            # 无效实体列表
            invalid_entities = ["查询内容", "我", "给我介绍", "一下", "介绍", "内容", "查询"]
            
            for entity in entities[:10]:  # 限制返回数量为10个
                name = entity.get("name", "")
                entity_type = entity.get("type", "未知")
                
                # 跳过无效实体
                if not name or name in seen_entities or name in invalid_entities:
                    continue
                
                # 添加到已见集合
                seen_entities.add(name)
                
                result_entities.append({
                    "name": name,
                    "type": entity_type,
                    "properties": {
                        "source": "llm_extraction",
                        "confidence": 0.95  # 大模型提取的实体置信度较高
                    }
                })
            
            # 确保查询主题本身作为核心实体存在
            query_topic = query.strip()
            if query_topic not in seen_entities and len(query_topic) > 2:
                # 尝试确定查询主题的类型
                topic_type = "概念"  # 默认类型
                
                # 简单的类型判断
                if any(keyword in query_topic for keyword in ["公司", "集团", "企业", "科技", "有限责任"]):
                    topic_type = "公司"
                elif any(keyword in query_topic for keyword in ["产品", "服务", "平台", "软件", "应用", "系统"]):
                    topic_type = "产品"
                elif any(keyword in query_topic for keyword in ["人物", "创始人", "CEO", "总裁", "董事长", "专家"]):
                    topic_type = "人物"
                elif any(keyword in query_topic for keyword in ["机构", "研究院", "实验室", "部门", "组织"]):
                    topic_type = "机构"
                elif any(keyword in query_topic for keyword in ["技术", "算法", "理论", "方法", "模型"]):
                    topic_type = "技术"
                elif any(keyword in query_topic for keyword in ["事件", "活动", "会议", "发布", "上市"]):
                    topic_type = "事件"
                
                # 将查询主题添加为核心实体
                result_entities.insert(0, {
                    "name": query_topic,
                    "type": topic_type,
                    "properties": {
                        "source": "query_topic",
                        "confidence": 1.0,
                        "is_core": True
                    }
                })
                seen_entities.add(query_topic)
            
            # 如果实体数量不足，基于核心实体类型动态生成相关实体
            if len(result_entities) < 5:
                logger.info(f"实体数量不足，基于核心实体类型动态生成相关实体")
                
                # 获取核心实体
                core_entity = result_entities[0] if result_entities else {"name": query, "type": "概念"}
                core_entity_name = core_entity["name"]
                
                # 常见公司的具体实体映射
                company_specific_entities = {
                    "阿里巴巴": {
                        "人物": ["马云", "张勇"],
                        "产品": ["淘宝", "支付宝", "阿里云", "天猫"],
                        "公司": ["菜鸟网络", "达摩院"]
                    },
                    "腾讯": {
                        "人物": ["马化腾", "张小龙"],
                        "产品": ["微信", "QQ", "腾讯云", "王者荣耀"],
                        "公司": ["阅文集团", "腾讯音乐"]
                    },
                    "字节跳动": {
                        "人物": ["张一鸣"],
                        "产品": ["抖音", "TikTok", "今日头条"],
                        "公司": ["火山引擎"]
                    },
                    "苹果": {
                        "人物": ["史蒂夫·乔布斯", "蒂姆·库克"],
                        "产品": ["iPhone", "iPad", "Mac", "iOS"],
                        "公司": ["苹果零售"]
                    }
                }
                
                # 基于核心实体类型生成相关实体
                generated_entities = []
                
                # 如果是常见公司，使用具体的实体名称
                if core_entity['type'] == "公司" and core_entity_name in company_specific_entities:
                    specific_entities = company_specific_entities[core_entity_name]
                    for entity_type, entity_names in specific_entities.items():
                        for name in entity_names:
                            if name not in seen_entities:
                                generated_entities.append({
                                    "name": name,
                                    "type": entity_type
                                })
                else:
                    # 通用实体生成规则
                    generic_entities_map = {
                        "公司": [
                            {"name": "创始人", "type": "人物"},
                            {"name": "核心产品", "type": "产品"},
                            {"name": "主要业务", "type": "业务"},
                            {"name": "竞争对手", "type": "公司"},
                            {"name": "核心技术", "type": "技术"},
                            {"name": "子公司", "type": "公司"},
                            {"name": "合作伙伴", "type": "公司"}
                        ],
                        "产品": [
                            {"name": "开发公司", "type": "公司"},
                            {"name": "核心功能", "type": "功能"},
                            {"name": "目标用户", "type": "人物"},
                            {"name": "竞品", "type": "产品"},
                            {"name": "核心技术", "type": "技术"},
                            {"name": "开发者", "type": "人物"}
                        ],
                        "人物": [
                            {"name": "所属公司", "type": "公司"},
                            {"name": "主要成就", "type": "事件"},
                            {"name": "代表作品", "type": "产品"},
                            {"name": "合作伙伴", "type": "人物"},
                            {"name": "影响力", "type": "概念"}
                        ],
                        "机构": [
                            {"name": "负责人", "type": "人物"},
                            {"name": "研究方向", "type": "技术"},
                            {"name": "研究成果", "type": "产品"},
                            {"name": "合作机构", "type": "机构"}
                        ],
                        "技术": [
                            {"name": "应用领域", "type": "领域"},
                            {"name": "发明者", "type": "人物"},
                            {"name": "相关产品", "type": "产品"},
                            {"name": "研究机构", "type": "机构"}
                        ],
                        "事件": [
                            {"name": "参与方", "type": "公司"},
                            {"name": "负责人", "type": "人物"},
                            {"name": "影响", "type": "概念"},
                            {"name": "相关产品", "type": "产品"}
                        ],
                        "概念": [
                            {"name": "应用场景", "type": "产品"},
                            {"name": "相关技术", "type": "技术"},
                            {"name": "研究机构", "type": "机构"},
                            {"name": "发展历程", "type": "事件"}
                        ]
                    }
                    
                    # 获取适合当前核心实体类型的生成实体列表
                    generated_entities = generic_entities_map.get(core_entity['type'], [
                        {"name": "相关概念", "type": "概念"},
                        {"name": "相关实体", "type": "实体"},
                        {"name": "影响", "type": "概念"}
                    ])
                
                # 添加生成的实体
                for entity in generated_entities:
                    name = entity["name"]
                    # 对于通用实体名称，添加核心实体名称作为前缀，否则使用具体名称
                    if name in ["创始人", "核心产品", "主要业务", "竞争对手", "核心技术", "子公司", "合作伙伴", 
                               "开发公司", "核心功能", "目标用户", "竞品", "开发者", "所属公司", "主要成就", 
                               "代表作品", "影响力", "负责人", "研究方向", "研究成果", "合作机构", "应用领域", 
                               "发明者", "相关产品", "研究机构", "参与方", "影响", "应用场景", "相关技术", "发展历程", 
                               "相关概念", "相关实体"]:
                        full_name = f"{core_entity_name}{name}"
                    else:
                        full_name = name
                    
                    if full_name not in seen_entities:
                        seen_entities.add(full_name)
                        result_entities.append({
                            "name": full_name,
                            "type": entity["type"],
                            "properties": {
                                "source": "dynamic_generation",
                                "confidence": 0.8,
                                "related_to": core_entity["name"],
                                "alias": name if full_name != name else None
                            }
                        })
                
                # 如果仍然没有足够的实体，从文本中提取关键词作为实体
                if len(result_entities) < 5:
                    logger.info(f"仍然没有足够的实体，从文本中提取关键词作为实体")
                    # 简单的关键词提取
                    keywords = full_text.split()
                    # 过滤掉一些常见的停用词
                    stop_words = ["的", "是", "在", "和", "了", "就", "都", "而", "及", "与", "或", "一个", "这个", "那个", "这些", "那些"]
                    filtered_keywords = [word for word in keywords if word not in stop_words and len(word) > 2]
                    # 去重
                    unique_keywords = list(set(filtered_keywords))
                    # 添加关键词作为实体
                    for keyword in unique_keywords[:10]:
                        if keyword not in seen_entities:
                            seen_entities.add(keyword)
                            result_entities.append({
                                "name": keyword,
                                "type": "概念",
                                "properties": {
                                    "source": "keyword_extraction",
                                    "confidence": 0.6
                                }
                            })
            
            logger.info(f"最终提取的实体: {result_entities}")
            
            return result_entities
        except Exception as e:
            logger.error(f"使用大模型提取实体失败: {str(e)}")
            # 失败时回退到默认的实体提取逻辑
            return await self._default_extract_entities(query, context)
    
    async def _default_extract_entities(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """默认的实体提取逻辑，当大模型提取失败时使用"""
        # 从上下文的图谱数据中提取实体
        entities = context.get("graph_data", {}).get("entities", [])
        
        # 转换实体格式，确保前端需要的字段存在
        result_entities = []
        seen_entities = set()  # 用于去重
        
        for entity in entities[:10]:  # 限制返回数量为10个
            name = entity.name if hasattr(entity, 'name') else entity.get('name', '')
            entity_type = entity.type if hasattr(entity, 'type') else entity.get('type', '未知')
            
            # 跳过无效实体
            if not name or name in seen_entities:
                continue
            
            # 添加到已见集合
            seen_entities.add(name)
            
            result_entities.append({
                "name": name,
                "type": entity_type,
                "properties": {
                    "source": "knowledge_graph",
                    "confidence": 0.85  # 添加置信度属性
                }
            })
        
        return result_entities
    
    async def _extract_related_relationships(self, query: str, context: Dict[str, Any], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用大模型提取相关关系"""
        try:
            # 使用延迟导入避免循环依赖
            from src.services.service_factory import service_factory
            
            # 从文档内容中获取文本
            documents = context.get("documents", [])
            doc_texts = [doc.get("content", "") for doc in documents]
            full_text = "\n".join(doc_texts)
            
            # 获取实体名称列表
            entity_names = [entity["name"] for entity in entities if entity["name"]]
            
            # 如果没有实体，返回空列表
            if not entity_names:
                return []
            
            # 构建提示词，使用大模型提取关系
            prompt = f"""请从以下文本中提取实体之间的关系，实体包括：{', '.join(entity_names)}。
            请确保提取的关系类型多样且准确，例如：创始人、开发、拥有、投资、合作、竞争、领导、创立、发布、基于等。
            请按照以下JSON格式返回，确保关系类型准确，来源和目标实体名称正确：
            [
                {{"from": "来源实体名称", "to": "目标实体名称", "type": "关系类型"}}
            ]
            
            文本内容：
            {full_text}
            
            查询内容：
            {query}
            """
            
            # 调用大模型提取关系
            llm_response = await service_factory.llm_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个关系提取专家，能够从文本中准确提取实体之间的关系。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            # 解析大模型返回的结果
            relationships_json = llm_response.get("content", "[]")
            relationships = json.loads(relationships_json)
            
            # 转换关系格式，确保前端需要的字段存在
            result_relationships = []
            seen_relationships = set()  # 用于去重
            
            for relationship in relationships[:15]:  # 限制返回数量为15个
                from_entity = relationship.get("from", "")
                to_entity = relationship.get("to", "")
                relation_type = relationship.get("type", "相关")
                
                # 跳过无效关系
                if not from_entity or not to_entity or from_entity == to_entity:
                    continue
                
                # 检查实体是否在实体列表中
                if from_entity not in entity_names or to_entity not in entity_names:
                    continue
                
                # 生成唯一键用于去重
                key = f"{from_entity}-{to_entity}-{relation_type}"
                if key in seen_relationships:
                    continue
                
                # 添加到已见集合
                seen_relationships.add(key)
                
                result_relationships.append({
                    "from": from_entity,
                    "to": to_entity,
                    "type": relation_type,
                    "properties": {
                        "source": "llm_extraction",
                        "confidence": 0.95  # 大模型提取的关系置信度较高
                    }
                })
            
            # 获取核心实体
            core_entity = entities[0] if entities else None
            core_entity_name = core_entity["name"] if core_entity else ""
            
            # 关系类型映射，基于实体类型组合
            relation_type_map = {
                "公司-人物": ["创始人", "CEO", "高管", "员工", "创始人兼CEO", "联合创始人", "董事长"],
                "公司-产品": ["开发", "拥有", "发布", "销售", "运营", "维护", "升级", "推广"],
                "公司-公司": ["合作", "竞争", "投资", "子公司", "母公司", "控股", "收购", "合并", "战略联盟"],
                "公司-技术": ["研发", "应用", "拥有", "专利", "创新", "采用", "授权"],
                "公司-业务": ["开展", "运营", "核心业务", "拓展", "转型", "外包"],
                "公司-机构": ["合作", "投资", "设立", "资助"],
                "公司-事件": ["举办", "参与", "赞助", "主导"],
                "人物-公司": ["创立", "领导", "投资", "任职", "离职", "顾问", "董事"],
                "人物-产品": ["设计", "发明", "使用", "推广", "代言"],
                "人物-人物": ["合作", "竞争", "师徒", "同事", "朋友", "家人", "导师", "学生"],
                "人物-技术": ["发明", "改进", "研究", "应用"],
                "人物-事件": ["参与", "主持", "演讲", "发起"],
                "产品-公司": ["属于", "由...开发", "归...所有"],
                "产品-产品": ["集成", "兼容", "替代", "互补"],
                "产品-功能": ["具有", "包含", "提供", "支持"],
                "产品-技术": ["基于", "使用", "采用", "实现"],
                "产品-用户": ["面向", "服务", "吸引", "满足"],
                "产品-事件": ["发布", "更新", "下架", "获奖"],
                "技术-产品": ["应用于", "支撑", "驱动", "赋能"],
                "技术-技术": ["依赖", "衍生", "融合", "替代"],
                "技术-公司": ["由...研发", "被...使用", "授权给...", "服务于..."],
                "技术-概念": ["基于", "实现", "体现", "支撑"],
                "技术-事件": ["发布", "突破", "应用", "展示"],
                "概念-公司": ["被...应用", "指导...发展", "影响...战略", "改变...模式"],
                "概念-产品": ["体现", "实现", "承载", "应用于"],
                "概念-技术": ["推动", "包含", "指导", "启发"],
                "概念-概念": ["相关", "衍生", "对立", "互补"],
                "机构-公司": ["合作", "投资", "监管", "服务"],
                "机构-人物": ["雇佣", "合作", "研究", "指导"],
                "机构-技术": ["研发", "推广", "标准", "认证"],
                "事件-公司": ["影响", "改变", "促进", "损害"],
                "事件-人物": ["影响", "改变", "成就", "挑战"],
                "事件-产品": ["发布", "展示", "测试", "评估"]
            }
            
            # 生成更多关系，确保核心实体与其他实体有足够的关系
            if len(result_relationships) < 5 and entities:
                logger.info(f"关系数量不足，生成更多关系")
                
                # 首先确保核心实体与其他实体有足够的关系
                if core_entity:
                    for i, other_entity in enumerate(entities[1:]):
                        # 生成从核心实体到其他实体的关系
                        entity_pair = f"{core_entity['type']}-{other_entity['type']}"
                        reverse_pair = f"{other_entity['type']}-{core_entity['type']}"
                        
                        # 获取可能的关系类型
                        possible_relations = relation_type_map.get(entity_pair, [])
                        if not possible_relations:
                            possible_relations = relation_type_map.get(reverse_pair, ["相关"])
                            
                            # 如果是反向关系，交换源和目标
                            if possible_relations and possible_relations != ["相关"]:
                                from_ent, to_ent = other_entity["name"], core_entity_name
                            else:
                                from_ent, to_ent = core_entity_name, other_entity["name"]
                        else:
                            from_ent, to_ent = core_entity_name, other_entity["name"]
                        
                        # 生成关系
                        for relation_type in possible_relations:
                            # 生成唯一键用于去重
                            key = f"{from_ent}-{to_ent}-{relation_type}"
                            if key in seen_relationships:
                                continue
                            
                            # 添加到已见集合
                            seen_relationships.add(key)
                            
                            result_relationships.append({
                                "from": from_ent,
                                "to": to_ent,
                                "type": relation_type,
                                "properties": {
                                    "source": "core_relation",
                                    "confidence": 0.9,
                                    "entity_types": f"{core_entity['type']}-{other_entity['type']}",
                                    "is_core_relation": True
                                }
                            })
                            
                            # 如果已经生成了5个核心关系，停止生成
                            if len(result_relationships) >= 10:
                                break
                        
                        if len(result_relationships) >= 10:
                            break
                
                # 如果仍然需要更多关系，生成其他实体间的关系
                if len(result_relationships) < 10:
                    for i, entity1 in enumerate(entities):
                        for j, entity2 in enumerate(entities):
                            if i != j:  # 允许单向关系，不限制i < j
                                # 生成实体对类型
                                entity_pair = f"{entity1['type']}-{entity2['type']}"
                                
                                # 获取可能的关系类型
                                possible_relations = relation_type_map.get(entity_pair, ["相关"])
                                
                                for relation_type in possible_relations:
                                    # 生成唯一键用于去重
                                    key = f"{entity1['name']}-{entity2['name']}-{relation_type}"
                                    if key in seen_relationships:
                                        continue
                                    
                                    # 添加到已见集合
                                    seen_relationships.add(key)
                                    
                                    result_relationships.append({
                                        "from": entity1["name"],
                                        "to": entity2["name"],
                                        "type": relation_type,
                                        "properties": {
                                            "source": "entity_relation",
                                            "confidence": 0.8,
                                            "entity_types": entity_pair
                                        }
                                    })
                                    
                                    # 如果已经生成了15个关系，停止生成
                                    if len(result_relationships) >= 15:
                                        break
                                
                                if len(result_relationships) >= 15:
                                    break
                        if len(result_relationships) >= 15:
                            break
            
            return result_relationships
            
        except Exception as e:
            logger.error(f"提取相关关系失败: {str(e)}")
            # 返回空列表，避免影响整体查询结果
            return []
    
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


