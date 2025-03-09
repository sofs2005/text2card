# Text2Card 渲染器使用说明

本文档介绍如何使用 Text2Card 渲染器将带有颜色标签的 Markdown 文本转换为图片。

## 背景

原始的 `pil_renderer.py` 存在一些语法错误和颜色渲染问题。我们创建了一个新的简化版渲染器 `simple_renderer.py`，它能够正确处理颜色标签和基本的 Markdown 格式。

## 如何使用

### 基本用法

```python
from simple_renderer import generate_image

# 准备文本
text = """# 标题

<span style="color:red">红色文本</span> 和 <span style="color:blue">蓝色文本</span>

—By 飞天
"""

# 生成图片
output_path = "output.png"
generate_image(text, output_path)
```

### 支持的特性

1. **颜色标签**：使用 HTML 样式标签
   ```
   <span style="color:red">红色文本</span>
   <span style="color:blue">蓝色文本</span>
   <span style="color:green">绿色文本</span>
   <span style="color:purple">紫色文本</span>
   <span style="color:orange">橙色文本</span>
   <span style="color:coral">珊瑚色文本</span>
   <span style="color:teal">青色文本</span>
   ```

2. **基本 Markdown 格式**：
   - 标题：`# 标题1`, `## 标题2`
   - 表格：使用 `|` 分隔的表格
   - 代码块：使用 ``` 包围的代码块

3. **组合使用**：颜色标签可以与 Markdown 格式结合使用
   ```
   <span style="color:red">**红色粗体**</span>
   <span style="color:blue">*蓝色斜体*</span>
   ```

4. **表格中的颜色**：
   ```
   | 产品 | 状态 | 价格 |
   |-----|-----|-----|
   | 商品A | <span style="color:red">重要商品</span> | ¥299 |
   | 商品B | <span style="color:green">促销商品</span> | ¥99 |
   ```

## 示例

以下是一个完整的示例，展示如何使用颜色标签和 Markdown 格式：

```python
from simple_renderer import generate_image

text = """# Markdown与颜色混合测试

<span style="color:red">红色文本</span> 和 <span style="color:blue">蓝色文本</span>

<span style="color:green">绿色文本</span> 和 <span style="color:purple">紫色文本</span>

## 表格测试

| 产品 | 状态 | 价格 |
|-----|-----|-----|
| 商品A | <span style="color:red">重要商品</span> | ¥299 |
| 商品B | <span style="color:green">促销商品</span> | ¥99 |

—By 飞天
"""

output_path = "example_output.png"
generate_image(text, output_path)
print(f"图片已保存到: {output_path}")
```

## 注意事项

1. 确保颜色标签格式正确：`<span style="color:colorname">文本</span>`
2. 颜色名称可以使用标准 HTML 颜色名称或十六进制颜色代码 (如 `#FF0000`)
3. 渲染器已优化处理中文文本和 emoji 表情符号

## 故障排除

如果遇到渲染问题：

1. 检查颜色标签语法是否正确
2. 确保标签闭合，每个开标签 `<span>` 都有对应的闭标签 `</span>`
3. 对于复杂的 Markdown 格式，尝试将内容分解为更简单的部分进行测试

## 更新日志

- **2023-07-10**: 创建简化版渲染器，修复颜色渲染问题
- **2023-07-11**: 优化表格渲染
- **2023-07-12**: 添加对更多颜色的支持 