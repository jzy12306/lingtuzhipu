import logging
from typing import Dict, Any, Optional, List
import httpx
from openai import AsyncOpenAI, OpenAIError
from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务接口"""
    
    def __init__(self):
        self.local_llm_enabled = settings.LOCAL_LLM_ENABLED
        self.local_llm_url = settings.LOCAL_LLM_URL
        self.local_llm_model = settings.LOCAL_LLM_MODEL
        self.local_llm_timeout = settings.LOCAL_LLM_TIMEOUT
        
        # 初始化OpenAI客户端（如果配置了API密钥）
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.logger = logger.getChild("LLMService")
    
    async def generate_text(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        use_fallback: bool = True
    ) -> str:
        """生成文本响应"""
        try:
            # 优先使用本地LLM
            if self.local_llm_enabled:
                try:
                    return await self._generate_with_local_llm(
                        prompt, system_message, max_tokens, temperature
                    )
                except Exception as e:
                    self.logger.error(f"本地LLM调用失败: {str(e)}")
                    if not use_fallback:
                        raise
            
            # 使用OpenAI作为降级方案
            if self.openai_client:
                return await self._generate_with_openai(
                    prompt, system_message, max_tokens, temperature
                )
            
            raise RuntimeError("没有可用的LLM服务")
            
        except Exception as e:
            self.logger.error(f"LLM生成失败: {str(e)}")
            raise
    
    async def _generate_with_local_llm(
        self, 
        prompt: str, 
        system_message: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """使用本地LM Studio生成文本"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=self.local_llm_timeout) as client:
            response = await client.post(
                f"{self.local_llm_url}/v1/chat/completions",
                json={
                    "model": self.local_llm_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"本地LLM返回格式错误: {result}")
    
    async def _generate_with_openai(
        self, 
        prompt: str, 
        system_message: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """使用OpenAI生成文本"""
        if not self.openai_client:
            raise ValueError("OpenAI客户端未初始化")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def extract_entities_and_relations(self, text: str) -> Dict[str, Any]:
        """从文本中提取实体和关系"""
        system_prompt = "你是一个专业的信息提取助手，负责从文本中识别实体及其关系。请以JSON格式返回结果。"
        
        user_prompt = f"""请从以下文本中提取实体和它们之间的关系：

{text}

请以以下JSON格式返回：
{
  "entities": [
    {"id": "实体ID", "name": "实体名称", "type": "实体类型"}
  ],
  "relations": [
    {"id": "关系ID", "source": "源实体ID", "target": "目标实体ID", "type": "关系类型", "properties": {}}
  ]
}

请确保返回的是有效的JSON格式，不要包含任何其他文本。"""
        
        try:
            result = await self.generate_text(
                user_prompt,
                system_prompt,
                max_tokens=2048,
                temperature=0.3
            )
            
            # 解析JSON结果
            import json
            parsed_result = json.loads(result)
            return parsed_result
        except Exception as e:
            self.logger.error(f"实体关系提取失败: {str(e)}")
            raise
    
    async def analyze_document_type(self, text: str) -> Dict[str, Any]:
        """分析文档类型"""
        system_prompt = "你是一个专业的文档分析助手，负责识别文档的行业和类型。"
        
        user_prompt = f"""请分析以下文本内容，确定文档所属的行业（金融、医疗、法律或其他）以及具体类型：

{text[:1000]}...

请以以下JSON格式返回：
{
  "industry": "行业类型",
  "document_type": "文档类型",
  "confidence": 置信度(0-1),
  "keywords": ["关键词1", "关键词2"]
}

请确保返回的是有效的JSON格式。"""
        
        result = await self.generate_text(
            user_prompt,
            system_prompt,
            max_tokens=512,
            temperature=0.2
        )
        
        import json
        return json.loads(result)


# 创建全局LLM服务实例
llm_service = LLMService()