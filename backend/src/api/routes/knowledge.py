from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from models.knowledge import (
    EntityResponse, RelationResponse, EntityCreate, RelationCreate,
    EntityUpdate, RelationUpdate, KnowledgeGraphQuery, KnowledgeGraphResponse,
    KnowledgeConflictResponse
)
from repositories.knowledge_repository import knowledge_repository
from repositories.document_repository import document_repository
from utils.dependencies import get_current_user

router = APIRouter()


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建新实体"""
    try:
        # 验证文档权限
        if entity.document_id:
            document = await document_repository.find_by_id(entity.document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联文档不存在"
                )
            
            # 检查权限
            if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权为此文档创建实体"
                )
        
        # 创建实体
        created_entity = await knowledge_repository.create_entity(
            entity.dict(),
            created_by=current_user["id"]
        )
        
        return EntityResponse(
            id=created_entity["id"],
            name=created_entity["name"],
            type=created_entity["type"],
            properties=created_entity.get("properties", {}),
            document_id=created_entity.get("document_id"),
            created_by=created_entity["created_by"],
            created_at=created_entity["created_at"],
            updated_at=created_entity["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建实体失败: {str(e)}"
        )


@router.get("/entities", response_model=List[EntityResponse])
async def get_entities(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    entity_type: Optional[str] = Query(None, description="按实体类型筛选"),
    document_id: Optional[str] = Query(None, description="按文档ID筛选"),
    current_user: dict = Depends(get_current_user)
):
    """获取实体列表
    
    - 普通用户只能查看自己文档中的实体
    - 管理员可以查看所有实体
    """
    try:
        # 构建查询条件
        filters = {}
        
        if entity_type:
            filters["type"] = entity_type
        
        if document_id:
            # 验证文档权限
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
                    detail="无权访问此文档的实体"
                )
            
            filters["document_id"] = document_id
        else:
            # 普通用户只能查看自己的文档实体
            if not current_user.get("is_admin", False):
                user_documents = await document_repository.find_documents(
                    filters={"created_by": current_user["id"]},
                    limit=1000
                )
                if user_documents:
                    filters["document_id"] = {"$in": [doc["id"] for doc in user_documents]}
                else:
                    # 如果用户没有文档，返回空列表
                    return []
        
        # 查询实体
        entities = await knowledge_repository.find_entities(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应模型
        return [
            EntityResponse(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                properties=entity.get("properties", {}),
                document_id=entity.get("document_id"),
                created_by=entity["created_by"],
                created_at=entity["created_at"],
                updated_at=entity["updated_at"]
            )
            for entity in entities
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实体列表失败: {str(e)}"
        )


@router.post("/relations", response_model=RelationResponse)
async def create_relation(
    relation: RelationCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建新关系"""
    try:
        # 验证源实体和目标实体是否存在
        source_entity = await knowledge_repository.find_entity_by_id(relation.source_id)
        target_entity = await knowledge_repository.find_entity_by_id(relation.target_id)
        
        if not source_entity or not target_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="源实体或目标实体不存在"
            )
        
        # 检查权限：用户只能为自己的文档创建关系
        if not current_user.get("is_admin", False):
            source_doc_id = source_entity.get("document_id")
            target_doc_id = target_entity.get("document_id")
            
            # 验证文档权限
            for doc_id in [source_doc_id, target_doc_id]:
                if doc_id:
                    document = await document_repository.find_by_id(doc_id)
                    if document and document["created_by"] != current_user["id"]:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="无权为此文档创建关系"
                        )
        
        # 创建关系
        created_relation = await knowledge_repository.create_relation(
            relation.dict(),
            created_by=current_user["id"]
        )
        
        return RelationResponse(
            id=created_relation["id"],
            source_id=created_relation["source_id"],
            target_id=created_relation["target_id"],
            type=created_relation["type"],
            properties=created_relation.get("properties", {}),
            created_by=created_relation["created_by"],
            created_at=created_relation["created_at"],
            updated_at=created_relation["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建关系失败: {str(e)}"
        )


@router.post("/graph/query", response_model=KnowledgeGraphResponse)
async def query_knowledge_graph(
    query: KnowledgeGraphQuery,
    current_user: dict = Depends(get_current_user)
):
    """查询知识图谱"""
    try:
        # 如果指定了文档ID，验证权限
        if query.document_id:
            document = await document_repository.find_by_id(query.document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )
            
            # 检查权限
            if not current_user.get("is_admin", False) and document["created_by"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查询此文档的知识图谱"
                )
        else:
            # 普通用户只能查询自己的文档
            if not current_user.get("is_admin", False):
                user_documents = await document_repository.find_documents(
                    filters={"created_by": current_user["id"]},
                    limit=1000
                )
                if user_documents:
                    query.document_ids = [doc["id"] for doc in user_documents]
                else:
                    # 如果用户没有文档，返回空结果
                    return KnowledgeGraphResponse(entities=[], relations=[])
        
        # 执行查询
        result = await knowledge_repository.query_knowledge_graph(query.dict())
        
        # 转换为响应模型
        entities_response = [
            EntityResponse(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                properties=entity.get("properties", {}),
                document_id=entity.get("document_id"),
                created_by=entity["created_by"],
                created_at=entity["created_at"],
                updated_at=entity["updated_at"]
            )
            for entity in result["entities"]
        ]
        
        relations_response = [
            RelationResponse(
                id=relation["id"],
                source_id=relation["source_id"],
                target_id=relation["target_id"],
                type=relation["type"],
                properties=relation.get("properties", {}),
                created_by=relation["created_by"],
                created_at=relation["created_at"],
                updated_at=relation["updated_at"]
            )
            for relation in result["relations"]
        ]
        
        return KnowledgeGraphResponse(
            entities=entities_response,
            relations=relations_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询知识图谱失败: {str(e)}"
        )


@router.post("/conflicts/check", response_model=List[KnowledgeConflictResponse])
async def check_knowledge_conflicts(
    query: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """检查知识冲突"""
    try:
        # 验证文档权限
        document_id = query.get("document_id")
        if document_id:
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
                    detail="无权为此文档检查冲突"
                )
        
        # 检查冲突
        conflicts = await knowledge_repository.check_conflicts(query)
        
        # 转换为响应模型
        return [
            KnowledgeConflictResponse(
                type=conflict["type"],
                level=conflict["level"],
                description=conflict["description"],
                entity_id=conflict.get("entity_id"),
                relation_id=conflict.get("relation_id"),
                related_entities=conflict.get("related_entities", [])
            )
            for conflict in conflicts
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查知识冲突失败: {str(e)}"
        )


@router.get("/documents/{document_id}/stats")
async def get_document_knowledge_stats(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取文档的知识统计信息"""
    try:
        # 验证文档权限
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
                detail="无权查看此文档的知识统计"
            )
        
        # 获取统计信息
        stats = await knowledge_repository.get_document_knowledge_stats(document_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识统计信息失败: {str(e)}"
        )