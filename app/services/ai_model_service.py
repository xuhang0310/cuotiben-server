"""
AI模型服务
负责调用各种AI模型API
"""

from __future__ import annotations
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.ai_chat import AiModel
import logging

logging.basicConfig(level=logging.DEBUG)
logging.debug("AI模型服务已加载")

# 为了兼容Python 3.9~3.13，使用延迟求值
# 在Python 3.7+中，可以使用from __future__ import annotations来提高类型提示性能


# 尝试导入aiohttp，如果失败则在使用时抛出更友好的错误
try:
    import aiohttp
except ImportError:
    aiohttp = None
    print("警告: aiohttp模块未安装，AI模型服务将无法正常工作。请运行: pip install aiohttp")


class AiModelService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def generate(self, model_name: str, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """调用AI模型生成响应"""
        # 获取模型配置
        ai_model = self.db.query(AiModel).filter(
            AiModel.model_name == model_name
        ).first()

        if not ai_model or (hasattr(ai_model, 'is_active') and ai_model.is_active is False):
            raise ValueError(f"AI模型不可用: {model_name}")

        # 根据模型类型调用相应API
        if "openai" in model_name.lower():
            return await self._call_openai_api(ai_model, prompt, max_tokens, temperature)
        elif "qwen" in model_name.lower() or "ali" in model_name.lower():
            return await self._call_alibaba_api(ai_model, prompt, max_tokens, temperature)
        else:
            # 默认使用OpenAI兼容接口
            return await self._call_openai_api(ai_model, prompt, max_tokens, temperature)

    async def _call_openai_api(self, ai_model: AiModel, prompt: str, max_tokens: int, temperature: float) -> str:
        """调用OpenAI API"""
        if aiohttp is None:
            raise ImportError("aiohttp模块未安装，请运行: pip install aiohttp")

        import ssl
        import certifi
        
        # 创建SSL上下文，使用certifi提供的证书
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ai_model.api_key}"
        }

        payload = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        logging.info(f"调用OpenAI API，模型: {ai_model.model_name}, 请求体: {payload}")
        logging.info(f"OpenAI API端点: {ai_model.endpoint}")
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                f"{ai_model.endpoint}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()

                if response.status != 200:
                    raise Exception(f"API调用失败: {result}")

                return result["choices"][0]["message"]["content"].strip()

    async def _call_alibaba_api(self, ai_model: AiModel, prompt: str, max_tokens: int, temperature: float) -> str:
        """调用阿里云API"""
        if aiohttp is None:
            raise ImportError("aiohttp模块未安装，请运行: pip install aiohttp")
        
        import ssl
        import certifi
        
        # 创建SSL上下文，使用certifi提供的证书
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # 这里需要根据阿里云实际API接口调整
        # 示例代码（需要根据实际API文档修改）
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ai_model.api_key}"
        }

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                ai_model.endpoint,
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()

                if response.status != 200:
                    raise Exception(f"API调用失败: {result}")

                return result["response"]["output"]["text"].strip()