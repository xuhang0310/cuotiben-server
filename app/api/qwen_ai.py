from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
import httpx
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

    # 固定的提示词，用于文本信息提取
    fixed_prompt = """你是一个文本信息提取助手，请严格按照要求处理用户提供的文本。

任务要求：
1. 从提供的文本中提取所有说话的人物，生成一个说话人列表（memberList）
2. 从提供的文本中提取所有人说的话，按照原文中出现的先后顺序进行排列
3. 将上述两个结果合并成一个统一的JSON格式

输出格式规范：
{
  "memberList": ["人物1", "人物2", ...],
  "content": [
    {
      "speaker": "说话人姓名",
      "sortId": 序号,
      "content": "该人物说的原话内容"
    },
    ...
  ]
}

处理规则：
1. memberList：列出文本中所有说过话的人物，使用原文中的标准称呼
2. content数组：按照说话内容在原文中出现的顺序，为每个发言创建一个对象
3. sortId：从1开始顺序编号，表示发言的先后顺序
4. 保持原文的说话内容和标点符号，不做修改或删减

示例参考：
如果文本包含：
人物A说："内容1"
人物B说："内容2"

那么输出应为：
{
  "memberList": ["人物A", "人物B"],
  "content": [
    {
      "speaker": "人物A",
      "sortId": 1,
      "content": "内容1"
    },
    {
      "speaker": "人物B",
      "sortId": 2,
      "content": "内容2"
    }
  ]
}

请仔细阅读用户提供的文本，准确提取所有说话人和他们的发言内容，并按照指定格式输出JSON。"""

    # 构建完整的提示词 - 使用固定提示词 + 用户提供的文本
    full_prompt = f"{fixed_prompt}\n\n{request.text}"

    # 阿里云通义千问API的URL
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        },
        "parameters": {
            "result_format": "json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API调用失败: {response.text}")

        result = response.json()

        # 解析并返回AI生成的内容
        generated_text = result.get("output", {}).get("text", "")

        # 尝试解析JSON
        try:
            parsed_data = json.loads(generated_text)
        except json.JSONDecodeError:
            parsed_data = {"generated_text": generated_text}

        return QwenResponse(
            success=True,
            data=parsed_data,
            message="AI生成成功"
        )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生未知错误: {str(e)}")