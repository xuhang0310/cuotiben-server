# 图片压缩工具使用指南

## 概述

图片压缩工具是一个用于将图片压缩至指定大小的实用程序，主要功能是将图片压缩至512KB以内，以节省存储空间和加快加载速度。

## 功能特性

1. **按大小压缩**：将图片压缩至指定大小（默认512KB）
2. **按比例缩放**：按百分比缩放图片尺寸
3. **按尺寸限制**：限制图片的最大宽度和高度
4. **格式兼容**：支持JPEG、PNG等多种常见图片格式
5. **透明度保留**：正确处理PNG等支持透明度的图片格式

## 主要函数

### `compress_image_to_size(image_input, target_size_kb=512, quality_step=5, max_iterations=20)`

将图片压缩至目标大小

**参数：**
- `image_input`: 图片输入，可以是文件路径、字节数据或BytesIO对象
- `target_size_kb`: 目标大小（KB），默认512KB
- `quality_step`: JPEG质量调整步长，默认5
- `max_iterations`: 最大迭代次数，默认20

**返回值：**
- `bytes`: 压缩后的图片字节数据

### `resize_image_by_percentage(image_input, scale_factor)`

按百分比缩放图片

**参数：**
- `image_input`: 图片输入
- `scale_factor`: 缩放因子 (例如 0.8 表示缩小到80%)

**返回值：**
- `bytes`: 缩放后的图片字节数据

### `get_image_info(image_input)`

获取图片信息

**参数：**
- `image_input`: 图片输入

**返回值：**
- `dict`: 包含图片信息的字典，如宽高、模式、格式、大小等

### `compress_image_by_dimensions(image_input, max_width=1920, max_height=1080)`

按最大尺寸限制压缩图片

**参数：**
- `image_input`: 图片输入
- `max_width`: 最大宽度，默认1920
- `max_height`: 最大高度，默认1080

**返回值：**
- `bytes`: 压缩后的图片字节数据

## 使用示例

### 基本用法

```python
from app.utils.image_compression import compress_image_to_size

# 压缩本地图片文件到512KB
with open('path/to/image.jpg', 'rb') as f:
    image_data = f.read()
    
compressed_data = compress_image_to_size(image_data, target_size_kb=512)

# 保存压缩后的图片
with open('path/to/compressed_image.jpg', 'wb') as f:
    f.write(compressed_data)
```

### 在上传处理中使用

```python
from app.utils.image_upload import ImageUploadUtil

# ImageUploadUtil现在会在上传时自动将图片压缩到512KB以内
upload_util = ImageUploadUtil()
url = await upload_util.upload_image(upload_file)
```

### 获取图片信息

```python
from app.utils.image_compression import get_image_info

info = get_image_info('path/to/image.jpg')
print(f"图片尺寸: {info['width']}x{info['height']}")
print(f"图片大小: {info['size_kb']}KB")
```

## 注意事项

1. 压缩过程可能会损失部分图片质量，但会尽量保持视觉效果
2. 对于已经很小的图片，压缩可能不会显著减小文件大小
3. 包含透明度的PNG图片会被正确处理并保留透明度
4. 压缩算法会优先降低JPEG质量，然后才缩小图片尺寸