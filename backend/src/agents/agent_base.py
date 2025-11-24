from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generic, TypeVar
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


class AgentResult(BaseModel):
    """智能体执行结果"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class BaseAgent(ABC, Generic[T, U]):
    """智能体基类"""
    
    def __init__(self, agent_id: str, agent_name: str, **kwargs):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.logger = logger.getChild(f"{self.__class__.__name__}[{agent_id}]")
        self.config = kwargs.get('config', {})
    
    @abstractmethod
    async def process(self, input_data: T) -> AgentResult:
        """处理输入数据并返回结果"""
        pass
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        try:
            self.logger.info(f"初始化智能体: {self.agent_name}")
            return True
        except Exception as e:
            self.logger.error(f"智能体初始化失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭智能体资源"""
        try:
            self.logger.info(f"关闭智能体: {self.agent_name}")
            return True
        except Exception as e:
            self.logger.error(f"智能体关闭失败: {str(e)}")
            return False
    
    def _create_success_result(self, data: Any = None, message: str = "") -> AgentResult:
        """创建成功结果"""
        return AgentResult(
            success=True,
            data=data,
            message=message,
            metrics={"agent": self.agent_name}
        )
    
    def _create_error_result(self, error: str, message: str = "") -> AgentResult:
        """创建错误结果"""
        return AgentResult(
            success=False,
            error=error,
            message=message,
            metrics={"agent": self.agent_name}
        )
    
    async def validate_input(self, input_data: T) -> Optional[str]:
        """验证输入数据"""
        if input_data is None:
            return "输入数据不能为空"
        return None