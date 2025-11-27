import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CrossModalService:
    """
    跨模态数据关联服务
    实现不同模态数据（文本、图像、表格等）之间的关联关系
    """
    
    def __init__(self, llm_service=None):
        self.logger = logger.getChild("CrossModalService")
        self.llm_service = llm_service
        self.initialized = False
    
    async def initialize(self):
        """
        初始化跨模态数据关联服务
        """
        try:
            self.logger.info("跨模态数据关联服务初始化")
            self.initialized = True
            return self
        except Exception as e:
            self.logger.error(f"跨模态数据关联服务初始化失败: {str(e)}")
            self.initialized = False
            raise
    
    async def shutdown(self):
        """
        关闭跨模态数据关联服务
        """
        try:
            self.logger.info("跨模态数据关联服务已关闭")
        except Exception as e:
            self.logger.warning(f"跨模态数据关联服务关闭发生错误: {str(e)}")
    
    async def associate_text_image(self, text_content: str, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建立文本和图像之间的关联
        
        Args:
            text_content: 文本内容
            image_data: 图像数据，包含图像描述、OCR结果等
            
        Returns:
            关联结果，包含关联关系、相似度等信息
        """
        try:
            self.logger.info("建立文本和图像之间的关联")
            
            # 简单实现：基于文本和图像描述的关键词匹配
            # 提取文本关键词
            text_keywords = await self._extract_keywords(text_content)
            
            # 提取图像关键词
            image_keywords = []
            
            # 从图像描述中提取关键词
            if image_data.get("description"):
                image_desc_keywords = await self._extract_keywords(image_data["description"])
                image_keywords.extend(image_desc_keywords)
            
            # 从OCR结果中提取关键词
            if image_data.get("ocr_result"):
                ocr_keywords = await self._extract_keywords(image_data["ocr_result"])
                image_keywords.extend(ocr_keywords)
            
            # 计算关键词相似度
            common_keywords = list(set(text_keywords) & set(image_keywords))
            similarity = len(common_keywords) / max(len(text_keywords), len(image_keywords), 1)
            
            # 构建关联结果
            association = {
                "type": "text_image_association",
                "text_content": text_content[:100] + "..." if len(text_content) > 100 else text_content,
                "image_info": {
                    "image_id": image_data.get("image_id", "unknown"),
                    "image_desc": image_data.get("description", ""),
                    "ocr_result": image_data.get("ocr_result", "")[:100] + "..." if image_data.get("ocr_result") and len(image_data.get("ocr_result")) > 100 else image_data.get("ocr_result", "")
                },
                "common_keywords": common_keywords,
                "similarity": round(similarity, 2),
                "confidence": round(min(similarity + 0.1, 1.0), 2),
                "created_at": datetime.now().isoformat()
            }
            
            return association
            
        except Exception as e:
            self.logger.error(f"建立文本和图像关联失败: {str(e)}", exc_info=True)
            return {
                "type": "text_image_association",
                "error": str(e),
                "similarity": 0.0,
                "confidence": 0.0
            }
    
    async def associate_text_table(self, text_content: str, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建立文本和表格之间的关联
        
        Args:
            text_content: 文本内容
            table_data: 表格数据，包含表格内容、列名等
            
        Returns:
            关联结果，包含关联关系、相似度等信息
        """
        try:
            self.logger.info("建立文本和表格之间的关联")
            
            # 提取文本关键词
            text_keywords = await self._extract_keywords(text_content)
            
            # 提取表格关键词
            table_keywords = []
            
            # 从表格列名中提取关键词
            columns = table_data.get("columns", [])
            for col in columns:
                col_keywords = await self._extract_keywords(col)
                table_keywords.extend(col_keywords)
            
            # 从表格数据中提取关键词
            data = table_data.get("data", [])
            for row in data[:10]:  # 只处理前10行数据
                for key, value in row.items():
                    if isinstance(value, str):
                        value_keywords = await self._extract_keywords(value)
                        table_keywords.extend(value_keywords)
            
            # 计算关键词相似度
            common_keywords = list(set(text_keywords) & set(table_keywords))
            similarity = len(common_keywords) / max(len(text_keywords), len(table_keywords), 1)
            
            # 构建关联结果
            association = {
                "type": "text_table_association",
                "text_content": text_content[:100] + "..." if len(text_content) > 100 else text_content,
                "table_info": {
                    "table_id": table_data.get("table_id", "unknown"),
                    "table_columns": columns,
                    "table_rows": len(data),
                    "table_sample": data[:2] if len(data) > 2 else data
                },
                "common_keywords": common_keywords,
                "similarity": round(similarity, 2),
                "confidence": round(min(similarity + 0.1, 1.0), 2),
                "created_at": datetime.now().isoformat()
            }
            
            return association
            
        except Exception as e:
            self.logger.error(f"建立文本和表格关联失败: {str(e)}", exc_info=True)
            return {
                "type": "text_table_association",
                "error": str(e),
                "similarity": 0.0,
                "confidence": 0.0
            }
    
    async def associate_image_table(self, image_data: Dict[str, Any], table_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建立图像和表格之间的关联
        
        Args:
            image_data: 图像数据，包含图像描述、OCR结果等
            table_data: 表格数据，包含表格内容、列名等
            
        Returns:
            关联结果，包含关联关系、相似度等信息
        """
        try:
            self.logger.info("建立图像和表格之间的关联")
            
            # 提取图像关键词
            image_keywords = []
            
            # 从图像描述中提取关键词
            if image_data.get("description"):
                image_desc_keywords = await self._extract_keywords(image_data["description"])
                image_keywords.extend(image_desc_keywords)
            
            # 从OCR结果中提取关键词
            if image_data.get("ocr_result"):
                ocr_keywords = await self._extract_keywords(image_data["ocr_result"])
                image_keywords.extend(ocr_keywords)
            
            # 提取表格关键词
            table_keywords = []
            
            # 从表格列名中提取关键词
            columns = table_data.get("columns", [])
            for col in columns:
                col_keywords = await self._extract_keywords(col)
                table_keywords.extend(col_keywords)
            
            # 从表格数据中提取关键词
            data = table_data.get("data", [])
            for row in data[:10]:  # 只处理前10行数据
                for key, value in row.items():
                    if isinstance(value, str):
                        value_keywords = await self._extract_keywords(value)
                        table_keywords.extend(value_keywords)
            
            # 计算关键词相似度
            common_keywords = list(set(image_keywords) & set(table_keywords))
            similarity = len(common_keywords) / max(len(image_keywords), len(table_keywords), 1)
            
            # 构建关联结果
            association = {
                "type": "image_table_association",
                "image_info": {
                    "image_id": image_data.get("image_id", "unknown"),
                    "image_desc": image_data.get("description", ""),
                    "ocr_result": image_data.get("ocr_result", "")[:100] + "..." if image_data.get("ocr_result") and len(image_data.get("ocr_result")) > 100 else image_data.get("ocr_result", "")
                },
                "table_info": {
                    "table_id": table_data.get("table_id", "unknown"),
                    "table_columns": columns,
                    "table_rows": len(data),
                    "table_sample": data[:2] if len(data) > 2 else data
                },
                "common_keywords": common_keywords,
                "similarity": round(similarity, 2),
                "confidence": round(min(similarity + 0.1, 1.0), 2),
                "created_at": datetime.now().isoformat()
            }
            
            return association
            
        except Exception as e:
            self.logger.error(f"建立图像和表格关联失败: {str(e)}", exc_info=True)
            return {
                "type": "image_table_association",
                "error": str(e),
                "similarity": 0.0,
                "confidence": 0.0
            }
    
    async def associate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        建立多个文档之间的跨模态关联
        
        Args:
            documents: 文档列表，每个文档包含不同模态的数据
            
        Returns:
            关联结果列表
        """
        try:
            self.logger.info(f"建立 {len(documents)} 个文档之间的跨模态关联")
            
            associations = []
            
            # 简单实现：两两比较文档，建立关联
            for i in range(len(documents)):
                for j in range(i + 1, len(documents)):
                    doc1 = documents[i]
                    doc2 = documents[j]
                    
                    # 根据文档模态类型建立关联
                    if doc1.get("modal_type") == "text" and doc2.get("modal_type") == "image":
                        # 文本和图像关联
                        association = await self.associate_text_image(
                            doc1.get("content", ""),
                            doc2.get("image_data", {})
                        )
                        associations.append(association)
                    elif doc1.get("modal_type") == "text" and doc2.get("modal_type") == "table":
                        # 文本和表格关联
                        association = await self.associate_text_table(
                            doc1.get("content", ""),
                            doc2.get("table_data", {})
                        )
                        associations.append(association)
                    elif doc1.get("modal_type") == "image" and doc2.get("modal_type") == "table":
                        # 图像和表格关联
                        association = await self.associate_image_table(
                            doc1.get("image_data", {}),
                            doc2.get("table_data", {})
                        )
                        associations.append(association)
                    elif doc1.get("modal_type") == "image" and doc2.get("modal_type") == "text":
                        # 图像和文本关联（与文本和图像关联相同，只是顺序不同）
                        association = await self.associate_text_image(
                            doc2.get("content", ""),
                            doc1.get("image_data", {})
                        )
                        associations.append(association)
                    elif doc1.get("modal_type") == "table" and doc2.get("modal_type") == "text":
                        # 表格和文本关联（与文本和表格关联相同，只是顺序不同）
                        association = await self.associate_text_table(
                            doc2.get("content", ""),
                            doc1.get("table_data", {})
                        )
                        associations.append(association)
                    elif doc1.get("modal_type") == "table" and doc2.get("modal_type") == "image":
                        # 表格和图像关联（与图像和表格关联相同，只是顺序不同）
                        association = await self.associate_image_table(
                            doc2.get("image_data", {}),
                            doc1.get("table_data", {})
                        )
                        associations.append(association)
            
            # 按相似度排序
            associations.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            
            return associations
            
        except Exception as e:
            self.logger.error(f"建立文档间跨模态关联失败: {str(e)}", exc_info=True)
            return []
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 文本内容
            
        Returns:
            关键词列表
        """
        try:
            if not text:
                return []
            
            # 使用LLM服务提取关键词，提高准确性
            if self.llm_service:
                try:
                    system_prompt = "你是一个专业的关键词提取助手，请从给定文本中提取最相关的关键词，只返回关键词列表，不要添加任何解释或说明。"
                    user_prompt = f"请从以下文本中提取关键词，只返回关键词列表，格式为['关键词1', '关键词2', ...]：\n{text[:1000]}"
                    
                    result = await self.llm_service.generate_text(
                        user_prompt,
                        system_prompt,
                        max_tokens=512,
                        temperature=0.1
                    )
                    
                    # 解析LLM返回的结果
                    import ast
                    keywords = ast.literal_eval(result)
                    return [keyword.strip() for keyword in keywords if keyword.strip()]
                except Exception as e:
                    self.logger.warning(f"使用LLM提取关键词失败，回退到基于规则的方法: {str(e)}")
            
            # 简单的回退实现：返回文本中的前几个词语
            import re
            # 分割文本为词语
            words = re.findall(r'\w+', text)
            # 返回前20个关键词，去重
            return list(set(words))[:20]
        except Exception as e:
            self.logger.error(f"关键词提取失败: {str(e)}")
            return []
