import os
import logging
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
from utils.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    OpenAI API服务封装类
    提供与OpenAI API或兼容接口的交互功能
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.default_model = settings.LLM_MODEL
        self.timeout = 60.0  # 超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2.0  # 重试延迟（秒）
        
        # 本地LLM支持
        self.use_local_llm = settings.USE_LOCAL_LLM
        self.local_llm_url = settings.LOCAL_LLM_URL
        
        logger.info(f"OpenAIService初始化完成，使用模型: {self.default_model}，本地模式: {self.use_local_llm}")
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None,
                            response_format: Optional[Dict[str, str]] = None) -> str:
        """
        调用Chat Completion API
        
        Args:
            messages: 消息列表，格式为[{"role": "system/user/assistant", "content": "消息内容"}]
            model: 使用的模型，默认为配置中的模型
            temperature: 温度参数，控制生成的随机性
            max_tokens: 最大生成token数
            response_format: 响应格式，例如 {"type": "json_object"}
            
        Returns:
            str: 生成的回复内容
        """
        if not model:
            model = self.default_model
        
        # 根据是否使用本地LLM选择请求URL
        if self.use_local_llm:
            url = f"{self.local_llm_url}/v1/chat/completions"
        else:
            url = f"{self.api_base}/v1/chat/completions"
        
        # 构建请求参数
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if response_format:
            payload["response_format"] = response_format
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 只有在使用非本地LLM时才添加API密钥
        if not self.use_local_llm and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # 重试逻辑
        retries = 0
        while retries < self.max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return result["choices"][0]["message"]["content"]
                        elif response.status == 429:
                            # 速率限制，等待后重试
                            retry_after = int(response.headers.get("Retry-After", str(self.retry_delay)))
                            logger.warning(f"API速率限制，{retry_after}秒后重试...")
                            await asyncio.sleep(retry_after)
                            retries += 1
                        else:
                            error_text = await response.text()
                            logger.error(f"API请求失败: {response.status} {error_text}")
                            raise Exception(f"API请求失败: {response.status} {error_text}")
                            
            except asyncio.TimeoutError:
                logger.error(f"API请求超时，{self.retry_delay}秒后重试...")
                await asyncio.sleep(self.retry_delay)
                retries += 1
            except Exception as e:
                logger.error(f"API调用异常: {str(e)}")
                if retries < self.max_retries - 1:
                    logger.info(f"{self.retry_delay}秒后重试...")
                    await asyncio.sleep(self.retry_delay)
                    retries += 1
                else:
                    raise
        
        raise Exception(f"达到最大重试次数({self.max_retries})，API调用失败")
    
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 要嵌入的文本
            model: 嵌入模型，默认为text-embedding-ada-002
            
        Returns:
            List[float]: 嵌入向量
        """
        if not model:
            model = "text-embedding-ada-002"
        
        # 根据是否使用本地LLM选择请求URL
        if self.use_local_llm:
            url = f"{self.local_llm_url}/v1/embeddings"
        else:
            url = f"{self.api_base}/v1/embeddings"
        
        # 构建请求参数
        payload = {
            "model": model,
            "input": text
        }
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 只有在使用非本地LLM时才添加API密钥
        if not self.use_local_llm and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result["data"][0]["embedding"]
                else:
                    error_text = await response.text()
                    logger.error(f"嵌入生成失败: {response.status} {error_text}")
                    raise Exception(f"嵌入生成失败: {response.status} {error_text}")
    
    async def batch_chat_completion(self, 
                                 batch_messages: List[List[Dict[str, str]]],
                                 model: Optional[str] = None,
                                 temperature: float = 0.7,
                                 max_concurrent: int = 5) -> List[str]:
        """
        批量执行Chat Completion
        
        Args:
            batch_messages: 消息列表的列表
            model: 使用的模型
            temperature: 温度参数
            max_concurrent: 最大并发数
            
        Returns:
            List[str]: 生成的回复列表
        """
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(messages):
            async with semaphore:
                return await self.chat_completion(messages, model, temperature)
        
        # 并发执行
        tasks = [process_item(messages) for messages in batch_messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量处理第{i}项失败: {str(result)}")
                final_results.append(f"错误: {str(result)}")
            else:
                final_results.append(result)
        
        return final_results
    
    def set_local_llm_mode(self, use_local: bool, local_url: Optional[str] = None):
        """
        设置是否使用本地LLM
        
        Args:
            use_local: 是否使用本地LLM
            local_url: 本地LLM URL
        """
        self.use_local_llm = use_local
        if local_url:
            self.local_llm_url = local_url
        logger.info(f"本地LLM模式设置: {use_local}, URL: {self.local_llm_url}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查，测试API连接
        
        Returns:
            Dict: 健康检查结果
        """
        try:
            # 发送一个简单的请求测试连接
            test_messages = [
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "请回复'健康检查成功'。"}
            ]
            
            response = await self.chat_completion(
                messages=test_messages,
                model=self.default_model,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "model": self.default_model,
                "local_mode": self.use_local_llm,
                "response": response.strip()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.default_model,
                "local_mode": self.use_local_llm
            }