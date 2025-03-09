import os
import re
import random
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListItem, ListFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as ReportlabImage

# 注册字体
current_dir = os.path.dirname(os.path.abspath(__file__))
pdfmetrics.registerFont(TTFont('Microsoft-YaHei', os.path.join(current_dir, 'msyh.ttc')))
pdfmetrics.registerFont(TTFont('Microsoft-YaHei-Bold', os.path.join(current_dir, 'msyhbd.ttc')))

def get_random_color():
    """获取随机背景色"""
    pastel_colors = [
        (255, 245, 245),  # 浅粉色
        (245, 255, 245),  # 浅绿色
        (245, 245, 255),  # 浅蓝色
        (255, 245, 230),  # 浅橙色
        (245, 230, 255),  # 浅紫色
        (230, 255, 245),  # 浅青色
        (248, 248, 255),  # 淡紫色
        (240, 255, 240),  # 淡绿色
        (255, 240, 245),  # 淡粉色
        (240, 248, 255),  # 淡蓝色
    ]
    return random.choice(pastel_colors)

def replace_color_span(match):
    """
    替换颜色标签为reportlab颜色标签
    """
    color_value = match.group(1)
    content = match.group(2)
    
    # 处理颜色值，确保有效
    if color_value == 'red':
        color_value = '#FF0000'
    elif color_value == 'blue':
        color_value = '#0000FF'
    elif color_value == 'green':
        color_value = '#00FF00'
    
    # 如果不是以#开头，添加#
    if not color_value.startswith('#') and not color_value in colors.getAllNamedColors():
        color_value = '#' + color_value
    
    return f'<font color="{color_value}">{content}</font>'

def process_html_tags(text):
    """
    处理HTML标签，将<span style="color:...">转换为reportlab支持的<font color="...">
    """
    # 替换颜色标签
    color_pattern = r'<span\s+style=["\']color:\s*([^;"\'\s]+)[;"\'](.*?)>(.*?)</span>'
    return re.sub(color_pattern, replace_color_span, text, flags=re.DOTALL)

def generate_image_with_reportlab(text: str, output_path: str, title_image: Optional[str] = None):
    """
    使用ReportLab生成PDF，然后转换为图像
    
    Args:
        text: Markdown文本，可包含HTML颜色标签
        output_path: 输出图像路径
        title_image: 可选的标题图片路径
    """
    # 处理HTML颜色标签
    processed_text = process_html_tags(text)
    
    # 转换Markdown为HTML
    html_content = markdown.markdown(processed_text, extensions=['extra'])
    
    # 设置PDF文档
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4,
        rightMargin=50, 
        leftMargin=50,
        topMargin=50, 
        bottomMargin=50
    )
    
    # 创建样式
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Normal-YaHei',
        fontName='Microsoft-YaHei',
        fontSize=12,
        leading=16,
        spaceBefore=5,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='Heading1-YaHei',
        fontName='Microsoft-YaHei-Bold',
        fontSize=18,
        leading=22,
        spaceBefore=10,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='Heading2-YaHei',
        fontName='Microsoft-YaHei-Bold',
        fontSize=16,
        leading=20,
        spaceBefore=8,
        spaceAfter=8
    ))
    
    # 构建文档内容
    content = []
    
    # 添加标题图片（如果有）
    if title_image:
        img = ReportlabImage(title_image, width=480, height=300)
        content.append(img)
        content.append(Spacer(1, 10))
    
    # 将HTML内容分割成段落和列表
    paragraphs = re.split(r'</?p>|</?h\d>', html_content)
    paragraphs = [p for p in paragraphs if p.strip()]
    
    for p in paragraphs:
        # 移除HTML标签，只保留<font>标签
        p = re.sub(r'<(?!/?font)[^>]*>', '', p)
        p = p.strip()
        if not p:
            continue
        
        # 检查是否是有序列表项
        list_match = re.match(r'^\d+\.\s+(.+)$', p)
        if list_match:
            # 有序列表项
            list_content = list_match.group(1)
            list_item = ListItem(
                Paragraph(list_content, styles['Normal-YaHei']),
                value=p.split('.')[0],
                leftIndent=20
            )
            list_flow = ListFlowable(
                [list_item],
                bulletType='bullet',
                start=int(p.split('.')[0]),
                leftIndent=20,
                bulletFontName='Microsoft-YaHei'
            )
            content.append(list_flow)
        elif p.startswith('# '):
            # 一级标题
            content.append(Paragraph(p[2:], styles['Heading1-YaHei']))
        elif p.startswith('## '):
            # 二级标题
            content.append(Paragraph(p[3:], styles['Heading2-YaHei']))
        else:
            # 普通段落
            content.append(Paragraph(p, styles['Normal-YaHei']))
    
    # 添加签名
    content.append(Spacer(1, 20))
    content.append(Paragraph("—By 飞天", ParagraphStyle(
        name='Signature',
        fontName='Microsoft-YaHei',
        fontSize=10,
        textColor=colors.darkgray,
        alignment=2  # 右对齐
    )))
    
    # 生成PDF
    doc.build(content)
    
    # 将PDF转换为图片
    from pdf2image import convert_from_bytes
    pages = convert_from_bytes(pdf_buffer.getvalue(), dpi=200)
    if pages:
        page = pages[0]
        # 设置背景色为浅色
        bg_color = get_random_color()
        background = Image.new('RGB', page.size, color=bg_color)
        background.paste(page, (0, 0), page.convert('RGBA'))
        background.save(output_path)
        print(f"图片已生成并保存到: {output_path}")
        return background
    else:
        print("无法生成图片")
        return None

# 添加对现有test_color.py的兼容支持
def generate_image(text: str, output_path: str, title_image: Optional[str] = None):
    """兼容原有generate_image函数的接口"""
    return generate_image_with_reportlab(text, output_path, title_image) 