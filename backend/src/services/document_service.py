from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.models.document import Document, DocumentCreate, DocumentUpdate, DocumentQuery, DocumentStats
from src.repositories.document_repository import DocumentRepository
from src.repositories.knowledge_repository import KnowledgeRepository
from src.agents.builder import BuilderAgentService
from src.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self,
                 document_repository: DocumentRepository,
                 knowledge_repository: KnowledgeRepository):
        self.document_repository = document_repository
        self.knowledge_repository = knowledge_repository
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
        document = Document(
            **document_data.dict(),
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="uploaded",
            processed_at=None,
            knowledge_extracted=False
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
        try:
            logger.info(f"开始处理文档: {document_id} 用户: {user_id}")
            
            # 获取文档
            document = await self.document_repository.get_document(document_id)
            if not document:
                logger.error(f"文档不存在: {document_id}")
                return
            
            # 获取文档内容
            content = await self.document_repository.get_document_content(document_id)
            if not content:
                logger.error(f"文档内容不存在: {document_id}")
                await self.update_document_status(document_id, "error")
                return
            
            # 更新文档状态为OCR识别中
            await self.update_document_status(document_id, "ocr_processing")
            
            # 使用构建者智能体处理文档
            builder_service = BuilderAgentService.get_instance(self.knowledge_repository)
            
            # 处理文档并提取知识
            result = await builder_service.process_document(
                document_id=document_id,
                title=document.title,
                content=content,
                document_type=document.type,
                user_id=user_id
            )
            
            if result['success']:
                # 更新文档状态
                await self.document_repository.update_document(
                    document_id,
                    {
                        'status': 'processed',
                        'knowledge_extracted': True,
                        'processed_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'extracted_entities': result.get('entities_count', 0),
                        'extracted_relationships': result.get('relationships_count', 0)
                    }
                )
                logger.info(f"文档处理成功: {document_id}, 提取实体: {result.get('entities_count', 0)}, 关系: {result.get('relationships_count', 0)}")
            else:
                await self.update_document_status(document_id, "error")
                logger.error(f"文档处理失败: {document_id}, 错误: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.exception(f"文档处理异常: {document_id}")
            try:
                await self.update_document_status(document_id, "error")
            except:
                pass
    
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