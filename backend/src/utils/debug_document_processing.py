#!/usr/bin/env python3
"""
调试文档处理流程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from src.services.service_factory import service_factory
from src.repositories.document_repository import DocumentRepository
from src.repositories.knowledge_repository import KnowledgeRepository

async def debug_document(doc_id: str):
    """调试文档处理"""
    print(f"=== 调试文档: {doc_id} ===")
    
    # 初始化服务
    await service_factory.initialize_all()
    
    # 获取文档
    doc_repo = DocumentRepository()
    doc = await doc_repo.get_document(doc_id)
    
    print(f"文档状态: {doc.status}")
    print(f"实体数量: {doc.entities_count}")
    print(f"关系数量: {doc.relations_count}")
    
    # 获取知识图谱数据
    knowledge_repo = KnowledgeRepository()
    
    entities = await knowledge_repo.find_entities_by_document(doc_id)
    print(f"实际实体数量: {len(entities)}")
    
    relations = await knowledge_repo.find_relations_by_document(doc_id)
    print(f"实际关系数量: {len(relations)}")
    
    if entities:
        print(f"\n前3个实体:")
        for e in entities[:3]:
            print(f"  - {e.name} ({e.type})")
    
    if relations:
        print(f"\n前3个关系:")
        for r in relations[:3]:
            print(f"  - {r.type}: {r.source_entity_name} -> {r.target_entity_name}")
    
    await service_factory.shutdown_all()

if __name__ == "__main__":
    # 替换为实际文档ID
    doc_id = "your_document_id_here"
    asyncio.run(debug_document(doc_id))
