import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/historical-figures"

def test_api():
    print("=== 历史人物API测试 ===\n")
    
    # 1. 测试获取所有历史人物（分页）
    print("1. 获取所有历史人物（分页）:")
    response = requests.get(f"{BASE_URL}/?skip=0&limit=10")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()
    
    # 2. 测试创建新历史人物
    print("2. 创建新历史人物:")
    new_figure = {
        "name": "测试人物",
        "avatar": "/images/test.png",
        "role": "测试角色",
        "status": "online",
        "create_time": "2024年"
    }
    response = requests.post(BASE_URL, json=new_figure)
    created_figure = response.json()
    print(json.dumps(created_figure, ensure_ascii=False, indent=2))
    print()
    
    # 保存新创建的人物ID用于后续测试
    figure_id = created_figure["id"]
    
    # 3. 测试获取特定历史人物
    print(f"3. 获取ID为{figure_id}的历史人物:")
    response = requests.get(f"{BASE_URL}/{figure_id}")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()
    
    # 4. 测试更新历史人物
    print(f"4. 更新ID为{figure_id}的历史人物:")
    update_data = {
        "role": "更新后的角色",
        "status": "offline"
    }
    response = requests.put(f"{BASE_URL}/{figure_id}", json=update_data)
    updated_figure = response.json()
    print(json.dumps(updated_figure, ensure_ascii=False, indent=2))
    print()
    
    # 5. 再次获取确认更新
    print(f"5. 确认ID为{figure_id}的历史人物已更新:")
    response = requests.get(f"{BASE_URL}/{figure_id}")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()
    
    # 6. 测试删除历史人物
    print(f"6. 删除ID为{figure_id}的历史人物:")
    response = requests.delete(f"{BASE_URL}/{figure_id}")
    print(response.json())
    print()
    
    # 7. 确认删除
    print(f"7. 确认ID为{figure_id}的历史人物已被删除:")
    response = requests.get(f"{BASE_URL}/{figure_id}")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()
    
    print("=== 所有测试完成 ===")

if __name__ == "__main__":
    test_api()