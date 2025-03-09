# 增强版Markdown渲染器

本文档介绍如何使用增强版Markdown渲染器，它能正确处理Markdown格式并支持颜色标签。

## 功能特点

1. **完整Markdown支持**：
   - 标题 (h1-h6)
   - 粗体、斜体、删除线
   - 有序列表和无序列表（包括嵌套列表）
   - 代码块和行内代码
   - 表格
   - 引用
   - 链接

2. **颜色支持**：
   - 使用HTML颜色标签 `<span style="color:red">红色文本</span>`
   - 支持各种标准HTML颜色名称和十六进制颜色代码

3. **混合格式**：
   - 可以在颜色标签内使用Markdown格式
   - 例如：`<span style="color:red">**红色粗体**</span>`

4. **文本边界控制**：
   - 自动文本换行，避免文本超出图片边界
   - 自动调整图片大小以适应内容

5. **Emoji支持**：
   - 支持在文本中使用Emoji表情符号

## 使用方法

```python
from enhanced_renderer import render_markdown_to_image

# Markdown文本
text = """# 标题

这是一个**粗体**和*斜体*文本的例子。

<span style="color:red">这是红色文本</span>

列表示例：
* 项目1
* 项目2

表格示例：
| 姓名 | 年龄 |
|------|------|
| 张三 | 20 |
| 李四 | 30 |

> 这是引用文本

"""

# 渲染并保存图片
output_path = "output.png"
render_markdown_to_image(text, output_path)
```

## 参数说明

`render_markdown_to_image` 函数接受以下参数：

- `markdown_text`：要渲染的Markdown文本
- `output_path`：输出图片的路径
- `width`：图片宽度，默认为1000像素
- `height`：图片高度，默认为自动计算（根据内容长度）

## 安装依赖

使用前需要安装以下依赖：

```
pip install markdown bs4 Pillow emoji
```

## 注意事项

1. 确保颜色标签格式正确：`<span style="color:colorname">文本</span>`
2. 颜色名称可以使用标准HTML颜色名称（如red, blue, green等）或十六进制颜色代码（如#FF0000）
3. 图片会自动剪裁，去除多余的空白区域

## 示例

参考 `test_markdown_elements_enhanced.py` 查看完整的示例。

## 进阶用法

### 自定义字体

```python
from enhanced_renderer import render_markdown_to_image
import os

# 自定义字体路径
os.environ['CUSTOM_FONT_PATH'] = '/path/to/your/font.ttf'

# 渲染文本
render_markdown_to_image(text, output_path)
```

### 调整图片尺寸

```python
# 指定宽度为1200像素，高度自动计算
render_markdown_to_image(text, output_path, width=1200)

# 指定固定宽度和高度
render_markdown_to_image(text, output_path, width=1200, height=1500)
``` 