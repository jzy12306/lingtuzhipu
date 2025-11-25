"""API限流中间件"""
import time
import logging
from typing import Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import asyncio
from functools import wraps

from src.core.performance import performance_config

logger = logging.getLogger(__name__)


class MemoryRateLimiter:
    """基于内存的简单速率限制器"""
    
    def __init__(self):
        # 请求记录字典: {client_ip: {route: [timestamps]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        # 封禁字典: {client_ip: {route: timestamp}}
        self.bans: Dict[str, Dict[str, float]] = defaultdict(dict)
        # 用于线程安全的锁
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, client_ip: str, route: str) -> bool:
        """检查是否允许请求"""
        async with self.lock:
            # 检查是否被封禁
            if await self._is_banned(client_ip, route):
                return False
            
            # 清理过期请求记录
            await self._clean_old_requests(client_ip, route)
            
            # 获取路由的限流配置
            config = performance_config.rate_limit.get_config_for_route(route)
            if not config["enabled"]:
                return True
            
            # 记录当前请求
            current_time = time.time()
            self.requests[client_ip][route].append(current_time)
            
            # 检查是否超过限制
            minute_window = current_time - 60
            minute_count = sum(1 for t in self.requests[client_ip][route] if t > minute_window)
            
            hour_window = current_time - 3600
            hour_count = sum(1 for t in self.requests[client_ip][route] if t > hour_window)
            
            if minute_count > config["per_minute"] or hour_count > config["per_hour"]:
                # 触发封禁
                self.bans[client_ip][route] = current_time + config["block_duration"]
                logger.warning(f"IP {client_ip} 访问路由 {route} 触发限流，已封禁 {config['block_duration']} 秒")
                return False
            
            return True
    
    async def _is_banned(self, client_ip: str, route: str) -> bool:
        """检查IP是否被封禁"""
        if route in self.bans[client_ip]:
            ban_end = self.bans[client_ip][route]
            current_time = time.time()
            
            # 如果封禁已过期，移除封禁记录
            if current_time > ban_end:
                del self.bans[client_ip][route]
                return False
            
            return True
        
        return False
    
    async def _clean_old_requests(self, client_ip: str, route: str) -> None:
        """清理过期的请求记录"""
        if route not in self.requests[client_ip]:
            return
        
        # 保留最近一小时的记录即可
        one_hour_ago = time.time() - 3600
        self.requests[client_ip][route] = [
            t for t in self.requests[client_ip][route] 
            if t > one_hour_ago
        ]
    
    async def get_rate_limits(self, client_ip: str, route: str) -> Dict[str, Any]:
        """获取当前速率限制信息"""
        async with self.lock:
            await self._clean_old_requests(client_ip, route)
            current_time = time.time()
            
            # 计算最近一分钟的请求数
            minute_window = current_time - 60
            minute_count = sum(1 for t in self.requests[client_ip].get(route, []) if t > minute_window)
            
            # 计算最近一小时的请求数
            hour_window = current_time - 3600
            hour_count = sum(1 for t in self.requests[client_ip].get(route, []) if t > hour_window)
            
            # 检查封禁状态
            ban_status = {"is_banned": False}
            if await self._is_banned(client_ip, route):
                ban_end = self.bans[client_ip][route]
                ban_status = {
                    "is_banned": True,
                    "ban_end": ban_end,
                    "ban_remaining": ban_end - current_time
                }
            
            return {
                "requests_per_minute": {
                    "count": minute_count,
                    "limit": performance_config.rate_limit.get_config_for_route(route)["per_minute"]
                },
                "requests_per_hour": {
                    "count": hour_count,
                    "limit": performance_config.rate_limit.get_config_for_route(route)["per_hour"]
                },
                "ban_status": ban_status
            }


# 创建全局速率限制器实例
rate_limiter = MemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI速率限制中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 如果限流功能未启用，直接通过
        if not performance_config.rate_limit.enabled:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        # 获取路由标识
        route = self._get_route_identifier(request)
        
        # 检查是否允许请求
        is_allowed = await rate_limiter.is_allowed(client_ip, route)
        
        if not is_allowed:
            # 获取封禁信息
            limits = await rate_limiter.get_rate_limits(client_ip, route)
            ban_remaining = limits["ban_status"].get("ban_remaining", 0)
            
            # 返回429错误
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": int(ban_remaining) if ban_remaining > 0 else 60
                }
            )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        limits = await rate_limiter.get_rate_limits(client_ip, route)
        response.headers["X-RateLimit-Limit-Minute"] = str(limits["requests_per_minute"]["limit"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            limits["requests_per_minute"]["limit"] - limits["requests_per_minute"]["count"]
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(limits["requests_per_hour"]["limit"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            limits["requests_per_hour"]["limit"] - limits["requests_per_hour"]["count"]
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """从请求中获取客户端IP"""
        # 尝试从X-Forwarded-For头获取（如果有代理）
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return x_forwarded_for.split(",")[0].strip()
        
        # 尝试从X-Real-IP头获取
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        
        # 使用请求的client.host
        return request.client.host
    
    def _get_route_identifier(self, request: Request) -> str:
        """获取路由标识符"""
        path = request.url.path
        method = request.method
        
        # 处理特殊路由
        if "/api/auth/login" in path:
            return "login"
        if "/api/auth/register" in path:
            return "register"
        
        # 为API路由生成标识符
        if path.startswith("/api/"):
            # 移除可能包含动态参数的部分
            path_parts = path.split("/")
            # 保留前3个部分，通常是 /api/{module}/
            if len(path_parts) >= 4:
                return f"{path_parts[2]}"
        
        # 默认使用完整路径
        return f"{method}:{path}"


def rate_limited(route: str = "default"):
    """装饰器：对特定路由应用速率限制"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 如果限流功能未启用，直接执行函数
            if not performance_config.rate_limit.enabled:
                return await func(request, *args, **kwargs)
            
            # 获取客户端IP
            client_ip = RateLimitMiddleware._get_client_ip(RateLimitMiddleware(), request)
            
            # 检查是否允许请求
            is_allowed = await rate_limiter.is_allowed(client_ip, route)
            
            if not is_allowed:
                # 获取封禁信息
                limits = await rate_limiter.get_rate_limits(client_ip, route)
                ban_remaining = limits["ban_status"].get("ban_remaining", 0)
                
                # 返回429错误
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": int(ban_remaining) if ban_remaining > 0 else 60
                    }
                )
            
            # 执行原函数
            response = await func(request, *args, **kwargs)
            
            # 如果响应是Response对象，添加速率限制头
            if isinstance(response, Response):
                limits = await rate_limiter.get_rate_limits(client_ip, route)
                response.headers["X-RateLimit-Limit-Minute"] = str(limits["requests_per_minute"]["limit"])
                response.headers["X-RateLimit-Remaining-Minute"] = str(
                    limits["requests_per_minute"]["limit"] - limits["requests_per_minute"]["count"]
                )
            
            return response
        
        return wrapper
    
    return decorator