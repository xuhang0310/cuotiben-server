import io
from PIL import Image
import numpy as np

def mock_ocr_recognize(image_data):
    """
    模拟OCR识别功能
    在实际项目中，这里会调用OCR引擎进行识别
    """
    # 模拟OCR识别结果
    recognized_text = """这是一道数学题：

**题目：**
已知函数 f(x) = x² - 4x + 3，求：
1. 函数的零点
2. 函数的最小值
3. 函数在区间 [0, 5] 上的最大值

**解答：**
1. 求零点：令 f(x) = 0
   x² - 4x + 3 = 0
   (x - 1)(x - 3) = 0
   所以零点为 x = 1 和 x = 3

2. 求最小值：
   f(x) = x² - 4x + 3 = (x - 2)² - 1
   当 x = 2 时，函数取得最小值 -1

3. 求区间 [0, 5] 上的最大值：
   由于函数开口向上，对称轴为 x = 2
   在区间 [0, 5] 上，比较端点值：
   f(0) = 3
   f(5) = 25 - 20 + 3 = 8
   所以最大值为 8"""
    
    return recognized_text

def paddle_ocr_recognize(image_data):
    """
    使用飞桨OCR进行识别
    """
    try:
        # 导入飞桨OCR模块（延迟导入，避免启动时依赖）
        from paddleocr import PaddleOCR
        
        # 初始化OCR引擎（首次运行会自动下载模型）
        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        
        # 将图像数据转换为PIL Image对象
        image = Image.open(io.BytesIO(image_data))
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 执行OCR识别
        result = ocr.ocr(img_array, cls=True)
        
        # 提取识别文本
        recognized_text = ""
        if result is not None:
            for idx, res in enumerate(result):
                if res is not None:
                    for line in res:
                        if line[1] is not None:
                            recognized_text += line[1][0] + "\n"
        
        return recognized_text if recognized_text else "未识别到文本内容"
        
    except Exception as e:
        # 如果飞桨OCR不可用，回退到模拟识别
        print(f"飞桨OCR识别失败，使用模拟识别: {e}")
        return mock_ocr_recognize(image_data)