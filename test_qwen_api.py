"""
Test script for the Qwen AI API
"""
import asyncio
import json
from app.api.qwen_ai import generate_with_qwen, QwenRequest


async def test_local_function():
    """
    Test the local function directly without starting the full server
    """
    # Create a sample request
    request = QwenRequest(
        text="请用中文总结人工智能的发展历程",
        prompt="你是一个专业的AI助手，请详细回答以下问题："
    )
    
    try:
        # Call the function directly
        result = await generate_with_qwen(request)
        print("API调用成功!")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Data: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"API调用失败: {str(e)}")


if __name__ == "__main__":
    # Note: This test will fail without a valid API key, but it will show if the structure is correct
    print("测试Qwen AI API功能...")
    try:
        asyncio.run(test_local_function())
    except Exception as e:
        print(f"测试过程中出现异常: {str(e)}")
        print("注意: 如果是因为缺少API密钥导致的错误，这是正常的。请确保在.env文件中设置了ALIBABA_CLOUD_API_KEY")