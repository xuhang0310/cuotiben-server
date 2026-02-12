# advanced_watermark_remover_fixed.py
import os
import cv2
import numpy as np
from PIL import Image
import argparse
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"watermark_removal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def remove_watermark_advanced(input_path, output_path, right_margin_percent=5.0, bottom_margin_percent=5.0, 
                             watermark_width_percent=20.0, watermark_height_percent=10.0):
    """
    使用OpenCV的inpainting功能去除豆包生成图片的水印
    
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径
    :param right_margin_percent: 距离右边距的百分比
    :param bottom_margin_percent: 距离底边距的百分比
    :param watermark_width_percent: 水印宽度占图片宽度的百分比
    :param watermark_height_percent: 水印高度占图片高度的百分比
    :return: 成功返回True，失败返回False
    """
    try:
        logger.info(f"开始处理图片: {input_path}")
        
        # 使用PIL读取图片以处理中文路径
        try:
            pil_img = Image.open(input_path)
            # 转换为OpenCV格式
            img_np = np.array(pil_img)
            # 如果是RGBA模式，转换为BGR
            if pil_img.mode == 'RGBA':
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGRA)
            elif pil_img.mode == 'RGB':
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_np
        except Exception as e:
            logger.error(f"使用PIL读取图片失败 {input_path}: {str(e)}")
            return False
        
        h, w = img_cv.shape[:2]
        logger.info(f"图片尺寸: {w}x{h}")
        
        # 计算水印区域坐标
        watermark_right_start = int(w * (1 - right_margin_percent / 100.0))
        watermark_bottom_start = int(h * (1 - bottom_margin_percent / 100.0))
        watermark_left = int(w - w * (right_margin_percent / 100.0 + watermark_width_percent / 100.0))
        watermark_top = int(h - h * (bottom_margin_percent / 100.0 + watermark_height_percent / 100.0))
        
        # 确保坐标在有效范围内
        watermark_left = max(0, watermark_left)
        watermark_top = max(0, watermark_top)
        watermark_right_start = min(w, watermark_right_start)
        watermark_bottom_start = min(h, watermark_bottom_start)
        
        logger.info(f"水印区域坐标: 左={watermark_left}, 上={watermark_top}, 右={watermark_right_start}, 下={watermark_bottom_start}")
        
        # 检查水印区域是否有效
        if watermark_right_start <= watermark_left or watermark_bottom_start <= watermark_top:
            logger.warning(f"水印区域无效，可能是参数设置不当: {input_path}")
            # 使用默认的小区域作为备选方案
            watermark_left = max(0, w - 150)
            watermark_top = max(0, h - 50)
            watermark_right_start = w
            watermark_bottom_start = h
            logger.info(f"使用默认水印区域: 左={watermark_left}, 上={watermark_top}, 右={watermark_right_start}, 下={watermark_bottom_start}")
        
        # 创建掩码，标记要去除的区域
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[watermark_top:watermark_bottom_start, watermark_left:watermark_right_start] = 255
        
        # 记录掩码统计信息
        mask_area = np.sum(mask) / 255
        total_pixels = h * w
        mask_percentage = (mask_area / total_pixels) * 100
        logger.info(f"掩码覆盖面积: {mask_area} 像素 ({mask_percentage:.2f}% of image)")
        
        # 使用inpainting算法去除水印
        # 尝试不同的inpainting方法，选择效果最好的
        result = None
        try:
            # 方法1: Navier-Stokes based inpainting
            logger.info("尝试使用Navier-Stokes算法进行修复...")
            result = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_NS)
            logger.info("Navier-Stokes算法成功")
        except Exception as e:
            logger.warning(f"Navier-Stokes算法失败: {str(e)}")
            try:
                # 方法2: Telea algorithm
                logger.info("尝试使用Telea算法进行修复...")
                result = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_TELEA)
                logger.info("Telea算法成功")
            except Exception as e2:
                logger.error(f"Telea算法也失败: {str(e2)}")
                logger.error(f"两种inpainting方法都失败了 {input_path}")
                return False
        
        # 检查结果是否有效
        if result is None or result.size == 0:
            logger.error(f"修复结果无效 {input_path}")
            return False
        
        # 使用PIL保存结果以处理中文路径
        try:
            # 转换回PIL格式
            if len(result.shape) == 3:
                if result.shape[2] == 4:
                    result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGRA2RGBA))
                else:
                    result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
            else:
                result_pil = Image.fromarray(result)
            
            result_pil.save(output_path)
            success = True
        except Exception as e:
            logger.error(f"使用PIL保存图片失败 {output_path}: {str(e)}")
            success = False
        
        if success:
            logger.info(f"水印去除完成: {input_path} -> {output_path}")
            return True
        else:
            logger.error(f"保存结果失败: {output_path}")
            return False
            
    except Exception as e:
        logger.error(f"处理图片时发生未预期的错误 {input_path}: {str(e)}", exc_info=True)
        return False

def batch_remove_watermark_advanced(input_folder, output_folder, right_margin_percent=5.0, bottom_margin_percent=5.0, 
                                   watermark_width_percent=20.0, watermark_height_percent=10.0):
    """
    批量去除水印
    
    :param input_folder: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    :param right_margin_percent: 距离右边距的百分比
    :param bottom_margin_percent: 距离底边距的百分比
    :param watermark_width_percent: 水印宽度占图片宽度的百分比
    :param watermark_height_percent: 水印高度占图片高度的百分比
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 支持的图片格式
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
    
    # 统计信息
    total_files = 0
    successful_files = 0
    failed_files = 0
    
    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in supported_formats:
            total_files += 1
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"cleaned_{filename}")
            
            logger.info(f"正在处理 ({total_files}): {filename}")
            success = remove_watermark_advanced(
                input_path=input_path,
                output_path=output_path,
                right_margin_percent=right_margin_percent,
                bottom_margin_percent=bottom_margin_percent,
                watermark_width_percent=watermark_width_percent,
                watermark_height_percent=watermark_height_percent
            )
            
            if success:
                successful_files += 1
            else:
                failed_files += 1
                logger.error(f"处理失败: {filename}")
    
    logger.info(f"批量处理完成! 总计: {total_files}, 成功: {successful_files}, 失败: {failed_files}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="高级豆包图片水印去除工具（修复版）")
    parser.add_argument("--input", "-i", required=True, help="输入图片或文件夹路径")
    parser.add_argument("--output", "-o", required=True, help="输出图片或文件夹路径")
    parser.add_argument("--right-margin", "-rm", type=float, default=5.0, help="距离右边距的百分比 (默认: 5.0)")
    parser.add_argument("--bottom-margin", "-bm", type=float, default=5.0, help="距离底边距的百分比 (默认: 5.0)")
    parser.add_argument("--width-percent", "-wp", type=float, default=20.0, help="水印宽度占图片宽度的百分比 (默认: 20.0)")
    parser.add_argument("--height-percent", "-hp", type=float, default=10.0, help="水印高度占图片高度的百分比 (默认: 10.0)")
    
    args = parser.parse_args()
    
    # 检查输入路径是否存在
    if not os.path.exists(args.input):
        logger.error(f"输入路径不存在 - {args.input}")
        exit(1)
    
    # 判断输入是文件还是文件夹
    if os.path.isfile(args.input):
        # 单个文件处理
        logger.info(f"开始处理单个文件: {args.input}")
        success = remove_watermark_advanced(
            input_path=args.input,
            output_path=args.output,
            right_margin_percent=args.right_margin,
            bottom_margin_percent=args.bottom_margin,
            watermark_width_percent=args.width_percent,
            watermark_height_percent=args.height_percent
        )
        if success:
            logger.info("单文件处理成功")
        else:
            logger.error("单文件处理失败")
    elif os.path.isdir(args.input):
        # 批量处理文件夹
        logger.info(f"开始批量处理文件夹: {args.input}")
        batch_remove_watermark_advanced(
            input_folder=args.input,
            output_folder=args.output,
            right_margin_percent=args.right_margin,
            bottom_margin_percent=args.bottom_margin,
            watermark_width_percent=args.width_percent,
            watermark_height_percent=args.height_percent
        )
    else:
        logger.error(f"输入路径既不是文件也不是文件夹 - {args.input}")
        exit(1)