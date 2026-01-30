import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
import httpx
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    logger.info(f"Received request to generate with text length: {len(request.text)}")

    # 获取API密钥 - 从环境变量或配置中获取
    api_key = os.getenv("ALIBABA_CLOUD_API_KEY") or settings.ALIBABA_CLOUD_API_KEY

    if not api_key:
        logger.error("Missing Alibaba Cloud API key")
        raise HTTPException(status_code=400, detail="缺少阿里云API密钥，请在环境变量中设置 ALIBABA_CLOUD_API_KEY")

    logger.info("API key found, proceeding with request")

    # 检查输入文本长度，防止过长的文本导致API调用失败
    if len(request.text) > 8000:  # 限制文本长度，可根据API限制调整
        logger.warning(f"Input text too long: {len(request.text)} characters")
        raise HTTPException(status_code=400, detail=f"输入文本过长 ({len(request.text)} 字符)，请减少到8000字符以内")

    logger.info(f"Text length is acceptable: {len(request.text)} characters")

    # 固定的提示词，用于文本信息提取
    fixed_prompt = """你是一个文本信息提取助手，请严格按照要求处理用户提供的文本。

任务要求：
1. 从提供的文本中提取所有说话的人物，生成一个说话人列表（memberList）
2. 从提供的文本中提取所有人说的话，按照原文中对话的顺序进行排列，生成一个内容列表（content），每条内容包括说话人姓名、排序ID和说话内容
3. 将上述两个结果合并成一个统一的JSON格式

输出格式规范：
{
  "memberList": ["人物1", "人物2", ...],
  "content": [
    {
      "speaker": "说话人姓名",
      "sortId": 序号,
      "content": "根据原文的说话内容进行提取，要求风趣幽默，并符合人物性格特点"
    },
    ...
  ]
}

处理规则：
1. memberList：列出文本中所有说过话的人物，使用原文中的标准称呼
2. content数组：按照说话内容在原文中出现的顺序，为每个发言创建一个对象
3. sortId：从1开始顺序编号，表示发言的先后顺序
4. 根据原文的说话内容进行提取，要求风趣幽默，并符合人物性格特点

示例参考：
如果文本包含：
人物A说："内容1"
人物B说："内容2"
人物A说："内容3"
人物B说："内容4"
人物C说："内容5"

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

    # 阿里云通义千问API的URL
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    logger.info(f"Calling API at URL: {url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-plus",
         "messages": [
             {
      "role": "system",
      "content": fixed_prompt
    },
                {
                    "role": "user",
                    "content": request.text
                }
            ],

        "response_format": {
            "type": "json_object"
        }
    }

    logger.info(f"Sending request with payload size: {len(json.dumps(payload))} characters")

    try:
        logger.info("Making API request...")
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        logger.info(f"API response received with status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API call failed with status {response.status_code}: {response}")
            raise HTTPException(status_code=response.status_code, detail=f"API调用失败: {response.text}")

        result = response.json()
        logger.info("API response parsed as JSON successfully ")

        # 解析并返回AI生成的内容
        # For OpenAI-compatible API, the response structure is different
        choices = result.get("choices", [])
        if choices:
            generated_text = choices[0].get("message", {}).get("content", "")
        else:
            generated_text = ""

        logger.info(f"Generated text received with length: {len(generated_text)} characters")

        # 尝试解析JSON
        try:
            parsed_data = json.loads(generated_text)
            logger.info("Generated text parsed as JSON successfully")
        except json.JSONDecodeError:
            logger.warning("Generated text is not valid JSON, returning as plain text")
            parsed_data = {"generated_text": generated_text}

        logger.info("Request completed successfully")
        return QwenResponse(
            success=True,
            data=parsed_data,
            message="AI生成成功"
        )

    except httpx.TimeoutException as e:
        logger.error(f"API request timed out: {str(e)}")
        raise HTTPException(status_code=500, detail="请求阿里云API超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"API request returned HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"API请求状态错误: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Network error during API request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生网络错误: {str(e)}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during API request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生HTTP错误: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}, response: {result}")
        raise HTTPException(status_code=500, detail=f"解析API响应时发生JSON错误: {str(e)}, 响应内容: {result}")
    except Exception as e:
        logger.error(f"Unexpected error during request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生未知错误: {str(e)}")


@router.post("/wechat-chat", response_model=QwenResponse)
async def generate_wechat_chat(request: QwenRequest):
    """
    将历史文本转化为微信群聊对话形式
    """
    logger.info(f"Received request to generate WeChat chat with text length: {len(request.text)}")

    # 获取API密钥 - 从环境变量或配置中获取
    api_key = os.getenv("ALIBABA_CLOUD_API_KEY") or settings.ALIBABA_CLOUD_API_KEY

    if not api_key:
        logger.error("Missing Alibaba Cloud API key")
        raise HTTPException(status_code=400, detail="缺少阿里云API密钥，请在环境变量中设置 ALIBABA_CLOUD_API_KEY")

    logger.info("API key found, proceeding with request")

    # 检查输入文本长度，防止过长的文本导致API调用失败
    if len(request.text) > 8000:  # 限制文本长度，可根据API限制调整
        logger.warning(f"Input text too long: {len(request.text)} characters")
        raise HTTPException(status_code=400, detail=f"输入文本过长 ({len(request.text)} 字符)，请减少到8000字符以内")

    logger.info(f"Text length is acceptable: {len(request.text)} characters")

    # 固定的提示词，用于将历史文本转换为微信群聊对话
    wechat_prompt = """### 优化后提示词：

**核心任务：**
将给定历史文本转化为**纯微信群聊对话**形式，要求风趣幽默且符合历史人物性格。

**具体要求：**

1. **形式限制**
   - 只允许出现**单一微信群聊**界面
   - 禁止出现"私聊""朋友圈""私信"等任何非群聊形式
   - 所有对话必须发生在**同一个群组内**

2. **风格与内容**
   - 语言风格：**现代微信聊天风格**（可合理使用表情包、撤回消息、群公告等功能性提示）
   - 人物性格：严格基于史料中的人物特征进行**合理化演绎**
   - 幽默处理：在尊重史实基础上，通过**对话设计、语气措辞、情境反差**制造幽默效果

3. **结构要求**
   - 开篇需有**群聊名称及初始成员说明**
   - 通过**自然的时间推进**展现历史事件发展
   - 关键情节用**群内互动**呈现（如：@特定人物）
   - 允许使用**系统提示**（如：xxx已退出群聊）但不得作为主要叙述手段

4. **禁止事项**
   - 不得添加原文外的虚构重大情节
   - 不得使用"旁白""注释""后记"等说明性文字
   - 不得中断对话插入作者解释

**示例结构：**
```
【群聊：大明内阁工作群（5人）】
崇祯帝：@全体成员 朕刚看到顾其国的奏折...
韩爌：陛下圣明，臣等已...
刘懋：（突然加入群聊）陛下！臣有数据！
...
（通过对话自然展现两年后）
刘懋：@崇祯帝 陛下，裁驿后各地怨声载道...
崇祯帝：...朕知道了。
【系统提示：刘懋已退出群聊】
```

请基于以上框架，将提供的"文本"史料转化为一个完整、连贯、有趣的微信群聊故事。"""

    # 构建完整的提示词 - 使用固定提示词 + 用户提供的文本
    full_prompt = f"{wechat_prompt}\n\n{request.text}"
    logger.info(f"Full prompt constructed, total length: {len(full_prompt)} characters")

    # 阿里云通义千问API的URL
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    logger.info(f"Calling API at URL: {url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-plus",
         "messages": [
             {
      "role": "system",
      "content": wechat_prompt
    },
                {
                    "role": "user",
                    "content": request.text
                }
            ],

        "response_format": {
            "type": "text"  # Return as text since we want the chat format as text
        }
    }

    logger.info(f"Sending request with payload size: {len(json.dumps(payload))} characters")

    try:
        logger.info("Making API request...")
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        logger.info(f"API response received with status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API call failed with status {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"API调用失败: {response.text}")

        result = response.json()
        logger.info("API response parsed as JSON successfully")
        logger.info(f"Raw API response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 解析并返回AI生成的内容
        # For OpenAI-compatible API, the response structure is different
        choices = result.get("choices", [])
        if choices:
            generated_text = choices[0].get("message", {}).get("content", "")
        else:
            generated_text = ""

        logger.info(f"Generated text received with length: {len(generated_text)} characters")

        # Return the generated text as is (it's already in the desired format)
        parsed_data = {"wechat_chat": generated_text}

        logger.info("Request completed successfully")
        return QwenResponse(
            success=True,
            data=parsed_data,
            message="微信群聊生成成功"
        )

    except httpx.TimeoutException as e:
        logger.error(f"API request timed out: {str(e)}")
        raise HTTPException(status_code=500, detail="请求阿里云API超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"API request returned HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"API请求状态错误: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Network error during API request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生网络错误: {str(e)}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during API request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"请求阿里云API时发生HTTP错误: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}, response: {result}")
        raise HTTPException(status_code=500, detail=f"解析API响应时发生JSON错误: {str(e)}, 响应内容: {result}")
    except Exception as e:
        logger.error(f"Unexpected error during request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生未知错误: {str(e)}")