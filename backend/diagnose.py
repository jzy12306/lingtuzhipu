#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件上传问题诊断脚本
用于检查前后端配置和服务状态
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_llm_service():
    """检查LLM服务配置"""
    print("\n" + "="*50)
    print("1. 检查LLM服务配置")
    print("="*50)
    
    try:
        from src.services.llm_service import llm_service
        from src.config.settings import settings
        
        print(f"✓ LLM服务模块加载成功")
        print(f"  - Kimi API Key: {settings.API_KEY[:10]}..." if settings.API_KEY else "  - Kimi API Key: 未配置")
        print(f"  - Kimi Base URL: {settings.API_BASE}")
        print(f"  - 本地LLM启用: {settings.LOCAL_LLM_ENABLED}")
        
        # 测试LLM调用
        print("\n测试LLM调用...")
        try:
            response = await llm_service.generate_text(
                prompt="请提取以下文本中的实体: 项目知识图谱构建需求",
                system_message="你是一个知识图谱专家",
                max_tokens=100,
                temperature=0.3
            )
            print(f"✓ LLM调用成功")
            print(f"  响应: {response[:100]}...")
            return True
        except Exception as e:
            print(f"✗ LLM调用失败: {str(e)}")
            return False
            
    except Exception as e:
        print(f"✗ LLM服务检查失败: {str(e)}")
        return False


async def check_ocr_service():
    """检查OCR服务配置"""
    print("\n" + "="*50)
    print("2. 检查OCR服务配置")
    print("="*50)
    
    try:
        from src.services.ocr_service import ocr_service
        
        print(f"✓ OCR服务模块加载成功")
        print(f"  - 有道智云 App Key: {ocr_service.app_key}")
        print(f"  - 有道智云 API URL: {ocr_service.youdao_url}")
        
        return True
    except Exception as e:
        print(f"✗ OCR服务检查失败: {str(e)}")
        return False


async def check_database():
    """检查数据库连接"""
    print("\n" + "="*50)
    print("3. 检查数据库连接")
    print("="*50)
    
    try:
        from src.services.db_service import db_service
        
        # 初始化数据库服务
        await db_service.initialize()
        
        # 检查MongoDB
        try:
            mongo_db = await db_service.get_mongodb()
            collections = await mongo_db.list_collection_names()
            print(f"✓ MongoDB连接成功")
            print(f"  - 集合数: {len(collections)}")
        except Exception as e:
            print(f"✗ MongoDB连接失败: {str(e)}")
        
        # 检查Neo4j
        try:
            from src.repositories.knowledge_repository import KnowledgeRepository
            repo = KnowledgeRepository()
            print(f"✓ Neo4j配置加载成功")
        except Exception as e:
            print(f"✗ Neo4j配置失败: {str(e)}")
        
        return True
    except Exception as e:
        print(f"✗ 数据库检查失败: {str(e)}")
        return False


async def check_builder_agent():
    """检查构建者智能体"""
    print("\n" + "="*50)
    print("4. 检查构建者智能体")
    print("="*50)
    
    try:
        from src.agents.builder.llm_builder_agent import LLMBuilderAgent
        from src.repositories.knowledge_repository import KnowledgeRepository
        
        repo = KnowledgeRepository()
        agent = LLMBuilderAgent(repo)
        
        print(f"✓ 构建者智能体加载成功")
        print(f"  - 智能体类型: {type(agent).__name__}")
        print(f"  - 启用状态: {agent.enabled}")
        
        # 测试实体提取
        print("\n测试实体提取...")
        try:
            test_content = "项目: 知识库行业知识图谱构建与多模态数据关联"
            entities = await agent.extract_entities(
                content=test_content,
                document_id="test",
                user_id="test"
            )
            print(f"✓ 实体提取成功, 提取到 {len(entities)} 个实体")
            for entity in entities[:3]:
                print(f"  - {entity.name} ({entity.type})")
        except Exception as e:
            print(f"✗ 实体提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return True
    except Exception as e:
        print(f"✗ 构建者智能体检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "="*70)
    print(" " * 20 + "系统诊断开始")
    print("="*70)
    
    results = []
    
    # 检查各个服务
    results.append(("LLM服务", await check_llm_service()))
    results.append(("OCR服务", await check_ocr_service()))
    results.append(("数据库", await check_database()))
    results.append(("构建者智能体", await check_builder_agent()))
    
    # 汇总结果
    print("\n" + "="*70)
    print(" " * 20 + "诊断结果汇总")
    print("="*70)
    
    for name, success in results:
        status = "✓ 正常" if success else "✗ 异常"
        print(f"{name:20} {status}")
    
    # 诊断建议
    print("\n" + "="*70)
    print("诊断建议:")
    print("="*70)
    
    if not results[0][1]:  # LLM服务失败
        print("⚠ LLM服务异常,请检查:")
        print("  1. Kimi API Key是否配置正确")
        print("  2. 网络连接是否正常")
        print("  3. Kimi API是否有剩余额度")
    
    if not results[3][1]:  # 构建者智能体失败
        print("⚠ 构建者智能体异常,这会导致文档处理失败")
        print("  请检查上述LLM服务和数据库配置")
    
    print("\n" + "="*70)
    print("诊断完成! 请根据上述结果排查问题。")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
