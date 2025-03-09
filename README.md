# Text2Card - Markdown卡片渲染工具

将Markdown文本渲染为精美卡片图片的工具，支持彩色文本、混合格式列表和任务列表，具有美观的卡片样式效果。

## 特性

- 🎨 **精美卡片样式** - 渐变背景、毛玻璃效果、圆角边框
- 🌈 **彩色文本支持** - 使用HTML span标签添加颜色
- 🔤 **混合格式文本** - 支持彩色+粗体/斜体组合
- ✅ **任务列表** - 支持带复选框的任务列表
- 📱 **响应式设计** - 自动调整卡片尺寸适配内容
- 🌙 **自动主题** - 根据时间自动选择明暗主题
- 🚀 **API支持** - 提供HTTP API便于集成到其他系统

## 安装

### 系统要求

- Python 3.7+
- 所需字体文件(目录中已包含):
  - msyh.ttc (微软雅黑)
  - msyhbd.ttc (微软雅黑粗体)
  - TwitterColorEmoji.ttf (emoji字体)

### 依赖安装

```bash
pip install -r requirements.txt
```

## 使用方法

### Python直接调用

```python
from enhanced_renderer import render_markdown_to_image

# 渲染Markdown文本到图片
markdown_text = """
# 标题
这是一个<span style="color:red">彩色</span>的Markdown示例

- 列表项1
- 列表项2
- [x] 已完成任务
- [ ] 未完成任务
"""

render_markdown_to_image(markdown_text, "output.png")
```

### API服务

1. 启动API服务器：

```bash
python api_server.py
```

2. 发送API请求：

```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{"markdown_text": "# 标题\n这是内容"}' \
  --output image.png
```

3. 或者打开`demo.html`使用网页演示界面

## Markdown格式示例

### 彩色文本

```markdown
这是<span style="color:red">红色</span>文本
这是<span style="color:blue">蓝色</span>文本
这是<span style="color:green">绿色</span>文本
```

### 混合格式

```markdown
<span style="color:red">**红色粗体**</span>
<span style="color:blue">*蓝色斜体*</span>
```

### 任务列表

```markdown
- [x] 已完成任务
- [ ] 未完成任务
- [x] <span style="color:green">彩色任务</span>
```

## 项目文件

- `enhanced_renderer.py` - 核心渲染引擎
- `api_server.py` - API服务器
- `test_api.py` - API测试脚本
- `demo.html` - 网页演示界面
- `msyh.ttc` - 微软雅黑字体
- `msyhbd.ttc` - 微软雅黑粗体
- `TwitterColorEmoji.ttf` - Twitter Emoji字体

## 许可证

MIT
