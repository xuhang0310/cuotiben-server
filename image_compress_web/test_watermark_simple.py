#!/usr/bin/env python3
"""
简单测试脚本 - 全自动水印检测与去除

用法:
    cd image_compress_web

    # 1. 测试单张图片（全自动检测+去除）
    python3 test_watermark_simple.py /path/to/image.jpg

    # 2. 只检测不去除
    python3 test_watermark_simple.py /path/to/image.jpg --detect-only

    # 3. 快速模式（使用预设位置，跳过检测）
    python3 test_watermark_simple.py /path/to/image.jpg --quick

    # 4. 批量处理文件夹
    python3 test_watermark_simple.py /path/to/folder --batch
"""

import sys
import os
import argparse

# 确保能导入 watermark 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watermark import AutoWatermarkRemover, QuickWatermarkRemover


def main():
    parser = argparse.ArgumentParser(description='水印检测与去除测试')
    parser.add_argument('path', help='图片或文件夹路径')
    parser.add_argument('--detect-only', action='store_true', help='仅检测不去除')
    parser.add_argument('--quick', action='store_true', help='快速模式（跳过检测）')
    parser.add_argument('--batch', action='store_true', help='批量处理文件夹')
    parser.add_argument('--preset', default='doubao_bottom_right',
                        help='预设位置: doubao_bottom_right, doubao_large, wenxin_bottom')

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"❌ 路径不存在: {args.path}")
        return

    # 批量处理
    if args.batch or os.path.isdir(args.path):
        print(f"📁 批量处理文件夹: {args.path}")
        remover = AutoWatermarkRemover()
        output_folder = os.path.join(args.path, "output")

        task = remover.batch_remove(args.path, output_folder)
        print(f"🚀 任务已启动: {task.task_id}")
        print("⏳ 处理中...")

        import time
        while task.status in ["pending", "processing"]:
            time.sleep(0.5)
            task = remover.get_task(task.task_id)
            if task.total_files > 0:
                pct = task.processed / task.total_files * 100
                print(f"  进度: {task.processed}/{task.total_files} ({pct:.1f}%) "
                      f"✓{task.successful} ⏭{task.skipped} ✗{task.failed}", end="\r")

        print(f"\n✅ 完成! 成功:{task.successful} 跳过:{task.skipped} 失败:{task.failed}")
        print(f"📂 输出目录: {output_folder}")
        return

    # 单张处理
    input_path = args.path
    output_path = os.path.join("/Users/xupei/Downloads/", f"removed_{os.path.basename(input_path)}")

    # 仅检测
    if args.detect_only:
        print(f"🔍 检测水印: {input_path}")
        from watermark.detector import WatermarkDetector
        import cv2
        from PIL import Image
        import numpy as np

        detector = WatermarkDetector()
        result = detector.detect_file(input_path)

        if result.success:
            print(f"✅ 检测到水印!")
            print(f"   区域: {result.bbox}")
            print(f"   置信度: {result.confidence:.2%}")
            print(f"   模式: {result.mode}")
            print(f"   检测策略: {', '.join(result.contributors)}")

            # 保存可视化
            vis_path = "/tmp/detection_result.jpg"
            pil_img = Image.open(input_path)
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            detector.visualize_detection(image, result, save_path=vis_path)
            print(f"📷 可视化结果: {vis_path}")
        else:
            print(f"❌ 未检测到水印: {result.reason}")
        return

    # 快速模式
    if args.quick:
        print(f"⚡ 快速去除（{args.preset}）: {input_path}")
        remover = QuickWatermarkRemover(preset=args.preset)
        success = remover.remove(input_path, output_path)

        if success:
            print(f"✅ 完成! 输出: {output_path}")
        else:
            print(f"❌ 处理失败")
        return

    # 全自动模式
    print(f"🤖 全自动水印去除: {input_path}")
    remover = AutoWatermarkRemover()
    result = remover.remove(input_path, output_path, visualize=True)

    if result['success']:
        det = result['detection']
        print(f"✅ 完成!")
        print(f"   检测区域: {det['bbox']}")
        print(f"   置信度: {det['confidence']:.2%}")
        print(f"   处理时间: {result['processing_time']:.2f}s")
        print(f"   输出文件: {output_path}")
        if result.get('visualization_path'):
            print(f"📷 可视化: {result['visualization_path']}")
    else:
        print(f"❌ 失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
