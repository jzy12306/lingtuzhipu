import logging
from typing import Dict, Any, List, Optional, Callable
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class ExtensionPoint:
    """扩展点类"""
    
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.extensions: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"ExtensionPoint[{name}]")
    
    def get_info(self) -> Dict[str, Any]:
        """获取扩展点信息"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "extensions_count": len(self.extensions)
        }
    
    def register_extension(self, extension_name: str, extension_impl: Any) -> bool:
        """注册扩展"""
        try:
            # 检查扩展是否已存在
            for ext in self.extensions:
                if ext["name"] == extension_name:
                    self.logger.warning(f"扩展已存在: {extension_name}")
                    return False
            
            # 注册扩展
            extension = {
                "id": str(uuid.uuid4()),
                "name": extension_name,
                "implementation": extension_impl,
                "created_at": datetime.utcnow(),
                "enabled": True
            }
            self.extensions.append(extension)
            self.logger.info(f"扩展注册成功: {extension_name}")
            return True
        except Exception as e:
            self.logger.error(f"注册扩展失败: {str(e)}")
            return False
    
    def unregister_extension(self, extension_name: str) -> bool:
        """注销扩展"""
        try:
            # 查找扩展
            for i, ext in enumerate(self.extensions):
                if ext["name"] == extension_name:
                    del self.extensions[i]
                    self.logger.info(f"扩展注销成功: {extension_name}")
                    return True
            
            self.logger.warning(f"扩展未找到: {extension_name}")
            return False
        except Exception as e:
            self.logger.error(f"注销扩展失败: {str(e)}")
            return False
    
    def enable_extension(self, extension_name: str) -> bool:
        """启用扩展"""
        try:
            # 查找扩展
            for ext in self.extensions:
                if ext["name"] == extension_name:
                    ext["enabled"] = True
                    self.logger.info(f"扩展启用成功: {extension_name}")
                    return True
            
            self.logger.warning(f"扩展未找到: {extension_name}")
            return False
        except Exception as e:
            self.logger.error(f"启用扩展失败: {str(e)}")
            return False
    
    def disable_extension(self, extension_name: str) -> bool:
        """禁用扩展"""
        try:
            # 查找扩展
            for ext in self.extensions:
                if ext["name"] == extension_name:
                    ext["enabled"] = False
                    self.logger.info(f"扩展禁用成功: {extension_name}")
                    return True
            
            self.logger.warning(f"扩展未找到: {extension_name}")
            return False
        except Exception as e:
            self.logger.error(f"禁用扩展失败: {str(e)}")
            return False
    
    def get_extension(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """获取扩展"""
        for ext in self.extensions:
            if ext["name"] == extension_name:
                return ext
        return None
    
    def get_enabled_extensions(self) -> List[Dict[str, Any]]:
        """获取所有启用的扩展"""
        return [ext for ext in self.extensions if ext["enabled"]]


class ExtensionPointManager:
    """扩展点管理器"""
    
    def __init__(self):
        self.extension_points: Dict[str, ExtensionPoint] = {}
        self.logger = logger.getChild("ExtensionPointManager")
    
    async def initialize(self) -> bool:
        """初始化扩展点管理器"""
        try:
            self.logger.info("初始化扩展点管理器")
            
            # 注册默认扩展点
            await self._register_default_extension_points()
            
            self.logger.info("扩展点管理器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"初始化扩展点管理器失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭扩展点管理器"""
        try:
            self.logger.info("关闭扩展点管理器")
            
            # 清空扩展点列表
            self.extension_points.clear()
            
            self.logger.info("扩展点管理器关闭完成")
            return True
        except Exception as e:
            self.logger.error(f"关闭扩展点管理器失败: {str(e)}")
            return False
    
    async def _register_default_extension_points(self):
        """注册默认扩展点"""
        default_extension_points = [
            {
                "name": "knowledge_graph_entity_created",
                "description": "知识图谱实体创建时触发"
            },
            {
                "name": "knowledge_graph_relation_created",
                "description": "知识图谱关系创建时触发"
            },
            {
                "name": "document_processed",
                "description": "文档处理完成时触发"
            },
            {
                "name": "query_processed",
                "description": "查询处理完成时触发"
            },
            {
                "name": "agent_task_completed",
                "description": "智能体任务完成时触发"
            },
            {
                "name": "api_call_completed",
                "description": "API调用完成时触发"
            }
        ]
        
        for ep in default_extension_points:
            await self.register_extension_point(ep["name"], ep["description"])
    
    async def register_extension_point(self, ep_name: str, ep_description: str = "") -> Dict[str, Any]:
        """注册扩展点"""
        try:
            self.logger.info(f"注册扩展点: {ep_name}")
            
            # 检查扩展点是否已存在
            if ep_name in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点已存在: {ep_name}"
                }
            
            # 创建扩展点
            extension_point = ExtensionPoint(ep_name, ep_description)
            self.extension_points[ep_name] = extension_point
            
            self.logger.info(f"扩展点注册成功: {ep_name}")
            return {
                "success": True,
                "message": f"扩展点注册成功: {ep_name}",
                "extension_point": extension_point.get_info()
            }
        except Exception as e:
            self.logger.error(f"注册扩展点失败: {str(e)}")
            return {
                "success": False,
                "message": f"注册扩展点失败: {str(e)}"
            }
    
    async def unregister_extension_point(self, ep_name: str) -> Dict[str, Any]:
        """注销扩展点"""
        try:
            self.logger.info(f"注销扩展点: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 注销扩展点
            del self.extension_points[ep_name]
            
            self.logger.info(f"扩展点注销成功: {ep_name}")
            return {
                "success": True,
                "message": f"扩展点注销成功: {ep_name}"
            }
        except Exception as e:
            self.logger.error(f"注销扩展点失败: {str(e)}")
            return {
                "success": False,
                "message": f"注销扩展点失败: {str(e)}"
            }
    
    async def list_extension_points(self) -> Dict[str, Any]:
        """列出所有扩展点"""
        try:
            self.logger.info("列出所有扩展点")
            
            extension_points_info = []
            for extension_point in self.extension_points.values():
                extension_points_info.append(extension_point.get_info())
            
            return {
                "extension_points": extension_points_info,
                "total": len(extension_points_info)
            }
        except Exception as e:
            self.logger.error(f"列出扩展点失败: {str(e)}")
            raise
    
    async def get_extension_point_info(self, ep_name: str) -> Dict[str, Any]:
        """获取扩展点信息"""
        try:
            self.logger.info(f"获取扩展点信息: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            extension_point = self.extension_points[ep_name]
            return {
                "success": True,
                "extension_point": extension_point.get_info()
            }
        except Exception as e:
            self.logger.error(f"获取扩展点信息失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取扩展点信息失败: {str(e)}"
            }
    
    async def register_extension(self, ep_name: str, extension_name: str, extension_impl: Any) -> Dict[str, Any]:
        """注册扩展"""
        try:
            self.logger.info(f"注册扩展到扩展点: {ep_name}, 扩展名称: {extension_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 注册扩展
            extension_point = self.extension_points[ep_name]
            if extension_point.register_extension(extension_name, extension_impl):
                return {
                    "success": True,
                    "message": f"扩展注册成功: {extension_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"扩展注册失败: {extension_name}"
                }
        except Exception as e:
            self.logger.error(f"注册扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"注册扩展失败: {str(e)}"
            }
    
    async def unregister_extension(self, ep_name: str, extension_name: str) -> Dict[str, Any]:
        """注销扩展"""
        try:
            self.logger.info(f"注销扩展: {extension_name}, 扩展点: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 注销扩展
            extension_point = self.extension_points[ep_name]
            if extension_point.unregister_extension(extension_name):
                return {
                    "success": True,
                    "message": f"扩展注销成功: {extension_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"扩展注销失败: {extension_name}"
                }
        except Exception as e:
            self.logger.error(f"注销扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"注销扩展失败: {str(e)}"
            }
    
    async def list_extensions(self, ep_name: str) -> Dict[str, Any]:
        """列出扩展点的所有扩展"""
        try:
            self.logger.info(f"列出扩展点的所有扩展: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 获取扩展点
            extension_point = self.extension_points[ep_name]
            extensions = extension_point.extensions
            
            # 转换扩展信息
            extensions_info = []
            for ext in extensions:
                extensions_info.append({
                    "id": ext["id"],
                    "name": ext["name"],
                    "enabled": ext["enabled"],
                    "created_at": ext["created_at"]
                })
            
            return {
                "success": True,
                "extensions": extensions_info,
                "total": len(extensions_info)
            }
        except Exception as e:
            self.logger.error(f"列出扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"列出扩展失败: {str(e)}"
            }
    
    async def execute_extensions(self, ep_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行扩展点的所有扩展"""
        try:
            self.logger.info(f"执行扩展点的所有扩展: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 获取扩展点
            extension_point = self.extension_points[ep_name]
            enabled_extensions = extension_point.get_enabled_extensions()
            
            # 执行所有启用的扩展
            results = []
            for ext in enabled_extensions:
                try:
                    self.logger.info(f"执行扩展: {ext['name']}")
                    
                    # 执行扩展
                    if callable(ext["implementation"]):
                        result = ext["implementation"](context or {})
                        results.append({
                            "extension_name": ext["name"],
                            "success": True,
                            "result": result
                        })
                    else:
                        results.append({
                            "extension_name": ext["name"],
                            "success": False,
                            "error": "扩展实现不是可调用对象"
                        })
                except Exception as e:
                    self.logger.error(f"执行扩展失败: {ext['name']}, 错误: {str(e)}")
                    results.append({
                        "extension_name": ext["name"],
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "results": results,
                "total_executed": len(results),
                "extension_point": ep_name
            }
        except Exception as e:
            self.logger.error(f"执行扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行扩展失败: {str(e)}"
            }
    
    async def enable_extension(self, ep_name: str, extension_name: str) -> Dict[str, Any]:
        """启用扩展"""
        try:
            self.logger.info(f"启用扩展: {extension_name}, 扩展点: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 启用扩展
            extension_point = self.extension_points[ep_name]
            if extension_point.enable_extension(extension_name):
                return {
                    "success": True,
                    "message": f"扩展启用成功: {extension_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"扩展启用失败: {extension_name}"
                }
        except Exception as e:
            self.logger.error(f"启用扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"启用扩展失败: {str(e)}"
            }
    
    async def disable_extension(self, ep_name: str, extension_name: str) -> Dict[str, Any]:
        """禁用扩展"""
        try:
            self.logger.info(f"禁用扩展: {extension_name}, 扩展点: {ep_name}")
            
            # 检查扩展点是否存在
            if ep_name not in self.extension_points:
                return {
                    "success": False,
                    "message": f"扩展点不存在: {ep_name}"
                }
            
            # 禁用扩展
            extension_point = self.extension_points[ep_name]
            if extension_point.disable_extension(extension_name):
                return {
                    "success": True,
                    "message": f"扩展禁用成功: {extension_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"扩展禁用失败: {extension_name}"
                }
        except Exception as e:
            self.logger.error(f"禁用扩展失败: {str(e)}")
            return {
                "success": False,
                "message": f"禁用扩展失败: {str(e)}"
            }
    
    def get_extension_point(self, ep_name: str) -> Optional[ExtensionPoint]:
        """根据名称获取扩展点"""
        return self.extension_points.get(ep_name)
    
    def get_all_extension_points(self) -> List[ExtensionPoint]:
        """获取所有扩展点"""
        return list(self.extension_points.values())
