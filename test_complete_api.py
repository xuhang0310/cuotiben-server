#!/usr/bin/env python3
"""
完整测试脚本：验证修复后的 API 端点功能
"""

import requests
import json
from typing import Dict, Any
import time
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

def create_test_user_token():
    """
    创建一个测试用户并生成有效的 JWT token
    """
    # 创建一个模拟的有效载荷
    expire = datetime.utcnow() + timedelta(minutes=180)  # 3小时过期
    to_encode = {
        "sub": "test@example.com",  # 使用一个测试邮箱
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def test_api_with_valid_token():
    """
    使用有效的 token 测试 API 端点
    """
    # 生成一个有效的 token
    token = create_test_user_token()
    
    # API 端点
    api_url = "http://localhost:8000/api/ai-chat/groups/"
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 请求参数
    params = {
        "skip": 0,
        "limit": 10
    }
    
    print(f"正在测试 API 端点: {api_url}")
    print(f"Token: {token[:20]}...")  # 只显示前20个字符
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    
    try:
        # 发送 GET 请求
        response = requests.get(api_url, headers=headers, params=params)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 尝试解析 JSON 响应
        try:
            json_response = response.json()
            print(f"JSON 响应: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("响应不是有效的 JSON 格式")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    
    # 测试创建群组的 POST 请求
    print("\n" + "="*50)
    print("测试创建群组的 POST 请求:")
    
    create_url = "http://localhost:8000/api/ai-chat/groups/"
    create_data = {
        "name": "测试群组",
        "description": "这是一个测试群组",
        "avatar_url": "https://example.com/avatar.jpg"
    }
    
    try:
        create_response = requests.post(create_url, headers=headers, json=create_data)
        print(f"创建群组响应状态码: {create_response.status_code}")
        print(f"创建群组响应内容: {create_response.text}")
        
        # 尝试解析 JSON 响应
        try:
            create_json_response = create_response.json()
            print(f"创建群组 JSON 响应: {json.dumps(create_json_response, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("创建群组响应不是有效的 JSON 格式")
            
    except requests.exceptions.RequestException as e:
        print(f"创建群组请求失败: {e}")


def test_original_token():
    """
    使用原始提供的 token 测试 API 端点
    """
    # 原始提供的 token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VybmFtZUAxNjMuY29tIiwiZXhwIjoxNzcwMzAyNDQwfQ.NLYTm_k9ho5_fjHOGO5n3eTpMF3guUBRW8ob2GWgmS8"
    
    # API 端点
    api_url = "http://localhost:8000/api/ai-chat/groups/"
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 请求参数
    params = {
        "skip": 0,
        "limit": 10
    }
    
    print(f"正在测试原始 token 的 API 端点: {api_url}")
    print(f"Token: {token[:20]}...")  # 只显示前20个字符
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    
    try:
        # 发送 GET 请求
        response = requests.get(api_url, headers=headers, params=params)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 尝试解析 JSON 响应
        try:
            json_response = response.json()
            print(f"JSON 响应: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("响应不是有效的 JSON 格式")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")


def decode_token_info(token: str) -> Dict[str, Any]:
    """
    解码 JWT token 的信息（不验证签名）
    """
    import base64
    
    try:
        # 分割 token
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid token format"}
        
        # 解码 payload（第二部分）
        payload = parts[1]
        # 补充 padding
        payload += '=' * (4 - len(payload) % 4)
        
        decoded_payload = base64.b64decode(payload)
        payload_json = json.loads(decoded_payload)
        
        return payload_json
    except Exception as e:
        return {"error": f"Failed to decode token: {e}"}


if __name__ == "__main__":
    print("API 功能验证测试脚本")
    print("="*60)
    
    
    print("\n" + "="*60)
    print("测试原始 token (可能失败，因为用户可能不存在于数据库中):")
    test_original_token()
    
    
    print("\n" + "="*60)
    print("测试完成!")