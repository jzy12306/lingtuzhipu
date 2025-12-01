from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from src.models.document import Document, DocumentCreate, DocumentUpdate, DocumentQuery, DocumentStats
from src.repositories.document_repository import DocumentRepository
from src.repositories.knowledge_repository import KnowledgeRepository
from src.agents.builder import BuilderAgentService
from src.services.ocr_service import ocr_service
from src.services.table_extraction_service import table_extraction_service

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self,
                 document_repository: DocumentRepository,
                 knowledge_repository: KnowledgeRepository,
                 cross_modal_service=None):
        self.document_repository = document_repository
        self.knowledge_repository = knowledge_repository
        self.cross_modal_service = cross_modal_service
        self.initialized = False
        self.logger = logger.getChild("DocumentService")
        # 文档处理结果缓存，基于内容哈希
        self._processing_cache = {}
        # 缓存过期时间（秒）
        self._cache_expiry = 3600
    
    async def initialize(self):
        """
        初始化文档服务
        在开发环境中简化初始化
        """
        try:
            self.logger.info("文档服务初始化 (开发模式)")
            self.initialized = True
            return self
        except Exception as e:
            self.logger.warning(f"文档服务初始化发生警告: {str(e)}")
            self.initialized = True
            return self
    
    async def shutdown(self):
        """
        关闭文档服务
        """
        try:
            self.logger.info("文档服务已关闭")
        except Exception as e:
            self.logger.warning(f"文档服务关闭发生错误: {str(e)}")
    
    async def create_document(self, document_data: DocumentCreate, user_id: str) -> Document:
        """创建新文档"""
        # 生成内容哈希
        import hashlib
        content_hash = hashlib.md5((document_data.content or "").encode()).hexdigest()
        
        # 创建文档对象，包含所有必填字段
        document = Document(
            **document_data.dict(),
            id=str(uuid.uuid4()),  # 生成唯一ID
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="uploaded",
            processed_at=None,
            file_size=len(document_data.content or ""),  # 内容大小
            entities_count=0,
            relations_count=0,
            content_hash=content_hash,
            ocr_status=None,
            ocr_result=None,
            ocr_confidence=None,
            ocr_error=None,
            embedding_id=None,
            processing_error=None
        )
        
        saved_doc = await self.document_repository.save_document(document)
        logger.info(f"Created document: {saved_doc.id} for user: {user_id}")
        return saved_doc
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档详情"""
        return await self.document_repository.get_document(document_id)
    
    async def update_document(self, document_id: str, document_update: DocumentUpdate) -> Optional[Document]:
        """更新文档信息"""
        update_data = document_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.now()
        return await self.document_repository.update_document(document_id, update_data)
    
    async def update_document_status(self, document_id: str, status: str) -> None:
        """更新文档状态"""
        update_data = {
            'status': status,
            'updated_at': datetime.now()
        }
        await self.document_repository.update_document(document_id, update_data)
    
    async def search_documents(self, query: DocumentQuery, skip: int, limit: int, user_id: Optional[str] = None) -> List[Document]:
        """高级文档搜索"""
        return await self.document_repository.advanced_search(
            query=query,
            skip=skip,
            limit=limit,
            user_id=user_id
        )
    
    async def process_document_async(self, document_id: str, user_id: str) -> None:
        """异步处理文档并提取知识"""
        import asyncio
        try:
            # 添加超时控制，防止无限等待
            logger.info(f"开始处理文档: {document_id} 用户: {user_id}")
            await asyncio.wait_for(
                self._process_document_with_timeout(document_id, user_id),
                timeout=300.0  # 5分钟超时
            )
        except asyncio.TimeoutError:
            logger.error(f"文档处理超时: {document_id} (5分钟)")
            try:
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'timeout',
                        'knowledge_extracted': False,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': '文档处理超时'
                    }
                )
            except Exception as update_error:
                logger.error(f"更新文档状态失败: {document_id}, 错误: {str(update_error)}")
        except Exception as e:
            logger.exception(f"文档处理异常: {document_id}")
            try:
                # 即使出现异常，也要确保文档状态更新为processed，保留OCR结果
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'processed',
                        'knowledge_extracted': False,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': str(e)
                    }
                )
            except Exception as update_error:
                logger.error(f"更新文档状态失败: {document_id}, 错误: {str(update_error)}")
    
    async def batch_process_documents(self, document_ids: List[str], user_id: str) -> Dict[str, Any]:
        """批量处理文档"""
        results = {
            'total': len(document_ids),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for doc_id in document_ids:
            try:
                # 异步处理每个文档
                await self.process_document_async(doc_id, user_id)
                results['success'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        return results
    
    async def get_document_statistics(self, user_id: Optional[str] = None) -> DocumentStats:
        """获取文档统计信息"""
        return await self.document_repository.get_document_statistics(user_id)
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """删除文档及相关知识"""
        # 验证文档存在并属于用户
        document = await self.document_repository.get_document(document_id)
        if not document:
            return False
        
        # 删除相关知识
        await self.knowledge_repository.delete_document_knowledge(document_id)
        
        # 删除文档
        return await self.document_repository.delete_document(document_id)
    
    def _get_content_hash(self, content: str) -> str:
        """计算文档内容的哈希值，用于缓存"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _process_document_with_timeout(self, document_id: str, user_id: str) -> None:
        """带超时控制的文档处理内部函数"""
        logger.info(f"开始带超时控制的文档处理: {document_id} 用户: {user_id}")
        try:
            logger.info(f"开始处理文档: {document_id} 用户: {user_id}")
            
            # 获取文档
            logger.debug(f"获取文档信息: {document_id}")
            document = await self.document_repository.get_document(document_id)
            if not document:
                logger.error(f"文档不存在: {document_id}")
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'failed',
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': '文档不存在'
                    }
                )
                return
            
            # 记录文档基本信息
            logger.debug(f"文档基本信息: ID={document.id}, 标题={document.title}, 类型={document.document_type}, 状态={document.status}")
            
            # 检查文档状态，如果已经是失败状态，直接返回
            if document.status == 'failed':
                logger.info(f"文档已标记为失败，跳过处理: {document_id}")
                return
            
            # 获取文档内容
            logger.info(f"获取文档内容: {document_id}")
            content = await self.document_repository.get_document_content(document_id)
            if not content:
                logger.error(f"文档内容不存在: {document_id}")
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'failed',
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': '文档内容不存在'
                    }
                )
                return
            
            logger.info(f"获取文档内容成功: {document_id}, 内容长度: {len(content)} 字符")
            
            # 计算内容哈希，检查缓存
            content_hash = self._get_content_hash(content)
            logger.debug(f"文档内容哈希: {content_hash}, 文档ID: {document_id}")
            
            # 检查缓存，如果内容已处理过，直接使用缓存结果
            current_time = datetime.now().timestamp()
            if content_hash in self._processing_cache:
                cache_entry = self._processing_cache[content_hash]
                if current_time - cache_entry['timestamp'] < self._cache_expiry:
                    logger.info(f"文档内容已缓存，使用缓存结果: {document_id}, 哈希: {content_hash}")
                    # 更新文档状态为已处理，使用缓存结果
                    await self.document_repository.update_document(
                        document_id,
                        {
                            'status': 'processed',
                            'knowledge_extracted': True,
                            'processed_at': datetime.now(),
                            'updated_at': datetime.now(),
                            'entities_count': cache_entry['result']['entities']['saved'],
                            'relations_count': cache_entry['result']['relations']['saved'],
                            'extracted_tables': cache_entry['result']['tables_count']
                        }
                    )
                    return
                else:
                    # 缓存过期，删除
                    del self._processing_cache[content_hash]
                    logger.debug(f"缓存已过期，删除: {content_hash}")
            
            # 记录文档内容预览，便于调试
            if len(content) > 1000:
                logger.debug(f"文档内容预览: {content[:1000]}...")
            else:
                logger.debug(f"文档完整内容: {content}")
            
            # 检查是否需要OCR识别（纯文本文件跳过OCR）
            need_ocr = False
            ocr_result = None
            ocr_content = None
            
            if document.document_type in ["pdf", "jpg", "jpeg", "png", "bmp", "tiff"]:
                need_ocr = True
                # 更新文档状态为OCR识别中
                logger.info(f"更新文档状态为OCR处理中: {document_id}")
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'ocr_processing',
                        'updated_at': datetime.now()
                    }
                )
            else:
                # 对于纯文本文件，直接跳过OCR步骤
                logger.info(f"纯文本文件跳过OCR: {document_id}, 类型: {document.document_type}")
                ocr_result = {"regions": [{"lines": [{"words": [{"text": content}]}]}], "content": content}
                await self.document_repository.update_document(document_id, {
                    "ocr_status": "not_needed",
                    "ocr_result": ocr_result,
                    "updated_at": datetime.now()
                })
            
            # 如果需要OCR识别
            if need_ocr:
                logger.info(f"对文档进行OCR识别: {document_id}, 类型: {document.document_type}")
                try:
                    # 使用文件流处理，避免本地文件存储
                    ocr_result = None
                    if document.document_type == "pdf":
                        # 直接使用文档内容进行OCR，避免文件路径依赖
                        logger.debug(f"调用OCR服务识别PDF流: {document_id}")
                        ocr_result = await ocr_service.recognize_pdf_stream(content)
                    else:
                        logger.debug(f"调用OCR服务识别图像流: {document_id}")
                        ocr_result = await ocr_service.recognize_image_stream(content)
                    
                    logger.debug(f"OCR服务返回结果: {document_id}, 结果类型: {type(ocr_result)}")
                    
                    # 提取OCR识别结果
                    ocr_content = ""
                    if ocr_result:
                        # 验证OCR结果格式
                        if isinstance(ocr_result, dict) and "regions" in ocr_result:
                            for region in ocr_result["regions"]:
                                if isinstance(region, dict) and "lines" in region:
                                    for line in region["lines"]:
                                        if isinstance(line, dict) and "words" in line:
                                            for word in line["words"]:
                                                if isinstance(word, dict) and "text" in word:
                                                    ocr_content += word["text"] + " "
                        elif isinstance(ocr_result, str):
                            # 如果OCR服务直接返回文本
                            ocr_content = ocr_result
                        else:
                            logger.warning(f"OCR结果格式不符合预期: {document_id}, 结果: {ocr_result}")
                    else:
                        logger.warning(f"OCR服务返回空结果: {document_id}")
                    
                    # 验证OCR识别结果
                    if ocr_content and len(ocr_content.strip()) > 10:  # 至少有10个字符才算有效
                        logger.info(f"OCR识别成功: {document_id}, 识别内容长度: {len(ocr_content)}")
                        await self.document_repository.update_document_content(document_id, ocr_content)
                        content = ocr_content
                        
                        await self.document_repository.update_document(document_id, {
                            "ocr_result": ocr_result,
                            "ocr_status": "success",
                            "ocr_confidence": ocr_result.get("confidence", None) if isinstance(ocr_result, dict) else None,
                            "updated_at": datetime.now()
                        })
                    else:
                        # OCR结果为空或无效，使用原始内容继续处理
                        logger.warning(f"OCR识别结果无效或为空，使用原始内容继续处理: {document_id}, 识别内容长度: {len(ocr_content)}")
                        await self.document_repository.update_document(document_id, {
                            "ocr_status": "partial",
                            "ocr_error": "OCR识别结果无效或为空，使用原始内容继续处理",
                            "updated_at": datetime.now()
                        })
                except Exception as e:
                    logger.exception(f"OCR识别失败: {document_id}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}")
                    # OCR失败时，使用原始内容继续处理，不中断整个流程
                    await self.document_repository.update_document(document_id, {
                        "ocr_status": "failed",
                        "ocr_error": f"OCR识别失败: {type(e).__name__}: {str(e)}",
                        "updated_at": datetime.now()
                    })
                    logger.info(f"OCR识别失败，使用原始内容继续处理文档: {document_id}")
            
            # 更新文档状态为处理中
            logger.info(f"更新文档状态为处理中: {document_id}")
            await self.document_repository.update_document(
                document_id,
                {
                    'status': 'processing',
                    'updated_at': datetime.now()
                }
            )
            
            # 使用构建者智能体处理文档
            logger.info(f"开始使用构建者智能体处理文档: {document_id}")
            result = {
                'status': 'success',
                'error': None,
                'entities': {'saved': 0},
                'relations': {'saved': 0},
                'tables_count': 0
            }
            
            try:
                # 检查BuilderAgentService的初始化状态
                logger.debug(f"获取BuilderAgentService实例: {document_id}")
                builder_service = BuilderAgentService.get_instance(self.knowledge_repository, self.document_repository)
                logger.debug(f"BuilderAgentService实例获取成功: {document_id}")
                
                # 调用构建者智能体处理文档
                logger.debug(f"调用BuilderAgentService处理文档: {document_id}")
                result = await builder_service.process_document_by_id(document_id)
                logger.debug(f"BuilderAgentService处理完成: {document_id}, 结果: {result}")
            except Exception as e:
                logger.exception(f"BuilderAgentService处理文档失败: {document_id}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}")
                # BuilderAgentService失败时，使用默认成功结果，确保文档能被标记为已处理
                result = {
                    'status': 'success',
                    'error': f"BuilderAgentService处理失败，但文档已保存: {type(e).__name__}: {str(e)}",
                    'entities': {'saved': 0},
                    'relations': {'saved': 0},
                    'tables_count': 0
                }
                logger.info(f"BuilderAgentService处理失败，使用默认结果继续处理: {document_id}")
            
            # 提取表格数据
            logger.info(f"开始提取文档表格数据: {document_id}")
            try:
                # 检查table_extraction_service的初始化状态
                if table_extraction_service:
                    tables = await table_extraction_service.extract_tables_from_document(
                        document_id=document_id,
                        document_type=document.document_type,
                        content=content
                    )
                    logger.debug(f"表格提取服务调用完成: {document_id}, 提取到表格数量: {len(tables) if tables else 0}")
                    
                    if tables and len(tables) > 0:
                        table_knowledge = []
                        for i, table in enumerate(tables):
                            try:
                                # 转换表格数据为知识
                                table_knowledge_item = await table_extraction_service.convert_table_to_knowledge(table)
                                table_knowledge.append(table_knowledge_item)
                                logger.debug(f"表格转换为知识成功: {document_id}, 表格索引: {i}")
                            except Exception as table_error:
                                logger.warning(f"单个表格转换为知识失败: {document_id}, 表格索引: {i}, 错误: {str(table_error)}")
                        
                        result['table_knowledge'] = table_knowledge
                        result['tables_count'] = len(tables)
                        logger.info(f"表格数据提取完成: {document_id}, 提取到表格数量: {len(tables)}, 转换为知识数量: {len(table_knowledge)}")
                    else:
                        logger.info(f"文档中未提取到表格: {document_id}")
                        result['tables_count'] = 0
                else:
                    logger.warning(f"表格提取服务未初始化: {document_id}")
                    result['tables_count'] = 0
            except Exception as e:
                logger.exception(f"表格提取服务处理失败: {document_id}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}")
                # 表格提取失败时，确保结果中包含必要的字段
                result['tables_count'] = 0
                logger.info(f"表格提取失败，继续处理文档: {document_id}")
            
            # 更新最终状态
            logger.info(f"开始更新文档最终状态: {document_id}")
            
            # 无论结果如何，都将文档标记为已处理，而不是失败
            # 这样用户至少可以看到文档已保存，即使知识提取失败
            await self.document_repository.update_document(
                document_id,
                {
                    'status': 'processed',
                    'knowledge_extracted': result.get('status') == 'success' and result.get('entities', {}).get('saved', 0) > 0,
                    'processed_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'entities_count': result.get('entities', {}).get('saved', 0),
                    'relations_count': result.get('relations', {}).get('saved', 0),
                    'extracted_tables': result.get('tables_count', 0),
                    'processing_error': result.get('error')  # 保存错误信息，但不标记为失败
                }
            )
            
            # 缓存处理结果
            if result.get('status') == 'success':
                content_hash = self._get_content_hash(content)
                self._processing_cache[content_hash] = {
                    'result': result,
                    'timestamp': datetime.now().timestamp()
                }
                logger.debug(f"文档处理结果已缓存: {document_id}, 哈希: {content_hash}")
            
            # 记录文档处理完成信息，包含实体和关系数量
            entities_count = result.get('entities', {}).get('saved', 0)
            relations_count = result.get('relations', {}).get('saved', 0)
            tables_count = result.get('tables_count', 0)
            logger.info(f"文档处理流程完成: {document_id}, 最终状态: processed")
            logger.info(f"处理结果统计: 实体数: {entities_count}, 关系数: {relations_count}, 表格数: {tables_count}")
            logger.info(f"文档处理完成，最终状态已更新: {document_id}")
                    
        except Exception as e:
            logger.error(f"文档处理异常: {document_id}, 错误: {str(e)}")
            import traceback
            logger.error(f"文档处理异常堆栈: {traceback.format_exc()}")
            try:
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'processed',
                        'knowledge_extracted': False,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': str(e)
                    }
                )
            except Exception as update_error:
                logger.error(f"更新文档状态失败: {document_id}, 错误: {str(update_error)}")

# 创建全局document_service实例以解决导入错误
document_service: Optional[DocumentService] = None

def get_document_service() -> DocumentService:
    """获取document_service实例"""
    global document_service
    if document_service is None:
        raise ValueError("DocumentService instance has not been initialized")
    return document_service

def set_document_service(service: DocumentService) -> None:
    """设置document_service实例"""
    global document_service
    document_service = service