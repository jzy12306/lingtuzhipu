import logging
import requests
import uuid
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class APIConfig:
    """API配置类"""
    
    def __init__(self, api_id: str, name: str, url: str, method: str = "GET", headers: Dict[str, Any] = None, auth: Dict[str, Any] = None, timeout: int = 10, cache_ttl: int = 0, rate_limit: int = 0, description: str = ""):
        self.id = api_id
        self.name = name
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.auth = auth or {}
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.rate_limit = rate_limit
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.enabled = True
        self.stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "avg_response_time": 0.0,
            "last_call": None
        }
    
    def get_info(self) -> Dict[str, Any]:
        """获取API配置信息"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "auth": {"type": self.auth.get("type", "none")} if self.auth else {},
            "timeout": self.timeout,
            "cache_ttl": self.cache_ttl,
            "rate_limit": self.rate_limit,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": self.enabled,
            "stats": self.stats
        }
    
    def update_stats(self, success: bool, response_time: float):
        """更新API统计信息"""
        self.stats["total_calls"] += 1
        if success:
            self.stats["success_calls"] += 1
        else:
            self.stats["failed_calls"] += 1
        
        # 更新平均响应时间
        if self.stats["total_calls"] == 1:
            self.stats["avg_response_time"] = response_time
        else:
            self.stats["avg_response_time"] = (
                self.stats["avg_response_time"] * (self.stats["total_calls"] - 1) + response_time
            ) / self.stats["total_calls"]
        
        self.stats["last_call"] = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class APIGateway:
    """API网关"""
    
    def __init__(self):
        self.apis: Dict[str, APIConfig] = {}
        self.cache: Dict[str, Any] = {}
        self.rate_limits: Dict[str, List[float]] = {}
        self.logger = logger.getChild("APIGateway")
    
    async def initialize(self) -> bool:
        """初始化API网关"""
        try:
            self.logger.info("初始化API网关")
            self.logger.info("API网关初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"初始化API网关失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭API网关"""
        try:
            self.logger.info("关闭API网关")
            # 清空API列表
            self.apis.clear()
            # 清空缓存
            self.cache.clear()
            # 清空限流记录
            self.rate_limits.clear()
            self.logger.info("API网关关闭完成")
            return True
        except Exception as e:
            self.logger.error(f"关闭API网关失败: {str(e)}")
            return False
    
    async def register_api(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """注册API"""
        try:
            self.logger.info(f"注册API: {api_config.get('name')}")
            
            # 验证API配置
            if "name" not in api_config or "url" not in api_config:
                return {
                    "success": False,
                    "message": "API名称和URL是必填项"
                }
            
            # 生成API ID
            api_id = api_config.get("id", str(uuid.uuid4()))
            
            # 检查API是否已存在
            if api_id in self.apis:
                return {
                    "success": False,
                    "message": f"API已存在: {api_id}"
                }
            
            # 创建API配置
            api = APIConfig(
                api_id=api_id,
                name=api_config["name"],
                url=api_config["url"],
                method=api_config.get("method", "GET"),
                headers=api_config.get("headers", {}),
                auth=api_config.get("auth", {}),
                timeout=api_config.get("timeout", 10),
                cache_ttl=api_config.get("cache_ttl", 0),
                rate_limit=api_config.get("rate_limit", 0),
                description=api_config.get("description", "")
            )
            
            # 添加到API列表
            self.apis[api_id] = api
            
            self.logger.info(f"API注册成功: {api_id}")
            return {
                "success": True,
                "message": f"API注册成功: {api_id}",
                "api": api.get_info()
            }
        except Exception as e:
            self.logger.error(f"注册API失败: {str(e)}")
            return {
                "success": False,
                "message": f"注册API失败: {str(e)}"
            }
    
    async def unregister_api(self, api_id: str) -> Dict[str, Any]:
        """注销API"""
        try:
            self.logger.info(f"注销API: {api_id}")
            
            # 检查API是否存在
            if api_id not in self.apis:
                return {
                    "success": False,
                    "message": f"API不存在: {api_id}"
                }
            
            # 删除API
            del self.apis[api_id]
            
            self.logger.info(f"API注销成功: {api_id}")
            return {
                "success": True,
                "message": f"API注销成功: {api_id}"
            }
        except Exception as e:
            self.logger.error(f"注销API失败: {str(e)}")
            return {
                "success": False,
                "message": f"注销API失败: {str(e)}"
            }
    
    async def update_api(self, api_id: str, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新API配置"""
        try:
            self.logger.info(f"更新API: {api_id}")
            
            # 检查API是否存在
            if api_id not in self.apis:
                return {
                    "success": False,
                    "message": f"API不存在: {api_id}"
                }
            
            # 获取API配置
            api = self.apis[api_id]
            
            # 更新API配置
            if "name" in api_config:
                api.name = api_config["name"]
            if "url" in api_config:
                api.url = api_config["url"]
            if "method" in api_config:
                api.method = api_config["method"]
            if "headers" in api_config:
                api.headers = api_config["headers"]
            if "auth" in api_config:
                api.auth = api_config["auth"]
            if "timeout" in api_config:
                api.timeout = api_config["timeout"]
            if "cache_ttl" in api_config:
                api.cache_ttl = api_config["cache_ttl"]
            if "rate_limit" in api_config:
                api.rate_limit = api_config["rate_limit"]
            if "description" in api_config:
                api.description = api_config["description"]
            if "enabled" in api_config:
                api.enabled = api_config["enabled"]
            
            # 更新时间
            api.updated_at = datetime.utcnow()
            
            self.logger.info(f"API更新成功: {api_id}")
            return {
                "success": True,
                "message": f"API更新成功: {api_id}",
                "api": api.get_info()
            }
        except Exception as e:
            self.logger.error(f"更新API失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新API失败: {str(e)}"
            }
    
    async def list_apis(self) -> Dict[str, Any]:
        """列出所有API"""
        try:
            self.logger.info("列出所有API")
            
            apis_info = [api.get_info() for api in self.apis.values()]
            
            return {
                "apis": apis_info,
                "total": len(apis_info)
            }
        except Exception as e:
            self.logger.error(f"列出API失败: {str(e)}")
            raise
    
    async def get_api_info(self, api_id: str) -> Dict[str, Any]:
        """获取API信息"""
        try:
            self.logger.info(f"获取API信息: {api_id}")
            
            # 检查API是否存在
            if api_id not in self.apis:
                return {
                    "success": False,
                    "message": f"API不存在: {api_id}"
                }
            
            api = self.apis[api_id]
            return {
                "success": True,
                "api": api.get_info()
            }
        except Exception as e:
            self.logger.error(f"获取API信息失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取API信息失败: {str(e)}"
            }
    
    async def call_api(self, api_id: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用API"""
        try:
            self.logger.info(f"调用API: {api_id}")
            
            # 检查API是否存在
            if api_id not in self.apis:
                return {
                    "success": False,
                    "error": f"API不存在: {api_id}"
                }
            
            api = self.apis[api_id]
            
            # 检查API是否启用
            if not api.enabled:
                return {
                    "success": False,
                    "error": f"API已禁用: {api_id}"
                }
            
            # 检查限流
            if api.rate_limit > 0:
                if not await self._check_rate_limit(api_id):
                    return {
                        "success": False,
                        "error": f"API调用频率超过限制: {api_id}"
                    }
            
            # 检查缓存
            cache_key = None
            if api.cache_ttl > 0:
                cache_key = self._generate_cache_key(api_id, params, headers)
                cached_response = self._get_cache(cache_key)
                if cached_response:
                    self.logger.info(f"API调用命中缓存: {api_id}")
                    api.update_stats(True, 0.0)
                    return {
                        "success": True,
                        "data": cached_response,
                        "from_cache": True,
                        "api_id": api_id,
                        "execution_time": 0.0
                    }
            
            # 准备请求
            request_headers = api.headers.copy()
            if headers:
                request_headers.update(headers)
            
            # 准备认证
            auth = self._prepare_auth(api.auth)
            
            # 执行请求
            start_time = time.time()
            response = self._execute_request(
                method=api.method,
                url=api.url,
                params=params,
                headers=request_headers,
                auth=auth,
                timeout=api.timeout
            )
            response_time = time.time() - start_time
            
            # 更新统计信息
            api.update_stats(True, response_time)
            
            # 保存到缓存
            if api.cache_ttl > 0 and cache_key:
                self._set_cache(cache_key, response, api.cache_ttl)
            
            return {
                "success": True,
                "data": response,
                "from_cache": False,
                "api_id": api_id,
                "execution_time": response_time,
                "status_code": 200
            }
        except requests.RequestException as e:
            self.logger.error(f"调用API失败: {str(e)}")
            if api_id in self.apis:
                api = self.apis[api_id]
                api.update_stats(False, 0.0)
            return {
                "success": False,
                "error": f"调用API失败: {str(e)}",
                "api_id": api_id
            }
        except Exception as e:
            self.logger.error(f"调用API失败: {str(e)}")
            if api_id in self.apis:
                api = self.apis[api_id]
                api.update_stats(False, 0.0)
            return {
                "success": False,
                "error": f"调用API失败: {str(e)}",
                "api_id": api_id
            }
    
    def _generate_cache_key(self, api_id: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        cache_data = {
            "api_id": api_id,
            "params": params or {},
            "headers": headers or {}
        }
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_json.encode()).hexdigest()
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if cache_entry["expires_at"] > datetime.utcnow():
                return cache_entry["data"]
            else:
                # 缓存过期，删除
                del self.cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any, ttl: int):
        """设置缓存"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self.cache[cache_key] = {
            "data": data,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
    
    async def _check_rate_limit(self, api_id: str) -> bool:
        """检查速率限制"""
        if api_id not in self.rate_limits:
            self.rate_limits[api_id] = []
        
        # 获取当前时间
        now = time.time()
        
        # 清理过期的请求记录
        self.rate_limits[api_id] = [
            timestamp for timestamp in self.rate_limits[api_id] 
            if now - timestamp < 60  # 每分钟限制
        ]
        
        # 检查是否超过限制
        api = self.apis[api_id]
        if len(self.rate_limits[api_id]) >= api.rate_limit:
            return False
        
        # 添加当前请求记录
        self.rate_limits[api_id].append(now)
        return True
    
    def _prepare_auth(self, auth_config: Dict[str, Any]) -> Optional[Any]:
        """准备认证"""
        auth_type = auth_config.get("type", "none")
        
        if auth_type == "none":
            return None
        elif auth_type == "basic":
            return requests.auth.HTTPBasicAuth(
                auth_config.get("username", ""),
                auth_config.get("password", "")
            )
        elif auth_type == "bearer":
            return requests.auth.HTTPBearerAuth(auth_config.get("token", ""))
        elif auth_type == "api_key":
            # API Key通常在headers中处理
            return None
        else:
            self.logger.warning(f"不支持的认证类型: {auth_type}")
            return None
    
    def _execute_request(self, method: str, url: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None, auth: Any = None, timeout: int = 10) -> Any:
        """执行HTTP请求"""
        method = method.upper()
        
        if method == "GET":
            response = requests.get(
                url, params=params, headers=headers, auth=auth, timeout=timeout
            )
        elif method == "POST":
            response = requests.post(
                url, json=params, headers=headers, auth=auth, timeout=timeout
            )
        elif method == "PUT":
            response = requests.put(
                url, json=params, headers=headers, auth=auth, timeout=timeout
            )
        elif method == "DELETE":
            response = requests.delete(
                url, params=params, headers=headers, auth=auth, timeout=timeout
            )
        elif method == "PATCH":
            response = requests.patch(
                url, json=params, headers=headers, auth=auth, timeout=timeout
            )
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 解析响应
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
    
    async def clear_cache(self, api_id: Optional[str] = None) -> Dict[str, Any]:
        """清除缓存"""
        try:
            if api_id:
                # 清除指定API的缓存
                cache_keys = list(self.cache.keys())
                cleared = 0
                for key in cache_keys:
                    if key.startswith(api_id):
                        del self.cache[key]
                        cleared += 1
                return {
                    "success": True,
                    "message": f"清除了 {cleared} 个缓存项",
                    "api_id": api_id
                }
            else:
                # 清除所有缓存
                cache_count = len(self.cache)
                self.cache.clear()
                return {
                    "success": True,
                    "message": f"清除了 {cache_count} 个缓存项"
                }
        except Exception as e:
            self.logger.error(f"清除缓存失败: {str(e)}")
            return {
                "success": False,
                "message": f"清除缓存失败: {str(e)}"
            }
    
    async def reset_stats(self, api_id: Optional[str] = None) -> Dict[str, Any]:
        """重置统计信息"""
        try:
            if api_id:
                # 重置指定API的统计信息
                if api_id in self.apis:
                    api = self.apis[api_id]
                    api.stats = {
                        "total_calls": 0,
                        "success_calls": 0,
                        "failed_calls": 0,
                        "avg_response_time": 0.0,
                        "last_call": None
                    }
                    return {
                        "success": True,
                        "message": f"重置了API {api_id} 的统计信息"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"API {api_id} 不存在"
                    }
            else:
                # 重置所有API的统计信息
                for api in self.apis.values():
                    api.stats = {
                        "total_calls": 0,
                        "success_calls": 0,
                        "failed_calls": 0,
                        "avg_response_time": 0.0,
                        "last_call": None
                    }
                return {
                    "success": True,
                    "message": f"重置了所有 {len(self.apis)} 个API的统计信息"
                }
        except Exception as e:
            self.logger.error(f"重置统计信息失败: {str(e)}")
            return {
                "success": False,
                "message": f"重置统计信息失败: {str(e)}"
            }
