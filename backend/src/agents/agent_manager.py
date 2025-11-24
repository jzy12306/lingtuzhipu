from typing import Dict, Optional, List, Any
from src.agents.agent_base import BaseAgent
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AgentManager:
    """智能体管理器"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, type] = {}
        self.logger = logger.getChild("AgentManager")
    
    def register_agent_type(self, agent_type: type, agent_id_prefix: str):
        """注册智能体类型"""
        self.agent_types[agent_id_prefix] = agent_type
        self.logger.info(f"注册智能体类型: {agent_type.__name__} (前缀: {agent_id_prefix})")
    
    async def create_agent(self, agent_id: str, agent_name: str, agent_type: str, **config) -> BaseAgent:
        """创建智能体实例"""
        if agent_id in self.agents:
            raise ValueError(f"智能体ID已存在: {agent_id}")
        
        # 查找对应的智能体类型
        agent_class = None
        for prefix, cls in self.agent_types.items():
            if agent_type.lower() == prefix.lower() or agent_type.lower() == cls.__name__.lower():
                agent_class = cls
                break
        
        if not agent_class:
            raise ValueError(f"未知的智能体类型: {agent_type}")
        
        try:
            # 创建并初始化智能体
            agent = agent_class(agent_id, agent_name, **config)
            success = await agent.initialize()
            
            if success:
                self.agents[agent_id] = agent
                self.logger.info(f"创建智能体成功: {agent_name} (ID: {agent_id})")
                return agent
            else:
                raise ValueError(f"智能体初始化失败: {agent_name}")
        except Exception as e:
            self.logger.error(f"创建智能体失败: {str(e)}")
            raise
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体实例"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        return [
            {
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "type": agent.__class__.__name__
            }
            for agent in self.agents.values()
        ]
    
    async def shutdown_agent(self, agent_id: str) -> bool:
        """关闭智能体"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"智能体不存在: {agent_id}")
        
        try:
            success = await agent.shutdown()
            if success:
                del self.agents[agent_id]
                self.logger.info(f"关闭智能体成功: {agent_id}")
            return success
        except Exception as e:
            self.logger.error(f"关闭智能体失败: {str(e)}")
            raise
    
    async def shutdown_all(self):
        """关闭所有智能体"""
        for agent_id in list(self.agents.keys()):
            await self.shutdown_agent(agent_id)
        self.logger.info("所有智能体已关闭")
    
    async def process_with_agent(self, agent_id: str, input_data: Any) -> Any:
        """使用指定智能体处理数据"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体不存在: {agent_id}")
        
        try:
            result = await agent.process(input_data)
            return result
        except Exception as e:
            self.logger.error(f"智能体处理失败 [{agent_id}]: {str(e)}")
            raise


# 创建全局智能体管理器实例
agent_manager = AgentManager()