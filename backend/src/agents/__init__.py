"""智能体系统包"""

from src.agents.agent_base import BaseAgent, AgentResult
from src.agents.agent_manager import agent_manager
from src.agents.workflow import AgentWorkflow, WorkflowNode, workflow_manager
from src.agents.langgraph_integration import langgraph_integration

__all__ = [
    "BaseAgent",
    "AgentResult",
    "agent_manager",
    "AgentWorkflow",
    "WorkflowNode",
    "workflow_manager",
    "langgraph_integration"
]


async def initialize_agent_system():
    """初始化智能体系统"""
    try:
        # 初始化LangGraph工作流
        from src.agents.agent_manager import agent_manager
        
        # 创建知识处理工作流
        langgraph_integration.create_knowledge_processing_graph(agent_manager)
        
        # 创建查询处理工作流
        langgraph_integration.create_query_processing_graph(agent_manager)
        
        # 注册基本工作流
        knowledge_workflow = AgentWorkflow(
            "knowledge_processing_basic",
            "基础知识处理工作流"
        )
        
        # 添加节点
        analyze_node = WorkflowNode("analyze", "agent", "analyzer")
        extract_node = WorkflowNode("extract", "agent", "builder")
        validate_node = WorkflowNode("validate", "agent", "auditor")
        
        # 设置节点关系
        analyze_node.add_next_node("success", "extract")
        analyze_node.add_next_node("failure", "error")
        extract_node.add_next_node("success", "validate")
        extract_node.add_next_node("failure", "error")
        validate_node.add_next_node("success", "complete")
        validate_node.add_next_node("failure", "error")
        
        # 添加到工作流
        knowledge_workflow.add_node(analyze_node)
        knowledge_workflow.add_node(extract_node)
        knowledge_workflow.add_node(validate_node)
        
        # 注册工作流
        workflow_manager.register_workflow(knowledge_workflow)
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"智能体系统初始化失败: {str(e)}")
        return False


async def process_document_with_workflow(document_content: str) -> dict:
    """使用工作流处理文档"""
    try:
        # 使用LangGraph工作流
        result = await langgraph_integration.run_graph(
            "knowledge_processing",
            {"document_content": document_content}
        )
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"文档处理失败: {str(e)}")
        raise


async def process_query_with_workflow(query: str) -> dict:
    """使用工作流处理查询"""
    try:
        # 使用LangGraph工作流
        result = await langgraph_integration.run_graph(
            "query_processing",
            {"query": query}
        )
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"查询处理失败: {str(e)}")
        raise