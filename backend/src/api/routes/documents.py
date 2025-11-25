from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import List, Optional
import io

from models.document import DocumentResponse, DocumentUpdate, DocumentCreate, DocumentType, DocumentStatus
from repositories.document_repository import document_repository
from repositories.knowledge_repository import knowledge_repository
from utils.dependencies import get_current_user
from utils.file_processing import process_uploaded_file
from agents import process_document_with_workflow

router = APIRouter()


@router.post("/", response_model=DocumentResponse)
async def create_document(
    title: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """上传并创建新文档"""
    try:
        # 验证文件类型
        allowed_types = [
            "application/pdf",
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # .xlsx
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        # 处理上传的文件
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        # 提取文本内容
        text_content = await process_uploaded_file(file_stream, file.content_type)
        
        # 创建文档数据
        document_data = DocumentCreate(
            title=title,
            document_type=document_type,
            content=text_content,
            filename=file.filename,
            file_type=file.content_type
        )
        
        # 保存文档到数据库
        document = await document_repository.create_document(
            document_data.dict(),
            user_id=current_user["id"]
        )
        
        # 异步处理文档内容，抽取知识
        # 在实际生产环境中，应该使用异步任务队列
        await process_document_with_workflow(document["id"], text_content)
        
        return DocumentResponse(
            id=document["id"],
            title=document["title"],
            document_type=document["document_type"],
            status=document["status"],
            filename=document["filename"],
            created_by=document["created_by"],
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文档失败: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    document_type: Optional[DocumentType] = Query(None, description="按文档类型筛选"),
    status: Optional[DocumentStatus] = Query(None, description="按文档状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """获取文档列表
    
    - 普通用户只能查看自己上传的文档
    - 管理员可以查看所有文档
    """
    try:
        # 构建查询条件
        filters = {}
        
        # 普通用户只能查看自己的文档
        if not current_user.get("is_admin", False):
            filters["created_by"] = current_user["id"]
        
        if document_type:
            filters["document_type"] = document_type
        
        if status:
            filters["status"] = status
        
        # 查询文档
        documents = await document_repository.find_documents(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应模型
        return [
            DocumentResponse(
                id=doc["id"],
                title=doc["title"],
                document_type=doc["document_type"],
                status=doc["status"],
                filename=doc["filename"],
                created_by=doc["created_by"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"]
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取文档详情
    
    - 普通用户只能查看自己上传的文档
    - 管理员可以查看所有文档
    """
    try:
        # 获取文档
        document = await document_repository.find_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文档"
            )
        
        return DocumentResponse(
            id=document["id"],
            title=document["title"],
            document_type=document["document_type"],
            status=document["status"],
            filename=document["filename"],
            created_by=document["created_by"],
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档失败: {str(e)}"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新文档信息
    
    - 普通用户只能更新自己上传的文档
    - 管理员可以更新所有文档
    """
    try:
        # 获取文档
        document = await document_repository.find_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新此文档"
            )
        
        # 准备更新数据
        update_data = document_update.dict(exclude_unset=True)
        
        # 更新文档
        updated_document = await document_repository.update_document(document_id, update_data)
        
        # 如果更新了内容，重新处理文档
        if "content" in update_data:
            await process_document_with_workflow(document_id, update_data["content"])
        
        return DocumentResponse(
            id=updated_document["id"],
            title=updated_document["title"],
            document_type=updated_document["document_type"],
            status=updated_document["status"],
            filename=updated_document["filename"],
            created_by=updated_document["created_by"],
            created_at=updated_document["created_at"],
            updated_at=updated_document["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档失败: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除文档
    
    - 普通用户只能删除自己上传的文档
    - 管理员可以删除所有文档
    """
    try:
        # 获取文档
        document = await document_repository.find_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此文档"
            )
        
        # 删除关联的知识图谱数据
        await knowledge_repository.delete_document_knowledge(document_id)
        
        # 删除文档
        await document_repository.delete_document(document_id)
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取文档完整内容
    
    - 普通用户只能查看自己上传的文档
    - 管理员可以查看所有文档
    """
    try:
        # 获取文档
        document = await document_repository.find_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文档"
            )
        
        return {
            "content": document.get("content", ""),
            "title": document["title"],
            "document_id": document["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档内容失败: {str(e)}"
        )