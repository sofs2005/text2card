import os
import re
import markdown
from weasyprint import HTML, CSS
from io import BytesIO
from PIL import Image
import base64
import random
from typing import Optional, Tuple

def get_random_gradient():
    """获取随机渐变背景样式"""
    gradients = [
        # 柔和渐变
        "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
        "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)",
        "linear-gradient(135deg, #f6d365 0%, #fda085 100%)",
        "linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)",
        "linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)",
        
        # 高级灰
        "linear-gradient(135deg, #f5f7fa 0%, #eef1f5 100%)",
        "linear-gradient(135deg, #f0f2f5 0%, #e8eaed 100%)",
        
        # 柔和粉
        "linear-gradient(135deg, #fff1eb 0%, #ace0f9 100%)",
        "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
        
        # 淡紫色
        "linear-gradient(135deg, #c1dfc4 0%, #deecdd 100%)",
        "linear-gradient(135deg, #e8e4fc 0%, #d5cafc 100%)"
    ]
    return random.choice(gradients)

def create_html_template(content, title_image=None):
    """
    创建用于渲染的HTML模板
    
    Args:
        content: 包含可能的HTML标签的文本内容
        title_image: 可选的标题图片URL
        
    Returns:
        完整的HTML文档字符串
    """
    # 将Markdown转换为HTML，但保留已有的HTML标签
    # markdown.markdown函数默认会转义HTML标签，设置extensions=['extra']可以保留
    md_content = markdown.markdown(content, extensions=['extra'])
    
    # 替换有序列表，确保它们有正确的样式
    md_content = re.sub(r'<ol>(.*?)</ol>', r'<div class="ordered-list">\1</div>', md_content, flags=re.DOTALL)
    
    # 获取随机渐变
    background_gradient = get_random_gradient()
    
    # 构建HTML模板
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>图片卡片</title>
        <style>
            @font-face {{
                font-family: 'MicrosoftYaHei';
                src: url('{os.path.abspath("msyh.ttc")}');
                font-weight: normal;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'MicrosoftYaHeiBold';
                src: url('{os.path.abspath("msyhbd.ttc")}');
                font-weight: bold;
                font-style: normal;
            }}
            body {{
                font-family: 'MicrosoftYaHei', sans-serif;
                margin: 0;
                padding: 0;
                background: {background_gradient};
                color: #333;
            }}
            .card {{
                width: 680px;
                margin: 20px auto;
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
            }}
            h1, h2, h3, h4, h5, h6 {{
                font-family: 'MicrosoftYaHeiBold', sans-serif;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
                color: #222;
            }}
            h1 {{
                font-size: 32px;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            p {{
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 1em;
            }}
            ol {{
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 1em;
                margin-left: 1.5em;
            }}
            ol li {{
                margin-bottom: 0.8em;
                padding-left: 0.5em;
            }}
            ul {{
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 1em;
                margin-left: 1.5em;
            }}
            ul li {{
                margin-bottom: 0.8em;
                list-style-type: disc;
            }}
            .ordered-list {{
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 1em;
            }}
            .title-image {{
                width: 100%;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .signature {{
                margin-top: 30px;
                text-align: right;
                font-style: italic;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="card">
    """
    
    # 添加标题图片（如果提供）
    if title_image:
        html_template += f'<img class="title-image" src="{title_image}" alt="Title Image">\n'
    
    # 添加内容
    html_template += f"""
            {md_content}
            <div class="signature">—By 飞天</div>
        </div>
    </body>
    </html>
    """
    
    return html_template

def generate_image_with_weasyprint(text: str, output_path: str, title_image: Optional[str] = None):
    """
    使用WeasyPrint渲染HTML文本并保存为图像
    
    Args:
        text: Markdown文本内容，可包含HTML标签
        output_path: 输出图像路径
        title_image: 可选的标题图片URL
    """
    # 创建HTML模板
    html_content = create_html_template(text, title_image)
    
    # 使用WeasyPrint渲染HTML
    html = HTML(string=html_content)
    
    # 创建基本CSS
    css = CSS(string='''
        @page {
            margin: 0;
            size: 760px 1000px;
        }
    ''')
    
    # 渲染为PNG
    png_file = html.write_png(target=None, stylesheets=[css])
    
    # 转换为PIL Image并裁剪到实际内容大小
    img = Image.open(BytesIO(png_file))
    # 适当裁剪，保留内容区域（WeasyPrint渲染的图像可能有空白）
    
    # 保存图像
    img.save(output_path)
    print(f"图片已生成并保存到: {output_path}")
    
    return img

# 添加对现有test_color.py的兼容支持
def generate_image(text: str, output_path: str, title_image: Optional[str] = None):
    """兼容原有generate_image函数的接口"""
    return generate_image_with_weasyprint(text, output_path, title_image) 