#!/usr/bin/env python3
"""
测试增强的 OpenCV 修复效果
对比原图和修复后的效果
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from watermark.removal.adaptive import AdaptiveRemovalConfig, RemovalConfig
from watermark.removal.lama_inpainting import HybridInpainter


def create_test_image():
    """创建测试图片（模拟带水印的图片）"""
    # 创建一个渐变色背景的图片
    h, w = 600, 800
    image = np.zeros((h, w, 3), dtype=np.uint8)

    # 创建渐变背景
    for y in range(h):
        for x in range(w):
            image[y, x] = [
                int(100 + (x / w) * 100),
                int(150 + (y / h) * 50),
                int(200 - (x / w) * 50)
            ]

    # 添加一些纹理
    noise = np.random.normal(0, 5, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return image


def add_watermark(image, text="WATERMARK"):
    """在图片右下角添加模拟水印"""
    result = image.copy()
    h, w = result.shape[:2]

    # 水印区域（右下角）
    wm_w, wm_h = 200, 60
    x1, y1 = w - wm_w - 20, h - wm_h - 20
    x2, y2 = x1 + wm_w, y1 + wm_h

    # 绘制半透明背景
    overlay = result.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 100, 100), -1)
    cv2.addWeighted(overlay, 0.6, result, 0.4, 0, result)

    # 绘制文字
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(result, text, (x1 + 20, y1 + 40), font, 1, (255, 255, 255), 2)

    return result, (x1, y1, x2, y2)


def test_inpainting():
    """测试修复效果"""
    print("=" * 60)
    print("测试增强 OpenCV 修复效果")
    print("=" * 60)

    # 创建测试图片
    print("\n1. 创建测试图片...")
    original = create_test_image()
    watermarked, bbox = add_watermark(original)

    # 保存原图
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    cv2.imwrite(str(output_dir / "1_original.jpg"), original)
    cv2.imwrite(str(output_dir / "2_watermarked.jpg"), watermarked)
    print(f"   原图已保存到: {output_dir / '1_original.jpg'}")
    print(f"   带水印图已保存到: {output_dir / '2_watermarked.jpg'}")

    # 创建修复器
    print("\n2. 初始化修复器...")
    inpainter = HybridInpainter(device="cpu")
    print(f"   LaMa 可用: {inpainter.lama.is_available()}")

    # 获取自适应配置
    print("\n3. 获取自适应配置...")
    config = AdaptiveRemovalConfig.get_config(
        (watermarked.shape[1], watermarked.shape[0]),
        bbox,
        mode="normal",
        confidence=0.85
    )
    print(f"   算法: {config.algorithm}")
    print(f"   修复半径: {config.inpaint_radius}")
    print(f"   羽化半径: {config.feather_radius}")
    print(f"   膨胀次数: {config.dilation_iterations}")

    # 创建掩码
    print("\n4. 创建修复掩码...")
    mask = AdaptiveRemovalConfig.create_optimized_mask(
        watermarked.shape,
        bbox,
        config.feather_radius,
        config.dilation_iterations
    )
    cv2.imwrite(str(output_dir / "3_mask.jpg"), mask)
    print(f"   掩码已保存到: {output_dir / '3_mask.jpg'}")

    # 执行修复
    print("\n5. 执行修复...")
    success, result = inpainter.inpaint(
        watermarked,
        mask,
        use_lama=False  # 强制使用 OpenCV
    )

    if success:
        cv2.imwrite(str(output_dir / "4_repaired.jpg"), result)
        print(f"   修复完成，已保存到: {output_dir / '4_repaired.jpg'}")
        print(f"   是否降级: {inpainter.fallback_used}")
    else:
        print("   修复失败!")
        return

    # 计算质量指标
    print("\n6. 计算质量指标...")
    # 裁剪出水印区域
    x1, y1, x2, y2 = bbox
    # 扩大区域以便观察边缘
    pad = 20
    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
    x2, y2 = min(watermarked.shape[1], x2 + pad), min(watermarked.shape[0], y2 + pad)

    orig_region = original[y1:y2, x1:x2]
    watermarked_region = watermarked[y1:y2, x1:x2]
    result_region = result[y1:y2, x1:x2]

    # 保存对比图
    comparison = np.hstack([orig_region, watermarked_region, result_region])
    cv2.imwrite(str(output_dir / "5_comparison.jpg"), comparison)
    print(f"   对比图已保存到: {output_dir / '5_comparison.jpg'}")

    # 计算 PSNR
    mse_watermarked = np.mean((orig_region.astype(float) - watermarked_region.astype(float)) ** 2)
    mse_result = np.mean((orig_region.astype(float) - result_region.astype(float)) ** 2)

    if mse_watermarked > 0:
        psnr_watermarked = 20 * np.log10(255.0 / np.sqrt(mse_watermarked))
    else:
        psnr_watermarked = float('inf')

    if mse_result > 0:
        psnr_result = 20 * np.log10(255.0 / np.sqrt(mse_result))
    else:
        psnr_result = float('inf')

    print(f"\n   PSNR (带水印): {psnr_watermarked:.2f} dB")
    print(f"   PSNR (修复后): {psnr_result:.2f} dB")
    print(f"   改善: {psnr_result - psnr_watermarked:+.2f} dB")

    print("\n" + "=" * 60)
    print("测试完成!")
    print(f"输出文件目录: {output_dir.absolute()}")
    print("=" * 60)


def test_transparent_png():
    """测试透明 PNG 的处理"""
    print("\n" + "=" * 60)
    print("测试透明 PNG 处理")
    print("=" * 60)

    from PIL import Image

    # 创建带透明的测试图片
    w, h = 400, 300
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    # 绘制一些内容
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, h], fill=(100, 150, 200, 255))
    draw.ellipse([50, 50, 150, 150], fill=(255, 100, 100, 200))

    # 添加模拟水印（右下角）
    draw.rectangle([w-150, h-50, w-10, h-10], fill=(50, 50, 50, 180))

    # 保存
    output_dir = Path("test_output")
    img.save(output_dir / "transparent_original.png")
    print(f"   透明原图已保存")

    # 测试 wrapper
    from watermark.removal.wrapper import WatermarkRemoverWrapper

    remover = WatermarkRemoverWrapper(device="cpu")

    input_path = output_dir / "transparent_original.png"
    output_path = output_dir / "transparent_repaired.png"

    result = remover.remove_file(
        str(input_path),
        str(output_path),
        bbox=(w-160, h-60, w, h),
        mode="normal"
    )

    if result['success']:
        print(f"   修复完成: {output_path}")

        # 验证透明通道
        result_img = Image.open(output_path)
        print(f"   输出模式: {result_img.mode}")
        if result_img.mode == 'RGBA':
            alpha = result_img.split()[3]
            print(f"   透明通道范围: {min(alpha.getdata())} - {max(alpha.getdata())}")
    else:
        print(f"   修复失败: {result.get('error')}")


if __name__ == "__main__":
    test_inpainting()
    test_transparent_png()
