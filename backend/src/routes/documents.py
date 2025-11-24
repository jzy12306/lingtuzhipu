from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from src.models.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentResponse, 
    DocumentContent, DocumentQuery, DocumentStats
)
from src.repositories.document_repository import DocumentRepository
from src.repositories.knowledge_repository import KnowledgeRepository
from src.utils.dependencies import get_current_user, validate_document_permission
from src.utils.file_processing import process_uploaded_file
from src.services.document_service import DocumentService
from src.models.user import User

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_document_repository() -> DocumentRepository:
    return DocumentRepository()


def get_knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository()


def get_document_service(
    doc_repo: DocumentRepository = Depends(get_document_repository),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
) -> DocumentService:
    return DocumentService(doc_repo, knowledge_repo)


@router.post("/", response_model=DocumentResponse)
async def create_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service)
):
    """上传并创建新文档"""
    try:
        # 处理上传的文件
        file_content, file_type = await process_uploaded_file(file)
        
        # 创建文档
        document_data = DocumentCreate(
            title=file.filename,
            description=f"上传的{file_type}文件",
            type=file_type,
            content=file_content,
            file_name=file.filename,
            file_type=file_type
        )
        
        # 保存文档
        document = await doc_service.create_document(
            document_data=document_data,
            user_id=current_user.id
        )
        
        return document
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """获取文档列表"""
    try:
        documents = await doc_repo.list_documents(
            skip=skip,
            limit=limit,
            search=search,
            document_type=document_type,
            user_id=current_user.id if not current_user.is_admin else None
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document: Document = Depends(validate_document_permission)
):
    """获取文档详情"""
    return document


@router.get("/{document_id}/content", response_model=DocumentContent)
async def get_document_content(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document: Document = Depends(validate_document_permission),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """获取文档内容"""
    content = await doc_repo.get_document_content(document_id)
    if not content:
        raise HTTPException(status_code=404, detail="文档内容不存在")
    return DocumentContent(content=content)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    document: Document = Depends(validate_document_permission),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """更新文档信息"""
    # 检查是否是文档所有者或管理员
    if document.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权更新此文档")
    
    updated_doc = await doc_repo.update_document(document_id, document_update)
    if not updated_doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return updated_doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document: Document = Depends(validate_document_permission),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """删除文档"""
    # 检查是否是文档所有者或管理员
    if document.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此文档")
    
    # 删除相关知识
    await knowledge_repo.delete_document_knowledge(document_id)
    
    # 删除文档
    success = await doc_repo.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {"message": "文档删除成功"}


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    document: Document = Depends(validate_document_permission),
    doc_service: DocumentService = Depends(get_document_service)
):
    """处理文档并提取知识（异步）"""
    # 检查是否是文档所有者或管理员
    if document.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权处理此文档")
    
    # 标记文档为处理中
    await doc_service.update_document_status(document_id, "processing")
    
    # 异步处理文档
    background_tasks.add_task(
        doc_service.process_document_async,
        document_id=document_id,
        user_id=current_user.id
    )
    
    # 返回更新后的文档状态
    updated_doc = await doc_service.get_document(document_id)
    return updated_doc


@router.get("/search/advanced", response_model=List[DocumentResponse])
async def advanced_search(
    query: DocumentQuery,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service)
):
    """高级文档搜索"""
    results = await doc_service.search_documents(
        query=query,
        skip=skip,
        limit=limit,
        user_id=current_user.id if not current_user.is_admin else None
    )
    return results


@router.get("/stats/overview", response_model=DocumentStats)
async def get_document_statistics(
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """获取文档统计信息"""
    stats = await doc_repo.get_document_statistics(
        user_id=current_user.id if not current_user.is_admin else None
    )
    return stats


@router.post("/batch/delete")
async def batch_delete_documents(
    document_ids: List[str],
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """批量删除文档"""
    if len(document_ids) > 50:
        raise HTTPException(status_code=400, detail="一次最多只能删除50个文档")
    
    deleted_count = 0
    for doc_id in document_ids:
        try:
            # 验证权限
            doc = await doc_repo.get_document(doc_id)
            if not doc:
                continue
            
            if doc.user_id != current_user.id and not current_user.is_admin:
                continue
            
            # 删除相关知识
            await knowledge_repo.delete_document_knowledge(doc_id)
            
            # 删除文档
            if await doc_repo.delete_document(doc_id):
                deleted_count += 1
        except Exception:
            continue
    
    return {"deleted_count": deleted_count}
