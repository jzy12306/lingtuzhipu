from langgraph.graph import Graph
from typing import Dict, Any, Optional
import asyncio
import logging
from agents.agent_base import AgentResult

logger = logging.getLogger(__name__)


class WorkflowNode:
    """工作流节点"""
    
    def __init__(self, node_id: str, node_type: str, agent_id: str):
        self.node_id = node_id
        self.node_type = node_type  # agent, decision, action
        self.agent_id = agent_id
        self.next_nodes: Dict[str, str] = {}  # condition -> next_node_id
    
    def add_next_node(self, condition: str, next_node_id: str):
        """添加下一个节点"""
        self.next_nodes[condition] = next_node_id


class AgentWorkflow:
    """智能体工作流"""
    
    def __init__(self, workflow_id: str, workflow_name: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.start_node_id: Optional[str] = None
        self.logger = logger.getChild(f"Workflow[{workflow_id}]")
    
    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.node_id] = node
        if len(self.nodes) == 1:
            self.start_node_id = node.node_id
    
    def set_start_node(self, node_id: str):
        """设置起始节点"""
        if node_id not in self.nodes:
            raise ValueError(f"节点不存在: {node_id}")
        self.start_node_id = node_id
    
    async def execute(self, agent_manager, input_data: Any) -> Dict[str, Any]:
        """执行工作流"""
        if not self.start_node_id:
            raise ValueError("工作流未设置起始节点")
        
        current_node_id = self.start_node_id
        execution_history = []
        result = None
        
        try:
            while current_node_id:
                node = self.nodes.get(current_node_id)
                if not node:
                    raise ValueError(f"节点不存在: {current_node_id}")
                
                self.logger.info(f"执行节点: {current_node_id} (类型: {node.node_type})")
                
                # 执行节点
                if node.node_type == "agent":
                    # 使用智能体处理数据
                    node_result = await agent_manager.process_with_agent(
                        node.agent_id, 
                        input_data if result is None else result.data
                    )
                    
                    execution_history.append({
                        "node_id": current_node_id,
                        "agent_id": node.agent_id,
                        "result": node_result.dict()
                    })
                    
                    result = node_result
                    
                    # 根据执行结果决定下一个节点
                    next_condition = "success" if result.success else "failure"
                    current_node_id = node.next_nodes.get(next_condition)
                    
                elif node.node_type == "decision":
                    # 决策节点（简化实现）
                    next_condition = "default"
                    current_node_id = node.next_nodes.get(next_condition)
                    
                elif node.node_type == "action":
                    # 动作节点（简化实现）
                    current_node_id = node.next_nodes.get("default")
                
                else:
                    raise ValueError(f"未知的节点类型: {node.node_type}")
            
            return {
                "workflow_id": self.workflow_id,
                "success": result.success if result else False,
                "result": result.dict() if result else None,
                "execution_history": execution_history
            }
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {str(e)}")
            raise


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.workflows: Dict[str, AgentWorkflow] = {}
        self.logger = logger.getChild("WorkflowManager")
    
    def register_workflow(self, workflow: AgentWorkflow):
        """注册工作流"""
        self.workflows[workflow.workflow_id] = workflow
        self.logger.info(f"注册工作流: {workflow.workflow_name} (ID: {workflow.workflow_id})")
    
    def get_workflow(self, workflow_id: str) -> Optional[AgentWorkflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    async def execute_workflow(self, workflow_id: str, agent_manager, input_data: Any) -> Dict[str, Any]:
        """执行工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        return await workflow.execute(agent_manager, input_data)
    
    def list_workflows(self) -> Dict[str, str]:
        """列出所有工作流"""
        return {
            wf.workflow_id: wf.workflow_name
            for wf in self.workflows.values()
        }


# 创建全局工作流管理器实例
workflow_manager = WorkflowManager()