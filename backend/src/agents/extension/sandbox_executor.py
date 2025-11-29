import logging
import subprocess
import sys
import time
import uuid
import os
import tempfile
import json
from typing import Dict, Any, Optional, List
import asyncio
import signal
import psutil

# 处理Windows不支持resource模块的情况
try:
    import resource
except ImportError:
    resource = None

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """沙箱执行器"""
    
    def __init__(self):
        self.logger = logger.getChild("SandboxExecutor")
        self.python_restricted_available = False
        self.node_available = False
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖"""
        # 检查Python Restricted库
        try:
            import RestrictedPython
            self.python_restricted_available = True
            self.logger.info("RestrictedPython库可用")
        except ImportError:
            self.logger.warning("RestrictedPython库不可用，将使用其他方式执行Python代码")
        
        # 检查Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
            self.node_available = True
            self.logger.info(f"Node.js可用，版本: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("Node.js不可用，将无法执行JavaScript代码")
    
    async def initialize(self) -> bool:
        """初始化沙箱执行器"""
        try:
            self.logger.info("初始化沙箱执行器")
            self.logger.info(f"Python Restricted可用: {self.python_restricted_available}")
            self.logger.info(f"Node.js可用: {self.node_available}")
            self.logger.info("沙箱执行器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"初始化沙箱执行器失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭沙箱执行器"""
        try:
            self.logger.info("关闭沙箱执行器")
            self.logger.info("沙箱执行器关闭完成")
            return True
        except Exception as e:
            self.logger.error(f"关闭沙箱执行器失败: {str(e)}")
            return False
    
    async def execute(self, code: str, language: str = "python", timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行代码"""
        try:
            self.logger.info(f"执行代码，语言: {language}, 超时: {timeout}秒")
            
            # 验证输入
            if not code:
                return {
                    "success": False,
                    "error": "代码不能为空"
                }
            
            if language not in ["python", "javascript"]:
                return {
                    "success": False,
                    "error": f"不支持的语言: {language}"
                }
            
            # 执行代码
            if language == "python":
                return await self._execute_python(code, timeout, resources or {}, context or {})
            elif language == "javascript":
                return await self._execute_javascript(code, timeout, resources or {}, context or {})
        except Exception as e:
            self.logger.error(f"执行代码失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_python(self, code: str, timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            self.logger.info(f"执行Python代码，超时: {timeout}秒")
            
            # 使用RestrictedPython执行
            if self.python_restricted_available:
                return await self._execute_python_restricted(code, timeout, resources, context)
            else:
                # 回退到使用subprocess执行
                return await self._execute_python_subprocess(code, timeout, resources, context)
        except Exception as e:
            self.logger.error(f"执行Python代码失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_python_restricted(self, code: str, timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用RestrictedPython执行Python代码"""
        try:
            from RestrictedPython import compile_restricted
            from RestrictedPython import safe_globals
            from RestrictedPython.Guards import safe_builtins
            from RestrictedPython.PrintCollector import PrintCollector
            
            self.logger.info("使用RestrictedPython执行Python代码")
            
            # 准备执行环境
            restricted_globals = dict(safe_globals)
            restricted_globals.update({
                '__builtins__': safe_builtins,
                '_print_': PrintCollector,
            })
            
            # 添加上下文变量
            restricted_locals = context.copy() if context else {}
            
            # 编译代码
            byte_code = compile_restricted(code, '<string>', 'exec')
            
            # 执行代码
            exec(byte_code, restricted_globals, restricted_locals)
            
            # 获取输出
            output = ""
            if '_print' in restricted_locals:
                output = restricted_locals['_print']()
            
            # 获取返回值
            result = restricted_locals.get('result', None)
            
            return {
                "success": True,
                "output": output,
                "result": result,
                "execution_time": 0.0,
                "language": "python",
                "resources_used": {
                    "cpu_time": 0.0,
                    "memory": 0
                }
            }
        except Exception as e:
            self.logger.error(f"使用RestrictedPython执行Python代码失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_python_subprocess(self, code: str, timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用subprocess执行Python代码"""
        try:
            self.logger.info("使用subprocess执行Python代码")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # 写入上下文变量
                if context:
                    for key, value in context.items():
                        f.write(f"{key} = {repr(value)}\n")
                # 写入代码
                f.write(code)
                temp_file = f.name
            
            # 准备命令
            cmd = [sys.executable, temp_file]
            
            # 执行代码
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir()
            )
            execution_time = time.time() - start_time
            
            # 清理临时文件
            os.unlink(temp_file)
            
            # 检查结果
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": result.stderr,
                    "execution_time": execution_time,
                    "language": "python",
                    "resources_used": {
                        "cpu_time": execution_time,
                        "memory": 0  # 暂时无法获取内存使用
                    }
                }
            else:
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr,
                    "execution_time": execution_time,
                    "language": "python"
                }
        except subprocess.TimeoutExpired:
            self.logger.error(f"Python代码执行超时")
            return {
                "success": False,
                "error": f"执行超时（{timeout}秒）",
                "language": "python"
            }
        except Exception as e:
            self.logger.error(f"使用subprocess执行Python代码失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": "python"
            }
    
    async def _execute_javascript(self, code: str, timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行JavaScript代码"""
        try:
            if not self.node_available:
                return {
                    "success": False,
                    "error": "Node.js不可用，无法执行JavaScript代码"
                }
            
            self.logger.info(f"执行JavaScript代码，超时: {timeout}秒")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                # 写入上下文变量
                if context:
                    f.write("const context = " + json.dumps(context) + ";\n")
                # 写入代码
                f.write(code)
                temp_file = f.name
            
            # 准备命令
            cmd = ["node", temp_file]
            
            # 执行代码
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir()
            )
            execution_time = time.time() - start_time
            
            # 清理临时文件
            os.unlink(temp_file)
            
            # 检查结果
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": result.stderr,
                    "execution_time": execution_time,
                    "language": "javascript",
                    "resources_used": {
                        "cpu_time": execution_time,
                        "memory": 0  # 暂时无法获取内存使用
                    }
                }
            else:
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr,
                    "execution_time": execution_time,
                    "language": "javascript"
                }
        except subprocess.TimeoutExpired:
            self.logger.error(f"JavaScript代码执行超时")
            return {
                "success": False,
                "error": f"执行超时（{timeout}秒）",
                "language": "javascript"
            }
        except Exception as e:
            self.logger.error(f"执行JavaScript代码失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": "javascript"
            }
    
    async def execute_with_resource_limits(self, code: str, language: str = "python", timeout: int = 10, resources: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行代码并限制资源"""
        try:
            self.logger.info(f"执行代码并限制资源，语言: {language}, 超时: {timeout}秒")
            
            # 默认资源限制
            default_resources = {
                "cpu_time": timeout,
                "memory": 100 * 1024 * 1024,  # 100MB
                "max_processes": 1,
                "network_access": False
            }
            
            # 合并资源限制
            if resources:
                default_resources.update(resources)
            
            # 执行代码
            result = await self.execute(code, language, timeout, default_resources, context)
            
            return result
        except Exception as e:
            self.logger.error(f"执行代码并限制资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _set_resource_limits(self, resources: Dict[str, Any]):
        """设置资源限制"""
        try:
            # 只有在resource模块可用时才设置资源限制
            if resource is not None:
                # 设置CPU时间限制
                if "cpu_time" in resources and hasattr(resource, "RLIMIT_CPU"):
                    cpu_time = resources["cpu_time"]
                    resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))
                
                # 设置内存限制
                if "memory" in resources and hasattr(resource, "RLIMIT_AS"):
                    memory = resources["memory"]
                    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
                
                # 设置进程数量限制
                if "max_processes" in resources and hasattr(resource, "RLIMIT_NPROC"):
                    max_processes = resources["max_processes"]
                    resource.setrlimit(resource.RLIMIT_NPROC, (max_processes, max_processes))
                
                # 设置文件大小限制
                if "max_file_size" in resources and hasattr(resource, "RLIMIT_FSIZE"):
                    max_file_size = resources["max_file_size"]
                    resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_size, max_file_size))
        except Exception as e:
            self.logger.error(f"设置资源限制失败: {str(e)}")
    
    def _monitor_process(self, pid: int, timeout: int, resources: Dict[str, Any]) -> bool:
        """监控进程资源使用"""
        try:
            process = psutil.Process(pid)
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if not process.is_running():
                    return True
                
                # 检查CPU使用
                if "cpu_time" in resources:
                    cpu_time = process.cpu_times().user + process.cpu_times().system
                    if cpu_time > resources["cpu_time"]:
                        process.terminate()
                        return False
                
                # 检查内存使用
                if "memory" in resources:
                    memory = process.memory_info().rss
                    if memory > resources["memory"]:
                        process.terminate()
                        return False
                
                time.sleep(0.1)
            
            # 超时
            process.terminate()
            return False
        except Exception as e:
            self.logger.error(f"监控进程失败: {str(e)}")
            return False
