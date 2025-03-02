# 📝 Text2Card 项目说明

[English](./README_EN.md) | [中文](./README.md)


## ✅ 前言
Text2Card 是一个小而美的工具，能够将文本内容转换为精美的图片卡片。相比使用无头浏览器截图的方式，Text2Card 更加轻量，不依赖外部服务，直接通过函数调用生成图片，性能高效且易于集成。现已支持 OpenAI API 格式调用，可轻松集成到各类 AI 应用中。

## 🙏 致谢
本项目是基于 [@LargeCupPanda/Text2Card](https://github.com/LargeCupPanda/Text2Card) 进行修改而来的，感谢原作者的开源贡献！

## 🚀 功能特性
- **开箱即用**：简化配置，无需复杂设置，快速部署使用。
- **OpenAI API兼容**：支持标准 OpenAI API 格式调用，易于集成。
- **流式响应支持**：支持OpenAI的流式响应(streaming)，适配更多LLM客户端。
- **自动图片检测**：自动识别URL格式内容作为标题图片，简化调用流程。
- **安全认证机制**：基于 token 的图片访问控制，支持 API 密钥认证。
- **卡片多主题配色**：支持多种渐变背景配色，卡片风格多样。
- **Markdown解析渲染**：支持基本的 Markdown 语法解析，如标题、列表等。
- **日间夜间模式自动切换**：根据时间自动切换日间和夜间模式。
- **图片标题**：支持在卡片顶部添加图片标题。
- **支持emoji渲染展示**：能够正确渲染和展示emoji表情。
- **超清图片保存**：生成的图片清晰度高，适合分享和展示。
- **自动清理机制**：定期清理过期图片文件。

**<span style="color:#FF9999;">PS：添加WeChat：Imladrsaon 转发微信公号文章可自动summary（Url2Text还能整理好，后续发）</span>**

## 🖼️ 效果图片展示
以下是使用 Text2Card 生成的图片示例：
![示例卡片](./assets/example_card.png)

（注：上图展示了 Text2Card 生成的卡片效果。）

## 🛠️ 环境安装

### 1. 克隆项目
```bash
git clone https://github.com/sofs2005/text2card.git
cd text2card
```

### 2. 环境配置
将`env_example` 复制为 `.env` 文件，并设置必要的环境变量：
```plaintext
# 服务器配置
HOST=http://127.0.0.1:3000  # 服务器基础URL，例如 http://your-server-ip:3000
PORT=3000                   # 服务器监听端口

# 安全配置
# 如不设置，系统会自动生成一个随机密钥
# SECRET_KEY=your-secret-key

# API密钥列表，JSON格式，例如 ["key1", "key2"]
# 为空时，任何API密钥都无法通过验证
API_KEYS=["your-api-key"]

# 图片URL令牌过期时间（秒）
TOKEN_EXPIRY=3600

# 存储配置
UPLOAD_FOLDER=picture       # 图片存储目录
MAX_CONTENT_LENGTH=10485760 # 最大请求大小，默认10MB

# 日志配置
LOG_LEVEL=INFO              # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=%(asctime)s - %(levelname)s - %(message)s

# 图片生成配置
SIGNATURE_TEXT=—By 飞天     # 图片签名文本，会自动右对齐
```

### 3. 安装依赖
```bash
# 虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 字体文件准备
确保以下字体文件存在于项目根目录：
- `msyh.ttc`（微软雅黑常规字体）
- `msyhbd.ttc`（微软雅黑粗体）
- `TwitterColorEmoji.ttf`（彩色emoji字体）

## 📡 API 使用说明

### OpenAI 格式调用
```python
import requests

def generate_card(text, api_key):
    url = "http://127.0.0.1:3000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Text2Card",
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 使用示例
result = generate_card("要转换的文本内容", "your-api-key")
print(result)
```

### 使用流式响应（Streaming）
```python
import requests
import json

def generate_card_streaming(text, api_key):
    url = "http://127.0.0.1:3000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Text2Card",
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ],
        "stream": True  # 启用流式响应
    }
    
    response = requests.post(url, headers=headers, json=data, stream=True)
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: ') and not line.endswith('[DONE]'):
                chunk = json.loads(line[6:])  # 去掉 "data: " 前缀
                if 'choices' in chunk and chunk['choices']:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        # 处理内容片段
                        print(f"收到内容: {delta['content']}")
```

### 直接在内容中添加图片URL
```python
def generate_card_with_url_content(api_key):
    """直接在内容中添加图片URL，系统会自动识别为标题图片"""
    url = "http://127.0.0.1:3000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # 在内容开头添加图片URL，系统会自动识别
    content = "https://example.com/image.jpg\n这是卡片的正文内容"
    data = {
        "model": "Text2Card",
        "messages": [
            {
                "role": "user", 
                "content": content
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### 设置响应格式

```python
def generate_card_with_format(text, api_key, format_type="text"):
    """指定响应格式，可选值为 text 或 json_object"""
    url = "http://127.0.0.1:3000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Text2Card",
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ],
        "response_format": {"type": format_type}
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### 带图片标题的调用
```python
def generate_card_with_image(text, image_url, api_key):
    url = "http://127.0.0.1:3000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Text2Card",
        "messages": [
            {
                "role": "user",
                "content": text,
                "title_image": image_url
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### 响应格式
#### 普通响应
```json
{
    "id": "text2card-1234567890",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "Text2Card",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "![图片卡片](http://127.0.0.1:3000/v1/images/20250102123456_abcdef.png?token=abc123&expiry=1234567890)"
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}
```

#### 流式响应片段
```json
data: {"id":"text2card-1234567890","object":"chat.completion.chunk","created":1234567890,"model":"Text2Card","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"text2card-1234567890","object":"chat.completion.chunk","created":1234567890,"model":"Text2Card","choices":[{"index":0,"delta":{"content":"![图片卡片](http://127.0.0.1:3000/v1/images/20250102123456_abcdef.png?token=abc123&expiry=1234567890)"},"finish_reason":null}]}

data: {"id":"text2card-1234567890","object":"chat.completion.chunk","created":1234567890,"model":"Text2Card","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## 📂 项目结构
```
text2card/
├── assets/
│   └── example_card.png    # 效果图
├── image_generator.py      # 图片生成主逻辑
├── app.py                  # API 服务器实现
├── config.py              # 配置管理
├── .env                   # 环境变量配置
├── requirements.txt       # 依赖文件
├── msyh.ttc              # 微软雅黑常规字体
├── msyhbd.ttc            # 微软雅黑粗体
├── TwitterColorEmoji.ttf # 彩色emoji字体
└── README.md             # 项目说明文档
```

## 🔐 安全说明
- API 密钥认证：所有请求需要通过 API 密钥认证
- URL Token：图片访问使用临时 token，增强安全性
- 文件清理：自动清理过期文件，避免存储占用
- 自动密钥生成：无需手动设置密钥，系统自动生成

## 🤝 贡献与反馈
如果你有任何建议或发现问题，欢迎提交 Issue 或 Pull Request。我们非常欢迎社区的贡献！

## 📄 许可证
本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

---
希望这个工具能帮助你轻松生成精美的图片卡片！如有问题或建议，欢迎随时反馈。🎉
