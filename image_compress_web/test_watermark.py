#!/usr/bin/env python3
"""
水印检测器测试脚本

使用方法:
    python test_watermark.py --image path/to/image.jpg
    python test_watermark.py --batch path/to/folder
"""

import os
import sys
import argparse
from pathlib import Path

# 导入水印模块
from watermark import AutoWatermarkRemover, QuickWatermarkRemover


def test_detection(image_path: str, visualize: bool = True):
    """测试水印检测"""
    print(f"\n{'='*60}")
    print(f"测试水印检测: {image_path}")
    print('='*60)

    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 {image_path}")
        return

    from watermark.detector import WatermarkDetector
    detector = WatermarkDetector()

    print("开始检测...")
    result = detector.detect_file(image_path)

    print(f"\n检测结果:")
    print(f"  成功: {result.success}")

    if result.success:
        print(f"  水印区域: {result.bbox}")
        print(f"  置信度: {result.confidence:.4f}")
        print(f"  模式: {result.mode}")
        print(f"  贡献策略: {result.contributors}")

        if result.all_results:
            print(f"\n  各策略检测结果:")
            for strategy, detections in result.all_results.items():
                print(f"    {strategy}:")
                for d in detections[:3]:  # 只显示前3个
                    print(f"      - {d.method}: bbox={d.bbox}, conf={d.confidence:.4f}")
    else:
        print(f"  失败原因: {result.reason}")

    # 可视化
    if visualize and result.success:
        import cv2
        import numpy as np
        from PIL import Image

        vis_path = f"/tmp/detection_vis_{Path(image_path).stem}.jpg"

        pil_img = Image.open(image_path)
        image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        detector.visualize_detection(image, result, save_path=vis_path)
        print(f"\n  可视化结果已保存: {vis_path}")

    return result


def test_removal(image_path: str, output_path: str = None):
    """测试水印去除"""
    print(f"\n{'='*60}")
    print(f"测试水印去除: {image_path}")
    print('='*60)

    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 {image_path}")
        return

    remover = AutoWatermarkRemover()

    if output_path is None:
        output_path = f"/tmp/removed_{Path(image_path).name}"

    print("开始处理...")
    result = remover.remove(
        image_path,
        output_path,
        visualize=True
    )

    print(f"\n处理结果:")
    print(f"  成功: {result['success']}")

    if result['success']:
        print(f"  检测区域: {result['detection'].get('bbox')}")
        print(f"  置信度: {result['detection'].get('confidence')}")
        print(f"  处理时间: {result['processing_time']:.3f}s")
        print(f"  输出文件: {result['output_path']}")

        if result.get('visualization_path'):
            print(f"  可视化: {result['visualization_path']}")
    else:
        print(f"  错误: {result.get('error')}")

    return result


def test_quick_removal(image_path: str, preset: str = "doubao_bottom_right"):
    """测试快速去除"""
    print(f"\n{'='*60}")
    print(f"测试快速去除 ({preset}): {image_path}")
    print('='*60)

    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 {image_path}")
        return

    remover = QuickWatermarkRemover(preset=preset)
    output_path = f"/tmp/quick_removed_{Path(image_path).name}"

    print("开始处理...")
    success = remover.remove(image_path, output_path)

    print(f"\n处理结果:")
    print(f"  成功: {success}")
    print(f"  输出文件: {output_path}")

    return success


def test_batch(folder_path: str):
    """测试批量处理"""
    print(f"\n{'='*60}")
    print(f"测试批量处理: {folder_path}")
    print('='*60)

    if not os.path.exists(folder_path):
        print(f"错误: 文件夹不存在 {folder_path}")
        return

    remover = AutoWatermarkRemover()
    output_folder = "/tmp/batch_output"

    os.makedirs(output_folder, exist_ok=True)

    print("启动批量任务...")
    task = remover.batch_remove(folder_path, output_folder)

    print(f"\n任务信息:")
    print(f"  任务ID: {task.task_id}")
    print(f"  状态: {task.status}")

    # 等待完成
    print("\n等待处理完成...")
    import time

    while task.status == "processing" or task.status == "pending":
        time.sleep(1)
        task = remover.get_task(task.task_id)
        if task.processed > 0:
            print(f"  进度: {task.processed}/{task.total_files} "
                  f"(成功:{task.successful}, 跳过:{task.skipped}, 失败:{task.failed})")

    print(f"\n最终结果:")
    print(f"  状态: {task.status}")
    print(f"  总文件: {task.total_files}")
    print(f"  成功: {task.successful}")
    print(f"  跳过: {task.skipped}")
    print(f"  失败: {task.failed}")
    print(f"  平均置信度: {task.average_confidence:.4f}")

    return task


def main():
    parser = argparse.ArgumentParser(description='水印检测与去除测试')
    parser.add_argument('--image', type=str, help='测试单张图片')
    parser.add_argument('--batch', type=str, help='测试批量处理')
    parser.add_argument('--detect-only', action='store_true', help='仅检测')
    parser.add_argument('--quick', action='store_true', help='使用快速模式')
    parser.add_argument('--preset', type=str, default='doubao_bottom_right',
                        help='快速模式预设: doubao_bottom_right, doubao_large, wenxin_bottom')

    args = parser.parse_args()

    if args.image:
        if args.detect_only:
            test_detection(args.image)
        elif args.quick:
            test_quick_removal(args.image, args.preset)
        else:
            test_removal(args.image)
    elif args.batch:
        test_batch(args.batch)
    else:
        parser.print_help()
        print("\n示例:")
        print("  python test_watermark.py --image test.jpg --detect-only")
        print("  python test_watermark.py --image test.jpg")
        print("  python test_watermark.py --image test.jpg --quick")
        print("  python test_watermark.py --batch ./images")


if __name__ == "__main__":
    main()
