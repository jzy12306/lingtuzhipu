import logging
import importlib.util
import os
import sys
import pkgutil
from typing import Dict, Any, List, Optional
import uuid
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class Plugin:
    """插件类"""
    
    def __init__(self, name: str, module: Any, path: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.module = module
        self.path = path
        self.version = getattr(module, "__version__", "1.0.0")
        self.description = getattr(module, "__description__", "")
        self.author = getattr(module, "__author__", "unknown")
        self.status = "loaded"
        self.enabled = True
        self.dependencies = getattr(module, "__dependencies__", [])
        self.dependencies_satisfied = True  # 依赖是否满足
        self.extensions = getattr(module, "__extensions__", [])
        self.entry_points = getattr(module, "__entry_points__", {})
        self.logger = logging.getLogger(f"Plugin[{name}]")
        self.installed_time = datetime.now()
        self.last_updated = datetime.now()
        self.security_check_passed = True  # 安全性检查是否通过
        self.update_available = False  # 是否有更新可用
        self.latest_version = self.version  # 最新版本
        self.checksum = None  # 插件文件校验和
        self.license = getattr(module, "__license__", "MIT")  # 插件许可证
        self.homepage = getattr(module, "__homepage__", "")  # 插件主页
        self.repository = getattr(module, "__repository__", "")  # 插件仓库
        self.keywords = getattr(module, "__keywords__", [])  # 插件关键词
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            if hasattr(self.module, "initialize"):
                return await self.module.initialize()
            return True
        except Exception as e:
            self.logger.error(f"初始化插件失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭插件"""
        try:
            if hasattr(self.module, "shutdown"):
                return await self.module.shutdown()
            return True
        except Exception as e:
            self.logger.error(f"关闭插件失败: {str(e)}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "status": self.status,
            "enabled": self.enabled,
            "dependencies": self.dependencies,
            "dependencies_satisfied": self.dependencies_satisfied,
            "extensions": self.extensions,
            "entry_points": self.entry_points,
            "path": self.path,
            "installed_time": self.installed_time.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "security_check_passed": self.security_check_passed,
            "update_available": self.update_available,
            "latest_version": self.latest_version,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "keywords": self.keywords
        }


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_paths: List[str] = []
        self.logger = logger.getChild("PluginManager")
        self.dependency_graph = {}  # 依赖图
        self.update_check_interval = 3600  # 更新检查间隔（秒）
        self.last_update_check = datetime.now()  # 上次更新检查时间
    
    async def initialize(self) -> bool:
        """初始化插件管理器"""
        try:
            self.logger.info("初始化插件管理器")
            
            # 注册默认插件路径
            self._register_default_plugin_paths()
            
            # 加载所有插件
            await self._load_all_plugins()
            
            self.logger.info("插件管理器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"初始化插件管理器失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭插件管理器"""
        try:
            self.logger.info("关闭插件管理器")
            
            # 关闭所有插件
            for plugin in self.plugins.values():
                await plugin.shutdown()
            
            # 清空插件列表
            self.plugins.clear()
            
            self.logger.info("插件管理器关闭完成")
            return True
        except Exception as e:
            self.logger.error(f"关闭插件管理器失败: {str(e)}")
            return False
    
    def _register_default_plugin_paths(self):
        """注册默认插件路径"""
        # 注册内置插件路径
        builtin_plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
        self.plugin_paths.append(builtin_plugins_path)
        
        # 注册外部插件路径
        external_plugins_path = os.path.join(os.getcwd(), "plugins")
        if os.path.exists(external_plugins_path):
            self.plugin_paths.append(external_plugins_path)
        
        # 注册环境变量指定的插件路径
        env_plugins_path = os.environ.get("PLUGINS_PATH")
        if env_plugins_path:
            for path in env_plugins_path.split(","):
                if os.path.exists(path):
                    self.plugin_paths.append(path)
        
        self.logger.info(f"注册的插件路径: {self.plugin_paths}")
    
    async def _load_all_plugins(self):
        """加载所有插件"""
        self.logger.info("开始加载所有插件")
        
        # 遍历所有插件路径
        for plugin_path in self.plugin_paths:
            await self._load_plugins_from_path(plugin_path)
        
        # 解析插件依赖关系
        await self._resolve_dependencies()
        
        self.logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")
    
    async def _load_plugins_from_path(self, plugin_path: str):
        """从指定路径加载插件"""
        self.logger.info(f"从路径加载插件: {plugin_path}")
        
        # 确保路径存在
        if not os.path.exists(plugin_path):
            self.logger.warning(f"插件路径不存在: {plugin_path}")
            return
        
        # 添加路径到sys.path
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)
        
        # 遍历路径下的所有Python文件和目录
        for root, dirs, files in os.walk(plugin_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    # 加载单个Python文件作为插件
                    await self._load_plugin_from_file(os.path.join(root, file))
            
            for dir in dirs:
                # 加载目录作为插件包
                await self._load_plugin_from_package(os.path.join(root, dir))
    
    async def _check_plugin_dependencies(self, plugin: Plugin) -> bool:
        """检查插件依赖"""
        try:
            self.logger.info(f"检查插件依赖: {plugin.name}")
            
            # 简单的依赖检查：检查依赖插件是否已加载
            for dependency in plugin.dependencies:
                # 解析依赖格式：plugin_name>=version
                if ">=" in dependency:
                    dep_name, dep_version = dependency.split(">=", 1)
                else:
                    dep_name = dependency
                    dep_version = None
                
                # 检查依赖插件是否已加载
                if dep_name not in self.plugins:
                    self.logger.warning(f"插件 {plugin.name} 的依赖 {dep_name} 未加载")
                    plugin.dependencies_satisfied = False
                    return False
                
                # 检查依赖版本
                if dep_version:
                    dep_plugin = self.plugins[dep_name]
                    if dep_plugin.version < dep_version:
                        self.logger.warning(f"插件 {plugin.name} 的依赖 {dep_name} 版本不满足要求")
                        plugin.dependencies_satisfied = False
                        return False
            
            plugin.dependencies_satisfied = True
            return True
        except Exception as e:
            self.logger.error(f"检查插件依赖失败: {str(e)}")
            plugin.dependencies_satisfied = False
            return False
    
    async def _check_plugin_security(self, plugin: Plugin) -> bool:
        """检查插件安全性"""
        try:
            self.logger.info(f"检查插件安全性: {plugin.name}")
            
            # 简单的安全性检查：检查插件是否包含危险操作
            # 1. 检查是否导入了危险模块
            dangerous_modules = ["os", "sys", "subprocess", "shutil", "socket", "pickle"]
            for module_name in dangerous_modules:
                if module_name in sys.modules and hasattr(plugin.module, module_name):
                    self.logger.warning(f"插件 {plugin.name} 导入了危险模块: {module_name}")
                    # 不阻止加载，但标记为安全性检查未通过
                    plugin.security_check_passed = False
            
            # 2. 检查是否有危险属性
            dangerous_attrs = ["exec", "eval", "__import__", "open", "write", "remove"]
            for attr_name in dangerous_attrs:
                if hasattr(plugin.module, attr_name):
                    self.logger.warning(f"插件 {plugin.name} 包含危险属性: {attr_name}")
                    plugin.security_check_passed = False
            
            return plugin.security_check_passed
        except Exception as e:
            self.logger.error(f"检查插件安全性失败: {str(e)}")
            plugin.security_check_passed = False
            return False
    
    async def _resolve_dependencies(self) -> bool:
        """解析插件依赖关系"""
        try:
            self.logger.info("解析插件依赖关系")
            
            # 构建依赖图
            self.dependency_graph = {}
            for plugin_name, plugin in self.plugins.items():
                self.dependency_graph[plugin_name] = plugin.dependencies
            
            # 简单的依赖解析：检查每个插件的依赖是否都已加载
            for plugin_name, plugin in self.plugins.items():
                await self._check_plugin_dependencies(plugin)
            
            return True
        except Exception as e:
            self.logger.error(f"解析插件依赖关系失败: {str(e)}")
            return False
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """检查插件更新"""
        try:
            self.logger.info("检查插件更新")
            
            # 检查是否需要更新检查
            if (datetime.now() - self.last_update_check).total_seconds() < self.update_check_interval:
                self.logger.info("更新检查间隔未到，跳过检查")
                return {
                    "success": True,
                    "message": "更新检查间隔未到，跳过检查",
                    "updates_available": 0
                }
            
            # 简单的更新检查：检查插件版本
            updates_available = 0
            for plugin in self.plugins.values():
                # 这里可以添加实际的更新检查逻辑，比如从插件仓库获取最新版本
                # 目前只是模拟检查
                plugin.update_available = False
                plugin.latest_version = plugin.version
            
            self.last_update_check = datetime.now()
            
            return {
                "success": True,
                "message": "更新检查完成",
                "updates_available": updates_available
            }
        except Exception as e:
            self.logger.error(f"检查插件更新失败: {str(e)}")
            return {
                "success": False,
                "message": f"检查插件更新失败: {str(e)}",
                "updates_available": 0
            }
    
    async def _update_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """更新插件"""
        try:
            self.logger.info(f"更新插件: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                return {
                    "success": False,
                    "message": f"插件未加载: {plugin_name}"
                }
            
            plugin = self.plugins[plugin_name]
            
            # 检查是否有更新可用
            if not plugin.update_available:
                return {
                    "success": False,
                    "message": f"插件 {plugin_name} 没有可用更新"
                }
            
            # 这里可以添加实际的更新逻辑，比如从插件仓库下载最新版本
            # 目前只是模拟更新
            plugin.version = plugin.latest_version
            plugin.update_available = False
            plugin.last_updated = datetime.now()
            
            return {
                "success": True,
                "message": f"插件 {plugin_name} 更新成功",
                "plugin": plugin.get_info()
            }
        except Exception as e:
            self.logger.error(f"更新插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新插件失败: {str(e)}"
            }
    
    async def _load_plugin_from_file(self, file_path: str):
        """从文件加载插件"""
        try:
            self.logger.info(f"从文件加载插件: {file_path}")
            
            # 获取插件名称
            plugin_name = os.path.basename(file_path).replace(".py", "")
            
            # 检查插件是否已加载
            if plugin_name in self.plugins:
                self.logger.warning(f"插件已加载: {plugin_name}")
                return
            
            # 加载模块
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            if spec is None:
                self.logger.error(f"无法加载插件规范: {file_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # 创建插件实例
            plugin = Plugin(plugin_name, module, file_path)
            
            # 检查插件安全性
            await self._check_plugin_security(plugin)
            
            # 初始化插件
            if await plugin.initialize():
                self.plugins[plugin_name] = plugin
                self.logger.info(f"插件加载成功: {plugin_name}")
            else:
                self.logger.error(f"插件初始化失败: {plugin_name}")
        except Exception as e:
            self.logger.error(f"从文件加载插件失败: {str(e)}")
    
    async def _load_plugin_from_package(self, package_path: str):
        """从包加载插件"""
        try:
            self.logger.info(f"从包加载插件: {package_path}")
            
            # 获取插件名称
            plugin_name = os.path.basename(package_path)
            
            # 检查插件是否已加载
            if plugin_name in self.plugins:
                self.logger.warning(f"插件已加载: {plugin_name}")
                return
            
            # 检查是否是有效的Python包
            if not os.path.exists(os.path.join(package_path, "__init__.py")):
                self.logger.warning(f"不是有效的Python包: {package_path}")
                return
            
            # 加载模块
            spec = importlib.util.spec_from_file_location(
                plugin_name, 
                os.path.join(package_path, "__init__.py")
            )
            if spec is None:
                self.logger.error(f"无法加载插件规范: {package_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # 创建插件实例
            plugin = Plugin(plugin_name, module, package_path)
            
            # 检查插件安全性
            await self._check_plugin_security(plugin)
            
            # 初始化插件
            if await plugin.initialize():
                self.plugins[plugin_name] = plugin
                self.logger.info(f"插件加载成功: {plugin_name}")
            else:
                self.logger.error(f"插件初始化失败: {plugin_name}")
        except Exception as e:
            self.logger.error(f"从包加载插件失败: {str(e)}")
    
    async def list_plugins(self) -> Dict[str, Any]:
        """列出所有插件"""
        try:
            plugins_info = []
            for plugin in self.plugins.values():
                plugins_info.append(plugin.get_info())
            
            return {
                "plugins": plugins_info,
                "total": len(plugins_info)
            }
        except Exception as e:
            self.logger.error(f"列出插件失败: {str(e)}")
            raise
    
    async def load_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """加载指定插件"""
        try:
            self.logger.info(f"加载插件: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name in self.plugins:
                return {
                    "success": True,
                    "message": f"插件已加载: {plugin_name}",
                    "plugin": self.plugins[plugin_name].get_info()
                }
            
            # 搜索插件
            for plugin_path in self.plugin_paths:
                # 检查文件插件
                plugin_file = os.path.join(plugin_path, f"{plugin_name}.py")
                if os.path.exists(plugin_file):
                    await self._load_plugin_from_file(plugin_file)
                    if plugin_name in self.plugins:
                        return {
                            "success": True,
                            "message": f"插件加载成功: {plugin_name}",
                            "plugin": self.plugins[plugin_name].get_info()
                        }
                
                # 检查包插件
                plugin_package = os.path.join(plugin_path, plugin_name)
                if os.path.exists(plugin_package):
                    await self._load_plugin_from_package(plugin_package)
                    if plugin_name in self.plugins:
                        return {
                            "success": True,
                            "message": f"插件加载成功: {plugin_name}",
                            "plugin": self.plugins[plugin_name].get_info()
                        }
            
            return {
                "success": False,
                "message": f"找不到插件: {plugin_name}"
            }
        except Exception as e:
            self.logger.error(f"加载插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"加载插件失败: {str(e)}"
            }
    
    async def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """卸载指定插件"""
        try:
            self.logger.info(f"卸载插件: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                return {
                    "success": False,
                    "message": f"插件未加载: {plugin_name}"
                }
            
            # 关闭插件
            plugin = self.plugins[plugin_name]
            await plugin.shutdown()
            
            # 从sys.modules中移除
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            # 从插件列表中移除
            del self.plugins[plugin_name]
            
            return {
                "success": True,
                "message": f"插件卸载成功: {plugin_name}"
            }
        except Exception as e:
            self.logger.error(f"卸载插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"卸载插件失败: {str(e)}"
            }
    
    async def enable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """启用指定插件"""
        try:
            self.logger.info(f"启用插件: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                return {
                    "success": False,
                    "message": f"插件未加载: {plugin_name}"
                }
            
            # 启用插件
            plugin = self.plugins[plugin_name]
            plugin.enabled = True
            
            return {
                "success": True,
                "message": f"插件启用成功: {plugin_name}",
                "plugin": plugin.get_info()
            }
        except Exception as e:
            self.logger.error(f"启用插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"启用插件失败: {str(e)}"
            }
    
    async def disable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """禁用指定插件"""
        try:
            self.logger.info(f"禁用插件: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                return {
                    "success": False,
                    "message": f"插件未加载: {plugin_name}"
                }
            
            # 禁用插件
            plugin = self.plugins[plugin_name]
            plugin.enabled = False
            
            return {
                "success": True,
                "message": f"插件禁用成功: {plugin_name}",
                "plugin": plugin.get_info()
            }
        except Exception as e:
            self.logger.error(f"禁用插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"禁用插件失败: {str(e)}"
            }
    
    async def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件信息"""
        try:
            self.logger.info(f"获取插件信息: {plugin_name}")
            
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                return {
                    "success": False,
                    "message": f"插件未加载: {plugin_name}"
                }
            
            plugin = self.plugins[plugin_name]
            return {
                "success": True,
                "plugin": plugin.get_info()
            }
        except Exception as e:
            self.logger.error(f"获取插件信息失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取插件信息失败: {str(e)}"
            }
    
    async def check_plugin_updates(self) -> Dict[str, Any]:
        """检查插件更新"""
        try:
            return await self.check_for_updates()
        except Exception as e:
            self.logger.error(f"检查插件更新失败: {str(e)}")
            return {
                "success": False,
                "message": f"检查插件更新失败: {str(e)}"
            }
    
    async def update_plugin_by_name(self, plugin_name: str) -> Dict[str, Any]:
        """根据名称更新插件"""
        try:
            return await self._update_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"更新插件失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新插件失败: {str(e)}"
            }
    
    async def get_dependency_graph(self) -> Dict[str, Any]:
        """获取依赖图"""
        try:
            return {
                "success": True,
                "dependency_graph": self.dependency_graph
            }
        except Exception as e:
            self.logger.error(f"获取依赖图失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取依赖图失败: {str(e)}"
            }
    
    def get_plugin_by_name(self, plugin_name: str) -> Optional[Plugin]:
        """根据名称获取插件"""
        return self.plugins.get(plugin_name)
    
    def get_plugin_by_id(self, plugin_id: str) -> Optional[Plugin]:
        """根据ID获取插件"""
        for plugin in self.plugins.values():
            if plugin.id == plugin_id:
                return plugin
        return None
    
    def get_enabled_plugins(self) -> List[Plugin]:
        """获取所有启用的插件"""
        return [plugin for plugin in self.plugins.values() if plugin.enabled]
    
    def get_extensions(self, extension_point: str) -> List[Dict[str, Any]]:
        """获取指定扩展点的所有扩展"""
        extensions = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                for extension in plugin.extensions:
                    if extension.get("point") == extension_point:
                        extensions.append({
                            "plugin": plugin.name,
                            "extension": extension
                        })
        return extensions
    
    def get_entry_points(self, entry_point: str) -> List[Any]:
        """获取指定入口点的所有实现"""
        entry_points = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                if entry_point in plugin.entry_points:
                    entry_points.append(plugin.entry_points[entry_point])
        return entry_points
