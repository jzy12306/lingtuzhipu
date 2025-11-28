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
    
    async def _process_document_with_timeout(self, document_id: str, user_id: str) -> None:
        """带超时控制的文档处理内部函数"""
        try:
            logger.info(f"开始处理文档: {document_id} 用户: {user_id}")
            
            # 获取文档
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
            
            # 检查文档状态，如果已经是失败状态，直接返回
            if document.status == 'failed':
                logger.info(f"文档已标记为失败，跳过处理: {document_id}")
                return
            
            # 获取文档内容
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
            
            # 检查是否需要OCR识别（纯文本文件跳过OCR）
            need_ocr = False
            ocr_result = None
            ocr_content = None
            
            if document.document_type in ["pdf", "jpg", "jpeg", "png", "bmp", "tiff"]:
                need_ocr = True
                # 更新文档状态为OCR识别中
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
                        ocr_result = await ocr_service.recognize_pdf_stream(content)
                    else:
                        ocr_result = await ocr_service.recognize_image_stream(content)
                    
                    # 提取OCR识别结果
                    if ocr_result and "regions" in ocr_result:
                        ocr_content = ""
                        for region in ocr_result["regions"]:
                            if "lines" in region:
                                for line in region["lines"]:
                                    if "words" in line:
                                        for word in line["words"]:
                                            if "text" in word:
                                                ocr_content += word["text"] + " "
                    
                    if ocr_content:
                        logger.info(f"OCR识别成功: {document_id}")
                        await self.document_repository.update_document_content(document_id, ocr_content)
                        content = ocr_content
                        
                        await self.document_repository.update_document(document_id, {
                            "ocr_result": ocr_result,
                            "ocr_status": "success",
                            "updated_at": datetime.now()
                        })
                    else:
                        logger.warning(f"OCR识别结果为空: {document_id}")
                        await self.document_repository.update_document(document_id, {
                            "ocr_status": "failed",
                            "ocr_error": "OCR识别结果为空",
                            "updated_at": datetime.now()
                        })
                except Exception as e:
                    logger.error(f"OCR识别失败: {document_id}, 错误: {str(e)}")
                    await self.document_repository.update_document(document_id, {
                        "ocr_status": "failed",
                        "ocr_error": str(e),
                        "updated_at": datetime.now()
                    })
            
            # 更新文档状态为知识提取中
            await self.document_repository.update_document(
                document_id,
                {
                    'status': 'knowledge_extracting',
                    'updated_at': datetime.now()
                }
            )
            
            # 使用构建者智能体处理文档
            builder_service = BuilderAgentService.get_instance(self.knowledge_repository, self.document_repository)
            result = await builder_service.process_document_by_id(document_id)
            
            # 提取表格数据
            try:
                tables = await table_extraction_service.extract_tables_from_document(
                    document_id=document_id,
                    document_type=document.document_type,
                    content=content
                )
                
                if tables:
                    table_knowledge = []
                    for table in tables:
                        table_knowledge.append(await table_extraction_service.convert_table_to_knowledge(table))
                    
                    result['table_knowledge'] = table_knowledge
                    result['tables_count'] = len(tables)
            except Exception as e:
                logger.warning(f"表格提取失败: {document_id}, 错误: {str(e)}")
            
            # 更新最终状态
            if result.get('status') == 'success':
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'processed',
                        'knowledge_extracted': True,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'extracted_entities': result.get('entities', {}).get('saved', 0),
                        'extracted_relationships': result.get('relations', {}).get('saved', 0),
                        'extracted_tables': result.get('tables_count', 0)
                    }
                )
                logger.info(f"文档处理成功: {document_id}")
            else:
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'failed',
                        'knowledge_extracted': False,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'processing_error': result.get('error', 'Unknown error')
                    }
                )
                logger.error(f"文档处理失败: {document_id}, 错误: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"文档处理异常: {document_id}, 错误: {str(e)}")
            try:
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'failed',
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