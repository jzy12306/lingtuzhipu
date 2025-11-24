import logging
from typing import Optional

from src.agents.builder.builder_agent import BuilderAgent
from src.agents.builder.llm_builder_agent import LLMBuilderAgent
from src.repositories.knowledge_repository import KnowledgeRepository
from src.utils.config import settings

logger = logging.getLogger(__name__)


def create_builder_agent(knowledge_repository: KnowledgeRepository) -> BuilderAgent:
    """
    创建构建者智能体实例
    
    Args:
        knowledge_repository: 知识仓库实例
        
    Returns:
        构建者智能体实例
    """
    # 根据配置选择合适的构建者智能体实现
    if settings.USE_LOCAL_LLM or settings.OPENAI_API_KEY:
        logger.info("创建LLM构建者智能体")
        return LLMBuilderAgent(knowledge_repository)
    else:
        logger.warning("未配置LLM，使用基本构建者智能体")
        # 如果需要，可以在这里返回一个基础实现
        return LLMBuilderAgent(knowledge_repository)  # 暂时仍返回LLM版本


# 智能体服务类
class BuilderAgentService:
    """构建者智能体服务，提供统一的接口"""
    
    _instance: Optional['BuilderAgentService'] = None
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        self.knowledge_repository = knowledge_repository
        self.builder_agent = create_builder_agent(knowledge_repository)
        logger.info("构建者智能体服务初始化完成")
    
    @classmethod
    def get_instance(cls, knowledge_repository: Optional[KnowledgeRepository] = None) -> 'BuilderAgentService':
        """
        获取单例实例
        
        Args:
            knowledge_repository: 知识仓库实例（首次调用时必需）
            
        Returns:
            构建者智能体服务实例
        
        Raises:
            ValueError: 如果首次调用时未提供knowledge_repository
        """
        if cls._instance is None:
            if knowledge_repository is None:
                raise ValueError("首次调用必须提供knowledge_repository")
            cls._instance = cls(knowledge_repository)
        return cls._instance
    
    async def process_document_by_id(self, document_id: str) -> dict:
        """
        根据文档ID处理文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            处理结果
            
        Raises:
            ValueError: 如果文档不存在
        """
        # 获取文档
        document = await self.knowledge_repository.get_document(document_id)
        if not document:
            raise ValueError(f"文档不存在: {document_id}")
        
        # 检查文档状态
        if document.status == "processing":
            raise ValueError("文档正在处理中")
        
        if document.status == "processed":
            raise ValueError("文档已经处理过")
        
        # 调用智能体处理文档
        return await self.builder_agent.process_document(document)
    
    async def batch_process_documents(self, document_ids: list, max_concurrent: int = 2) -> list:
        """
        批量处理文档
        
        Args:
            document_ids: 文档ID列表
            max_concurrent: 最大并发数
            
        Returns:
            处理结果列表
        """
        import asyncio
        
        # 限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(doc_id):
            async with semaphore:
                try:
                    result = await self.process_document_by_id(doc_id)
                    return {
                        "document_id": doc_id,
                        "status": "success",
                        "result": result
                    }
                except Exception as e:
                    logger.error(f"处理文档失败: {doc_id}, 错误: {str(e)}")
                    return {
                        "document_id": doc_id,
                        "status": "error",
                        "error": str(e)
                    }
        
        # 并发处理
        tasks = [process_with_semaphore(doc_id) for doc_id in document_ids]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return results
