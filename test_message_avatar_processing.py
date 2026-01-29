#!/usr/bin/env python
"""
测试会话消息API头像URL处理功能
"""
import requests
import json

def test_message_avatar_processing():
    base_url = "http://localhost:8000"
    # 使用一个存在的会话ID进行测试
    endpoint = "/api/chat/test-session/messages/"
    
    print(f"正在测试API端点: {base_url}{endpoint}")
    print("注意：如果会话不存在，将返回空的消息列表，这是正常的")
    
    try:
        response = requests.get(base_url + endpoint)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API调用成功!")
            print(f"状态码: {response.status_code}")
            print(f"总共找到 {data['total']} 条消息")
            
            if data['data']:
                print(f"\n📋 消息列表:")
                for msg in data['data']:
                    user_id = msg['user_id']
                    content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content'] if msg['content'] else ""
                    avatar = msg.get('avatar', 'N/A')
                    
                    # 判断头像URL是否已处理
                    if avatar != 'N/A':
                        is_processed = avatar.startswith('http://180.76.183.241:8000/')
                        status = "✅ 已处理" if is_processed else "❌ 未处理或外部链接"
                        print(f"- 用户ID: {user_id}, 内容: {content}, 头像: {status}")
                    else:
                        print(f"- 用户ID: {user_id}, 内容: {content}, 头像: N/A")
            else:
                print("\n📋 没有找到任何消息（会话可能为空或不存在）")
                
            print(f"\n💡 说明:")
            print(f"- 以 'http://180.76.183.241:8000/' 开头的URL表示已被处理")
            print(f"- 以其他域名开头的URL表示是外部链接，不会被处理")
            print(f"- 空的或None的头像URL不会被处理")
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
        print("请运行 'python run.py' 启动服务器")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

def test_specific_conversation():
    """测试一个具体存在的会话"""
    base_url = "http://localhost:8000"
    # 先获取一个存在的会话ID
    conv_endpoint = "/api/chat/"
    
    print(f"\n🔍 首先获取会话列表...")
    try:
        response = requests.get(base_url + conv_endpoint)
        if response.status_code == 200:
            conv_data = response.json()
            if conv_data['data']:
                # 使用第一个会话ID测试消息API
                first_conv_id = conv_data['data'][0]['id']
                print(f"使用会话ID '{first_conv_id}' 测试消息API...")
                
                msg_endpoint = f"/api/chat/{first_conv_id}/messages/"
                msg_response = requests.get(base_url + msg_endpoint)
                
                if msg_response.status_code == 200:
                    msg_data = msg_response.json()
                    print(f"\n✅ 找到会话 '{first_conv_id}' 的 {msg_data['total']} 条消息")
                    
                    if msg_data['data']:
                        print(f"\n📋 消息详情:")
                        for i, msg in enumerate(msg_data['data'][:5]):  # 只显示前5条
                            user_id = msg['user_id']
                            content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content'] if msg['content'] else ""
                            avatar = msg.get('avatar', 'N/A')
                            
                            # 判断头像URL是否已处理
                            if avatar != 'N/A':
                                is_processed = avatar.startswith('http://180.76.183.241:8000/')
                                status = "✅ 已处理" if is_processed else "❌ 未处理或外部链接"
                                print(f"- [{i+1}] 用户ID: {user_id}, 内容: {content}, 头像: {status}")
                            else:
                                print(f"- [{i+1}] 用户ID: {user_id}, 内容: {content}, 头像: N/A")
                        if len(msg_data['data']) > 5:
                            print(f"... 还有 {len(msg_data['data']) - 5} 条消息")
                    else:
                        print(f"\n📋 会话 '{first_conv_id}' 中没有消息")
                else:
                    print(f"❌ 获取消息失败: {msg_response.status_code}")
            else:
                print("❌ 没有找到任何会话")
        else:
            print(f"❌ 获取会话列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_message_avatar_processing()
    test_specific_conversation()