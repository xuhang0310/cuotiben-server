from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import requests
import json
from app.core.config import settings


router = APIRouter(prefix="/qwen", tags=["qwen-ai"])


class QwenRequest(BaseModel):
    text: str
    prompt: Optional[str] = ""


class QwenResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.post("/generate", response_model=QwenResponse)
async def generate_with_qwen(request: QwenRequest):
    """
    根据传入的文本调用阿里云千问AI大模型，返回指定的JSON数据
    """
    # 获取API密钥 - 从环境变量或配置中获取
    api_key = os.getenv("ALIBABA_CLOUD_API_KEY") or settings.ALIBABA_CLOUD_API_KEY

    if not api_key:
        raise HTTPException(status_code=400, detail="缺少阿里云API密钥，请在环境变量中设置 ALIBABA_CLOUD_API_KEY")

    # 构建完整的提示词
    full_prompt = request.prompt + "\n\n" + request.text if request.prompt else request.text

    # 阿里云通义千问API的URL (这里使用通义千问的API地址)
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-max",  # 或者使用其他可用的模型如 qwen-plus, qwen-turbo
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        },
        "parameters": {
            "result_format": "json"  # 请求返回格式为JSON
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API调用失败: {response.text}")

        result = response.json()

        # 解析并返回AI生成的内容
        generated_text = result.get("output", {}).get("text", "")

        # 这里可以根据实际需求解析返回的数据结构
        # 假设返回的是JSON格式的数据
        try:
            parsed_data = json.loads(generated_text)
        except json.JSONDecodeError:
            # 如果返回的不是有效的JSON，则直接返回文本内容
            parsed_data = {"generated_text": generated_text}

        return QwenResponse(
            success=True,
            data=parsed_data,
            message="AI生成成功"
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生未知错误: {str(e)}")