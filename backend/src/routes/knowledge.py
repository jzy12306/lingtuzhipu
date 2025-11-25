from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Tuple

from models.knowledge import (
    Entity, EntityCreate, EntityUpdate, EntityResponse,
    Relation, RelationCreate, RelationUpdate, RelationResponse,
    KnowledgeStats, KnowledgeGraphPath, GraphVisualization,
    KnowledgeGraphQuery, KnowledgeGraphQueryAdvanced, KnowledgeConflict
)
from repositories.knowledge_repository import KnowledgeRepository
from utils.dependencies import get_current_user, validate_knowledge_permission
from models.user import User

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def get_knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository()


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity_data: EntityCreate,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """创建新实体"""
    try:
        entity = await knowledge_repo.create_entity(
            entity_data=entity_data,
            user_id=current_user.id
        )
        return entity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    document_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取实体列表"""
    try:
        entities = await knowledge_repo.find_entities(
            skip=skip,
            limit=limit,
            entity_type=entity_type,
            search=search,
            document_id=document_id,
            user_id=current_user.id if not current_user.is_admin else None
        )
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取实体详情"""
    entity = await knowledge_repo.find_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    # 验证权限
    if entity.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此实体")
    
    return entity


@router.put("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    entity_update: EntityUpdate,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """更新实体"""
    # 获取实体以验证权限
    entity = await knowledge_repo.find_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    # 检查是否是实体创建者或管理员
    if entity.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权更新此实体")
    
    updated_entity = await knowledge_repo.update_entity(entity_id, entity_update)
    if not updated_entity:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_entity


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """删除实体"""
    # 获取实体以验证权限
    entity = await knowledge_repo.find_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    # 检查是否是实体创建者或管理员
    if entity.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此实体")
    
    success = await knowledge_repo.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="删除失败")
    
    return {"message": "实体删除成功"}


@router.post("/relations", response_model=RelationResponse)
async def create_relation(
    relation_data: RelationCreate,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """创建新关系"""
    try:
        # 验证源实体和目标实体是否存在且有权限
        source_entity = await knowledge_repo.find_entity_by_id(relation_data.source_entity_id)
        target_entity = await knowledge_repo.find_entity_by_id(relation_data.target_entity_id)
        
        if not source_entity or not target_entity:
            raise HTTPException(status_code=404, detail="源实体或目标实体不存在")
        
        if (source_entity.user_id != current_user.id and 
            target_entity.user_id != current_user.id and 
            not current_user.is_admin):
            raise HTTPException(status_code=403, detail="无权在这些实体之间创建关系")
        
        relation = await knowledge_repo.create_relation(
            relation_data=relation_data,
            user_id=current_user.id
        )
        return relation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relations", response_model=List[RelationResponse])
async def list_relations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    relation_type: Optional[str] = None,
    source_entity_id: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    document_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取关系列表"""
    try:
        relations = await knowledge_repo.find_relations(
            skip=skip,
            limit=limit,
            relation_type=relation_type,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            document_id=document_id,
            user_id=current_user.id if not current_user.is_admin else None
        )
        return relations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relations/{relation_id}", response_model=RelationResponse)
async def get_relation(
    relation_id: str,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取关系详情"""
    relation = await knowledge_repo.find_relation_by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    
    # 验证权限
    if relation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此关系")
    
    return relation


@router.put("/relations/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: str,
    relation_update: RelationUpdate,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """更新关系"""
    # 获取关系以验证权限
    relation = await knowledge_repo.find_relation_by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    
    # 检查是否是关系创建者或管理员
    if relation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权更新此关系")
    
    updated_relation = await knowledge_repo.update_relation(relation_id, relation_update)
    if not updated_relation:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_relation


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: str,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """删除关系"""
    # 获取关系以验证权限
    relation = await knowledge_repo.find_relation_by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    
    # 检查是否是关系创建者或管理员
    if relation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此关系")
    
    success = await knowledge_repo.delete_relation(relation_id)
    if not success:
        raise HTTPException(status_code=404, detail="删除失败")
    
    return {"message": "关系删除成功"}


@router.post("/graph/query", response_model=dict)
async def query_knowledge_graph(
    query: KnowledgeGraphQueryAdvanced,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """查询知识图谱"""
    try:
        entities, relations = await knowledge_repo.query_knowledge_graph(query)
        return {
            "entities": entities,
            "relations": relations,
            "total_entities": len(entities),
            "total_relations": len(relations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_statistics(
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取知识图谱统计信息"""
    try:
        stats = await knowledge_repo.get_knowledge_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path", response_model=KnowledgeGraphPath)
async def find_entity_path(
    source_id: str = Query(..., description="源实体ID"),
    target_id: str = Query(..., description="目标实体ID"),
    max_depth: int = Query(3, ge=1, le=5, description="最大搜索深度"),
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """查找两个实体之间的路径"""
    try:
        # 验证实体权限
        source_entity = await knowledge_repo.find_entity_by_id(source_id)
        target_entity = await knowledge_repo.find_entity_by_id(target_id)
        
        if not source_entity or not target_entity:
            raise HTTPException(status_code=404, detail="源实体或目标实体不存在")
        
        if (source_entity.user_id != current_user.id and 
            target_entity.user_id != current_user.id and 
            not current_user.is_admin):
            raise HTTPException(status_code=403, detail="无权访问这些实体")
        
        path = await knowledge_repo.find_entity_path(source_id, target_id, max_depth)
        if not path:
            raise HTTPException(status_code=404, detail="未找到实体间的路径")
        
        return path
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization", response_model=GraphVisualization)
async def get_visualization_data(
    query: Optional[KnowledgeGraphQueryAdvanced] = None,
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """获取知识图谱可视化数据"""
    try:
        # 限制非管理员的数据范围
        if not current_user.is_admin and query:
            # 这里可以添加用户权限过滤逻辑
            pass
        
        visualization_data = await knowledge_repo.get_visualization_data(query)
        return visualization_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts", response_model=List[KnowledgeConflict])
async def detect_knowledge_conflicts(
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """检测知识冲突"""
    try:
        conflicts = await knowledge_repo.find_conflicts()
        
        # 根据用户权限过滤冲突
        if not current_user.is_admin:
            conflicts = [c for c in conflicts if any(e.user_id == current_user.id for e in c.entities)]
        
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/entities", response_model=List[EntityResponse])
async def batch_create_entities(
    entities_data: List[EntityCreate],
    current_user: User = Depends(get_current_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository)
):
    """批量创建实体"""
    if len(entities_data) > 50:
        raise HTTPException(status_code=400, detail="一次最多只能创建50个实体")
    
    created_entities = []
    errors = []
    
    for i, entity_data in enumerate(entities_data):
        try:
            entity = await knowledge_repo.create_entity(
                entity_data=entity_data,
                user_id=current_user.id
            )
            created_entities.append(entity)
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"created": len(created_entities), "errors": errors}
        )
    
    return created_entities
