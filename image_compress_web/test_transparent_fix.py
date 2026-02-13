#!/usr/bin/env python3
"""
测试透明PNG修复效果
验证水印去除后透明背景不再变黑
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from watermark.removal.wrapper import WatermarkRemoverWrapper
from watermark.removal.adaptive import RemovalConfig


def create_transparent_test_image():
    """创建带透明背景的测试图片"""
    w, h = 600, 400

    # 创建透明背景图
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    # 绘制背景图案（模拟透明PNG）
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # 绘制半透明彩色块
    for i in range(5):
        x = i * 120
        draw.rectangle([x, 0, x + 100, h], fill=(100 + i*30, 150, 200 - i*20, 180))

    # 绘制一些文字/内容
    draw.ellipse([100, 100, 200, 200], fill=(255, 100, 100, 220))
    draw.rectangle([350, 150, 450, 250], fill=(100, 255, 100, 220))

    return img


def add_watermark_transparent(img, text="WATERMARK"):
    """添加半透明水印"""
    result = img.copy()
    w, h = result.size
    from PIL import ImageDraw
    draw = ImageDraw.Draw(result)

    # 水印区域（右下角）
    wm_w, wm_h = 200, 50
    x1, y1 = w - wm_w - 20, h - wm_h - 20
    x2, y2 = x1 + wm_w, y1 + wm_h

    # 半透明水印背景
    watermark_overlay = Image.new('RGBA', result.size, (0, 0, 0, 0))
    wm_draw = ImageDraw.Draw(watermark_overlay)
    wm_draw.rectangle([x1, y1, x2, y2], fill=(50, 50, 50, 200))

    # 合并水印
    result = Image.alpha_composite(result, watermark_overlay)

    return result, (x1, y1, x2, y2)


def test_transparent_fix():
    """测试透明图修复"""
    print("=" * 60)
    print("测试透明PNG修复（验证不发黑）")
    print("=" * 60)

    # 创建测试图
    print("\n1. 创建透明测试图...")
    original = create_transparent_test_image()
    watermarked, bbox = add_watermark_transparent(original)

    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    # 保存原图
    original_path = output_dir / "trans_original.png"
    watermarked_path = output_dir / "trans_watermarked.png"

    original.save(original_path)
    watermarked.save(watermarked_path)

    print(f"   原图: {original_path}")
    print(f"   带水印: {watermarked_path}")

    # 检查原图Alpha
    orig_alpha = np.array(original.split()[3])
    water_alpha = np.array(watermarked.split()[3])
    print(f"\n2. 原图Alpha统计:")
    print(f"   透明区域: {np.sum(orig_alpha < 255)} 像素")
    print(f"   半透明区域(100-254): {np.sum((orig_alpha >= 100) & (orig_alpha < 255))} 像素")

    # 测试不同输出格式
    test_cases = [
        ("auto", "自动检测（应为PNG）"),
        ("png", "强制PNG无损"),
        ("jpeg", "强制JPEG有损"),
    ]

    remover = WatermarkRemoverWrapper(device="cpu")

    for fmt, desc in test_cases:
        print(f"\n3. 测试 {desc}...")

        output_path = output_dir / f"trans_repaired_{fmt}.png"

        config = RemovalConfig(output_format=fmt)

        result = remover.remove_file(
            str(watermarked_path),
            str(output_path),
            bbox=bbox,
            config=config
        )

        if result['success']:
            # 检查结果
            result_img = Image.open(output_path)
            print(f"   输出格式: {result_img.format}")
            print(f"   输出模式: {result_img.mode}")

            if result_img.mode == 'RGBA':
                result_alpha = np.array(result_img.split()[3])

                # 检查水印区域Alpha
                x1, y1, x2, y2 = bbox
                wm_alpha = result_alpha[y1:y2, x1:x2]

                print(f"   水印区域Alpha:")
                print(f"     - 最小值: {wm_alpha.min()}")
                print(f"     - 最大值: {wm_alpha.max()}")
                print(f"     - 平均值: {wm_alpha.mean():.1f}")
                print(f"     - 255(不透明)像素: {np.sum(wm_alpha == 255)} / {wm_alpha.size}")

                # 验证不发黑
                if wm_alpha.min() >= 200:
                    print(f"   ✅ 水印区域已变为不透明（不发黑）")
                else:
                    print(f"   ❌ 水印区域仍有透明像素")

                # 检查边缘是否平滑
                edge_pixels = np.sum((wm_alpha > 0) & (wm_alpha < 255))
                if edge_pixels > 0:
                    print(f"   ✅ 边缘羽化: {edge_pixels} 像素渐变")
            else:
                print(f"   JPEG输出无Alpha通道")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_transparent_fix()
