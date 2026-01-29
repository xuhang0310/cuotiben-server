#!/usr/bin/env python
"""
测试历史人物API头像URL处理功能
"""
import requests
import json

def test_avatar_processing():
    base_url = "http://localhost:8000"
    endpoint = "/api/historical-figures/"
    
    print(f"正在测试API端点: {base_url}{endpoint}")
    
    try:
        response = requests.get(base_url + endpoint)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API调用成功!")
            print(f"状态码: {response.status_code}")
            print(f"总共找到 {data['total']} 个历史人物")
            
            print(f"\n📋 历史人物列表:")
            for figure in data['data']:
                name = figure['name']
                avatar = figure['avatar']
                id = figure['id']
                # 判断头像URL是否已处理
                is_processed = avatar.startswith('http://180.76.183.241:8000/')
                status = "✅ 已处理" if is_processed else "❌ 未处理或外部链接"
                print(f"- ID: {id}, 名称: {name}, 头像: {status}")
                
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

if __name__ == "__main__":
    test_avatar_processing()