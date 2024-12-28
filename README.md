# 📝 Text2Card 项目说明

## ✅ 前言
Text2Card 是一个小而美的工具，能够将文本内容转换为精美的图片卡片。相比使用无头浏览器截图的方式，Text2Card 更加轻量，不依赖外部服务，直接通过函数调用生成图片，性能高效且易于集成。

## 🚀 功能特性
- **卡片多主题配色**：支持多种渐变背景配色，卡片风格多样。
- **Markdown解析渲染**：支持基本的Markdown语法解析，如标题、列表等。
- **日间夜间模式自动切换**：根据时间自动切换日间和夜间模式。
- **图片标题**：支持在卡片顶部添加图片标题。
- **支持emoji渲染展示**：能够正确渲染和展示emoji表情。
- **超清图片保存**：生成的图片清晰度高，适合分享和展示。
- **待完善功能**：
  - 复杂Markdown渲染（如表格、代码块等）。
  - 卡片高度计算有时不准确（正在优化中）。
- **后续计划**：
  - 兼容OpenAI API调用

## 🖼️ 效果图片展示
以下是使用 Text2Card 生成的图片示例：

![示例卡片](./assets/example_card.png)

（注：上图展示了 Text2Card 生成的卡片效果。）

## 🛠️ 环境安装

### 1. 克隆项目
首先，将项目克隆到本地：

```bash
git clone https://github.com/LargeCupPanda/text2card.git
cd text2card
```

### 2. 安装依赖
项目依赖Python 3.7及以上版本。建议使用虚拟环境来管理依赖。

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 字体文件准备
项目使用了自定义字体文件，确保以下字体文件存在于项目根目录中：
- `msyh.ttc`（微软雅黑常规字体）
- `msyhbd.ttc`（微软雅黑粗体）
- `TwitterColorEmoji.ttf`（彩色emoji字体）

如果缺少这些字体文件，可以从系统字体目录中复制，或者从合法渠道下载。

### 4. 运行示例
项目提供了一个入口函数 `generate_image`，可以直接调用生成图片。以下是一个简单的示例：

```python
from image_generator import generate_image

text = """
# 这是一个标题
## 这是一个二级标题
- 这是一个列表项
- 这是另一个列表项
"""

generate_image(text, "output.png", title_image="title.png")
```

运行后，生成的图片将保存为 `output.png`。

## 📂 项目结构
```
text2card/
├── assets/
│   └── example_card.png  # 效果图
├── image_generator.py    # 图片生成主逻辑
├── requirements.txt      # 依赖文件
├── msyh.ttc              # 微软雅黑常规字体
├── msyhbd.ttc            # 微软雅黑粗体
├── TwitterColorEmoji.ttf # 彩色emoji字体
└── README.md             # 项目说明文档
```

## 📜 使用说明
### 1. 文本输入
支持Markdown格式的文本输入，包括标题、列表、普通文本等。示例：

```markdown
# 这是一个标题
## 这是一个二级标题
- 这是一个列表项
- 这是另一个列表项
```

### 2. 图片标题
可以通过 `title_image` 参数指定卡片顶部的图片标题。图片会自动缩放以适应卡片宽度。

### 3. 生成图片
调用 `generate_image` 函数，传入文本、输出路径和可选标题图片路径，即可生成图片。

```python
generate_image(text, "output.png", title_image="title.png")
```

## 🤝 贡献与反馈
如果你有任何建议或发现问题，欢迎提交Issue或Pull Request。我们非常欢迎社区的贡献！

## 📄 许可证
本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

---

希望这个小工具能帮助你轻松生成精美的图片卡片！如果有任何问题或建议，欢迎随时反馈。🎉

---