import logging
from typing import Dict, Any, Optional, List
from src.agents.agent_base import BaseAgent, AgentResult
from src.agents.extension.plugin_manager import PluginManager
from src.agents.extension.sandbox_executor import SandboxExecutor
from src.agents.extension.api_gateway import APIGateway
from src.agents.extension.extension_point import ExtensionPointManager

logger = logging.getLogger(__name__)


class ExtensionAgent(BaseAgent):
    """扩展智能体"""
    
    def __init__(self, agent_id: str, agent_name: str, **kwargs):
        super().__init__(agent_id, agent_name, **kwargs)
        self.plugin_manager = PluginManager()
        self.sandbox_executor = SandboxExecutor()
        self.api_gateway = APIGateway()
        self.extension_point_manager = ExtensionPointManager()
        self.logger = logger.getChild(f"ExtensionAgent[{agent_id}]")
    
    async def initialize(self) -> bool:
        """初始化扩展智能体"""
        try:
            self.logger.info(f"初始化扩展智能体: {self.agent_name}")
            
            # 初始化插件管理器
            await self.plugin_manager.initialize()
            self.logger.info("插件管理器初始化完成")
            
            # 初始化沙箱执行器
            await self.sandbox_executor.initialize()
            self.logger.info("沙箱执行器初始化完成")
            
            # 初始化API网关
            await self.api_gateway.initialize()
            self.logger.info("API网关初始化完成")
            
            # 初始化扩展点管理器
            await self.extension_point_manager.initialize()
            self.logger.info("扩展点管理器初始化完成")
            
            self.logger.info("扩展智能体初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"扩展智能体初始化失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭扩展智能体"""
        try:
            self.logger.info(f"关闭扩展智能体: {self.agent_name}")
            
            # 关闭插件管理器
            await self.plugin_manager.shutdown()
            self.logger.info("插件管理器已关闭")
            
            # 关闭沙箱执行器
            await self.sandbox_executor.shutdown()
            self.logger.info("沙箱执行器已关闭")
            
            # 关闭API网关
            await self.api_gateway.shutdown()
            self.logger.info("API网关已关闭")
            
            # 关闭扩展点管理器
            await self.extension_point_manager.shutdown()
            self.logger.info("扩展点管理器已关闭")
            
            self.logger.info("扩展智能体已关闭")
            return True
        except Exception as e:
            self.logger.error(f"关闭扩展智能体失败: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理输入数据"""
        try:
            self.logger.info(f"处理输入数据: {input_data}")
            
            # 验证输入
            validation_error = await self.validate_input(input_data)
            if validation_error:
                return self._create_error_result(validation_error, "输入数据验证失败")
            
            # 提取操作类型
            operation = input_data.get("operation")
            if not operation:
                return self._create_error_result("operation is required", "缺少操作类型")
            
            # 根据操作类型执行不同的处理
            if operation == "plugin_management":
                result = await self._handle_plugin_management(input_data)
            elif operation == "sandbox_execution":
                result = await self._handle_sandbox_execution(input_data)
            elif operation == "api_gateway":
                result = await self._handle_api_gateway(input_data)
            elif operation == "extension_point":
                result = await self._handle_extension_point(input_data)
            else:
                return self._create_error_result(f"unknown operation: {operation}", "未知的操作类型")
            
            return self._create_success_result(result, f"操作 {operation} 执行成功")
        except Exception as e:
            self.logger.error(f"处理输入数据失败: {str(e)}")
            return self._create_error_result(str(e), "处理失败")
    
    async def _handle_plugin_management(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理插件管理操作"""
        try:
            plugin_operation = input_data.get("plugin_operation")
            if not plugin_operation:
                raise ValueError("plugin_operation is required")
            
            if plugin_operation == "list_plugins":
                return await self.plugin_manager.list_plugins()
            elif plugin_operation == "load_plugin":
                plugin_name = input_data.get("plugin_name")
                if not plugin_name:
                    raise ValueError("plugin_name is required")
                return await self.plugin_manager.load_plugin(plugin_name)
            elif plugin_operation == "unload_plugin":
                plugin_name = input_data.get("plugin_name")
                if not plugin_name:
                    raise ValueError("plugin_name is required")
                return await self.plugin_manager.unload_plugin(plugin_name)
            elif plugin_operation == "enable_plugin":
                plugin_name = input_data.get("plugin_name")
                if not plugin_name:
                    raise ValueError("plugin_name is required")
                return await self.plugin_manager.enable_plugin(plugin_name)
            elif plugin_operation == "disable_plugin":
                plugin_name = input_data.get("plugin_name")
                if not plugin_name:
                    raise ValueError("plugin_name is required")
                return await self.plugin_manager.disable_plugin(plugin_name)
            elif plugin_operation == "get_plugin_info":
                plugin_name = input_data.get("plugin_name")
                if not plugin_name:
                    raise ValueError("plugin_name is required")
                return await self.plugin_manager.get_plugin_info(plugin_name)
            else:
                raise ValueError(f"unknown plugin operation: {plugin_operation}")
        except Exception as e:
            self.logger.error(f"处理插件管理操作失败: {str(e)}")
            raise
    
    async def _handle_sandbox_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理沙箱执行操作"""
        try:
            code = input_data.get("code")
            if not code:
                raise ValueError("code is required")
            
            language = input_data.get("language", "python")
            timeout = input_data.get("timeout", 10)
            resources = input_data.get("resources", {})
            context = input_data.get("context", {})
            
            result = await self.sandbox_executor.execute(
                code=code,
                language=language,
                timeout=timeout,
                resources=resources,
                context=context
            )
            return result
        except Exception as e:
            self.logger.error(f"处理沙箱执行操作失败: {str(e)}")
            raise
    
    async def _handle_api_gateway(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API网关操作"""
        try:
            api_operation = input_data.get("api_operation")
            if not api_operation:
                raise ValueError("api_operation is required")
            
            if api_operation == "register_api":
                api_config = input_data.get("api_config")
                if not api_config:
                    raise ValueError("api_config is required")
                return await self.api_gateway.register_api(api_config)
            elif api_operation == "unregister_api":
                api_id = input_data.get("api_id")
                if not api_id:
                    raise ValueError("api_id is required")
                return await self.api_gateway.unregister_api(api_id)
            elif api_operation == "call_api":
                api_id = input_data.get("api_id")
                if not api_id:
                    raise ValueError("api_id is required")
                params = input_data.get("params", {})
                headers = input_data.get("headers", {})
                return await self.api_gateway.call_api(api_id, params, headers)
            elif api_operation == "list_apis":
                return await self.api_gateway.list_apis()
            elif api_operation == "get_api_info":
                api_id = input_data.get("api_id")
                if not api_id:
                    raise ValueError("api_id is required")
                return await self.api_gateway.get_api_info(api_id)
            else:
                raise ValueError(f"unknown api operation: {api_operation}")
        except Exception as e:
            self.logger.error(f"处理API网关操作失败: {str(e)}")
            raise
    
    async def _handle_extension_point(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理扩展点操作"""
        try:
            ep_operation = input_data.get("ep_operation")
            if not ep_operation:
                raise ValueError("ep_operation is required")
            
            if ep_operation == "register_extension_point":
                ep_name = input_data.get("ep_name")
                if not ep_name:
                    raise ValueError("ep_name is required")
                ep_description = input_data.get("ep_description", "")
                return await self.extension_point_manager.register_extension_point(ep_name, ep_description)
            elif ep_operation == "list_extension_points":
                return await self.extension_point_manager.list_extension_points()
            elif ep_operation == "get_extension_point_info":
                ep_name = input_data.get("ep_name")
                if not ep_name:
                    raise ValueError("ep_name is required")
                return await self.extension_point_manager.get_extension_point_info(ep_name)
            elif ep_operation == "register_extension":
                ep_name = input_data.get("ep_name")
                extension_name = input_data.get("extension_name")
                extension_impl = input_data.get("extension_impl")
                if not ep_name or not extension_name or not extension_impl:
                    raise ValueError("ep_name, extension_name and extension_impl are required")
                return await self.extension_point_manager.register_extension(ep_name, extension_name, extension_impl)
            elif ep_operation == "list_extensions":
                ep_name = input_data.get("ep_name")
                if not ep_name:
                    raise ValueError("ep_name is required")
                return await self.extension_point_manager.list_extensions(ep_name)
            elif ep_operation == "execute_extensions":
                ep_name = input_data.get("ep_name")
                context = input_data.get("context", {})
                if not ep_name:
                    raise ValueError("ep_name is required")
                return await self.extension_point_manager.execute_extensions(ep_name, context)
            else:
                raise ValueError(f"unknown extension point operation: {ep_operation}")
        except Exception as e:
            self.logger.error(f"处理扩展点操作失败: {str(e)}")
            raise
    
    async def list_plugins(self) -> Dict[str, Any]:
        """列出所有插件"""
        try:
            return await self.plugin_manager.list_plugins()
        except Exception as e:
            self.logger.error(f"列出插件失败: {str(e)}")
            raise
    
    async def load_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """加载插件"""
        try:
            return await self.plugin_manager.load_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"加载插件失败: {str(e)}")
            raise
    
    async def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """卸载插件"""
        try:
            return await self.plugin_manager.unload_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"卸载插件失败: {str(e)}")
            raise
    
    async def execute_code(self, code: str, language: str = "python", timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行代码"""
        try:
            return await self.sandbox_executor.execute(
                code=code,
                language=language,
                timeout=timeout,
                resources=resources or {},
                context=context or {}
            )
        except Exception as e:
            self.logger.error(f"执行代码失败: {str(e)}")
            raise
    
    async def call_api(self, api_id: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用API"""
        try:
            return await self.api_gateway.call_api(api_id, params or {}, headers or {})
        except Exception as e:
            self.logger.error(f"调用API失败: {str(e)}")
            raise
    
    async def register_extension_point(self, ep_name: str, ep_description: str = "") -> Dict[str, Any]:
        """注册扩展点"""
        try:
            return await self.extension_point_manager.register_extension_point(ep_name, ep_description)
        except Exception as e:
            self.logger.error(f"注册扩展点失败: {str(e)}")
            raise
    
    async def register_extension(self, ep_name: str, extension_name: str, extension_impl: Any) -> Dict[str, Any]:
        """注册扩展"""
        try:
            return await self.extension_point_manager.register_extension(ep_name, extension_name, extension_impl)
        except Exception as e:
            self.logger.error(f"注册扩展失败: {str(e)}")
            raise
    
    async def execute_extensions(self, ep_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行扩展"""
        try:
            return await self.extension_point_manager.execute_extensions(ep_name, context or {})
        except Exception as e:
            self.logger.error(f"执行扩展失败: {str(e)}")
            raise
