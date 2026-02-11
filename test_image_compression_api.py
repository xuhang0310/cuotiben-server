"""
测试图片压缩API
"""
import requests
import os
from PIL import Image
import io

# API基础URL
BASE_URL = "http://localhost:8000"


def create_test_image(filename="test_image.jpg", size=(2000, 1500), color=(73, 109, 137)):
    """
    创建一个测试图片
    """
    img = Image.new('RGB', size, color)
    img.save(filename, "JPEG")
    print(f"创建测试图片: {filename}, 尺寸: {size}")
    return filename


def test_compress_to_size():
    """
    测试压缩到指定大小功能
    """
    print("\n=== 测试压缩到指定大小功能 ===")
    
    # 创建测试图片
    test_image_path = create_test_image("test_large_image.jpg", (2000, 1500))
    
    # 准备要上传的文件
    with open(test_image_path, 'rb') as f:
        # 使用元组格式来指定文件名和内容，让requests自动检测正确的MIME类型
        files = {'file': (os.path.basename(test_image_path), f, 'image/jpeg')}
        data = {'target_size_kb': 512}  # 压缩到512KB
        
        try:
            response = requests.post(f"{BASE_URL}/api/image-compression/compress-to-size/", files=files, data=data)
            
            if response.status_code == 200:
                print(f"[SUCCESS] 压缩成功！状态码: {response.status_code}")
                
                # 保存压缩后的图片
                output_filename = "compressed_output.jpg"
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                # 检查压缩后文件大小
                compressed_size = os.path.getsize(output_filename) / 1024  # KB
                print(f"压缩后文件大小: {compressed_size:.2f} KB")
                
                # 检查原始文件大小
                original_size = os.path.getsize(test_image_path) / 1024  # KB
                print(f"原始文件大小: {original_size:.2f} KB")
                
                print(f"压缩率: {((original_size - compressed_size) / original_size) * 100:.2f}%")
            else:
                print(f"[ERROR] 压缩失败！状态码: {response.status_code}, 错误信息: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}")
    
    # 清理测试文件
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"已清理测试文件: {test_image_path}")


def test_resize_by_percentage():
    """
    测试按百分比缩放功能
    """
    print("\n=== 测试按百分比缩放功能 ===")
    
    # 创建测试图片
    test_image_path = create_test_image("test_scale_image.jpg", (1000, 800))
    
    # 准备要上传的文件
    with open(test_image_path, 'rb') as f:
        # 使用元组格式来指定文件名和内容，让requests自动检测正确的MIME类型
        files = {'file': (os.path.basename(test_image_path), f, 'image/jpeg')}
        data = {'scale_factor': 0.5}  # 缩放到50%
        
        try:
            response = requests.post(f"{BASE_URL}/api/image-compression/resize-by-percentage/", files=files, data=data)
            
            if response.status_code == 200:
                print(f"[SUCCESS] 缩放成功！状态码: {response.status_code}")
                
                # 保存缩放后的图片
                output_filename = "scaled_output.jpg"
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                # 检查缩放后文件大小
                scaled_size = os.path.getsize(output_filename) / 1024  # KB
                print(f"缩放后文件大小: {scaled_size:.2f} KB")
                
                # 检查原始文件大小
                original_size = os.path.getsize(test_image_path) / 1024  # KB
                print(f"原始文件大小: {original_size:.2f} KB")
                
            else:
                print(f"[ERROR] 缩放失败！状态码: {response.status_code}, 错误信息: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}")
    
    # 清理测试文件
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"已清理测试文件: {test_image_path}")


def test_compress_by_dimensions():
    """
    测试按尺寸压缩功能
    """
    print("\n=== 测试按尺寸压缩功能 ===")
    
    # 创建测试图片
    test_image_path = create_test_image("test_dimension_image.jpg", (3000, 2000))
    
    # 准备要上传的文件
    with open(test_image_path, 'rb') as f:
        # 使用元组格式来指定文件名和内容，让requests自动检测正确的MIME类型
        files = {'file': (os.path.basename(test_image_path), f, 'image/jpeg')}
        data = {
            'max_width': 1024,
            'max_height': 768
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/image-compression/compress-by-dimensions/", files=files, data=data)
            
            if response.status_code == 200:
                print(f"[SUCCESS] 按尺寸压缩成功！状态码: {response.status_code}")
                
                # 保存压缩后的图片
                output_filename = "dimension_compressed_output.jpg"
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                # 检查压缩后文件大小
                compressed_size = os.path.getsize(output_filename) / 1024  # KB
                print(f"压缩后文件大小: {compressed_size:.2f} KB")
                
                # 检查原始文件大小
                original_size = os.path.getsize(test_image_path) / 1024  # KB
                print(f"原始文件大小: {original_size:.2f} KB")
                
            else:
                print(f"[ERROR] 按尺寸压缩失败！状态码: {response.status_code}, 错误信息: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}")
    
    # 清理测试文件
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"已清理测试文件: {test_image_path}")


def test_get_image_info():
    """
    测试获取图片信息功能
    """
    print("\n=== 测试获取图片信息功能 ===")
    
    # 创建测试图片
    test_image_path = create_test_image("test_info_image.jpg", (800, 600))
    
    # 准备要上传的文件
    with open(test_image_path, 'rb') as f:
        # 使用元组格式来指定文件名和内容，让requests自动检测正确的MIME类型
        files = {'file': (os.path.basename(test_image_path), f, 'image/jpeg')}
        
        try:
            response = requests.post(f"{BASE_URL}/api/image-compression/info/", files=files)
            
            if response.status_code == 200:
                print(f"[SUCCESS] 获取图片信息成功！状态码: {response.status_code}")
                info = response.json()
                print(f"图片信息: {info}")
            else:
                print(f"[ERROR] 获取图片信息失败！状态码: {response.status_code}, 错误信息: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}")
    
    # 清理测试文件
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"已清理测试文件: {test_image_path}")


if __name__ == "__main__":
    print("开始测试图片压缩API...")
    
    # 确保服务器正在运行
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print("[SUCCESS] 服务器连接正常")
        else:
            print("[ERROR] 服务器连接异常，请确保服务器已在运行")
            exit(1)
    except requests.ConnectionError:
        print("[ERROR] 无法连接到服务器，请确保服务器已在运行")
        exit(1)
    
    # 执行各项测试
    test_compress_to_size()
    test_resize_by_percentage()
    test_compress_by_dimensions()
    test_get_image_info()
    
    print("\n所有测试完成！")