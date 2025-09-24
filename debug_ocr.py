#!/usr/bin/env python3
"""
OCR 调试脚本
"""

import os
from app.utils.ocr import paddle_ocr_recognize, mock_ocr_recognize

def test_ocr_with_image(image_path):
    """测试 OCR 识别图片"""
    if not os.path.exists(image_path):
        print(f"图片文件不存在: {image_path}")
        return
    
    print(f"正在读取图片: {image_path}")
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    print("调用 OCR 识别...")
    try:
        result = paddle_ocr_recognize(image_data)
        print("OCR 识别结果:")
        print(result)
    except Exception as e:
        print(f"OCR 识别出错: {e}")
        import traceback
        traceback.print_exc()

def test_mock_ocr():
    """测试模拟 OCR"""
    print("测试模拟 OCR...")
    # 创建一些模拟的图像数据（这里只是简单示例）
    mock_image_data = b"fake image data"
    result = mock_ocr_recognize(mock_image_data)
    print("模拟 OCR 结果:")
    print(result)

if __name__ == "__main__":
    # 你可以在这里调用测试函数
    # test_mock_ocr()
    
    # 如果你有测试图片，可以使用下面的函数
    test_ocr_with_image("path/to/your/test/image.jpg")
    pass