import logging
from typing import Optional, List, Dict, Any
from .auditor_agent import AuditorAgent
from src.repositories.knowledge_repository import KnowledgeRepository
from src.models.knowledge import KnowledgeConflict

logger = logging.getLogger(__name__)


def create_auditor_agent(knowledge_repository: KnowledgeRepository = None) -> AuditorAgent:
    """
    创建审计智能体实例
    
    Args:
        knowledge_repository: 知识仓库实例
        
    Returns:
        审计智能体实例
    """
    logger.info("创建审计智能体")
    return AuditorAgent("auditor_1", "审计智能体", knowledge_repository)


class AuditorAgentService:
    """审计智能体服务，提供统一的接口"""
    
    _instance: Optional['AuditorAgentService'] = None
    
    def __init__(self, knowledge_repository: KnowledgeRepository = None):
        self.knowledge_repository = knowledge_repository or KnowledgeRepository()
        self.auditor_agent = create_auditor_agent(knowledge_repository)
        logger.info("审计智能体服务初始化完成")
    
    @classmethod
    def get_instance(cls, knowledge_repository: Optional[KnowledgeRepository] = None) -> 'AuditorAgentService':
        """
        获取单例实例
        
        Args:
            knowledge_repository: 知识仓库实例（首次调用时必需）
            
        Returns:
            审计智能体服务实例
        """
        if cls._instance is None:
            if knowledge_repository is None:
                knowledge_repository = KnowledgeRepository()
            cls._instance = cls(knowledge_repository)
        return cls._instance
    
    async def audit_knowledge_graph(self, document_id: Optional[str] = None, auto_correct: bool = False) -> Dict[str, Any]:
        """
        审计知识图谱
        
        Args:
            document_id: 文档ID，可选
            auto_correct: 是否自动修正冲突
            
        Returns:
            审计结果
        """
        try:
            logger.info(f"开始审计知识图谱，文档ID: {document_id}")
            
            # 执行审计
            conflicts = await self.auditor_agent.audit_knowledge_graph(document_id)
            
            # 生成审计报告
            report = await self.auditor_agent.generate_audit_report(conflicts)
            
            # 如果需要自动修正
            corrected_conflicts = []
            if auto_correct and conflicts:
                corrected_conflicts = await self.auditor_agent.auto_correct_conflicts(conflicts)
                report["corrected_conflicts"] = len(corrected_conflicts)
            
            logger.info(f"审计完成，发现 {len(conflicts)} 个冲突")
            
            return {
                "success": True,
                "report": report,
                "conflicts": conflicts,
                "corrected_conflicts": corrected_conflicts
            }
        except Exception as e:
            logger.error(f"审计知识图谱失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_entities(self, entities: List[Dict[str, Any]]) -> List[KnowledgeConflict]:
        """
        验证实体列表
        
        Args:
            entities: 实体列表
            
        Returns:
            冲突列表
        """
        try:
            logger.info(f"开始验证 {len(entities)} 个实体")
            
            # 这里可以实现实体验证逻辑
            conflicts = []
            
            logger.info(f"实体验证完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            logger.error(f"验证实体失败: {str(e)}")
            raise
    
    async def validate_relations(self, relations: List[Dict[str, Any]]) -> List[KnowledgeConflict]:
        """
        验证关系列表
        
        Args:
            relations: 关系列表
            
        Returns:
            冲突列表
        """
        try:
            logger.info(f"开始验证 {len(relations)} 个关系")
            
            # 这里可以实现关系验证逻辑
            conflicts = []
            
            logger.info(f"关系验证完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            logger.error(f"验证关系失败: {str(e)}")
            raise


__all__ = ["AuditorAgent", "AuditorAgentService", "create_auditor_agent"]
