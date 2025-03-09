from PIL import Image, ImageDraw, ImageFont
import os
import re
import emoji
import markdown
from bs4 import BeautifulSoup
from io import BytesIO
import textwrap
import random
import math
from datetime import datetime
import numpy as np
import uuid

class TextStyle:
    """文本样式定义"""
    def __init__(self, color='black', is_bold=False, is_italic=False, font_size=30):
        self.color = color
        self.is_bold = is_bold
        self.is_italic = is_italic
        self.font_size = font_size

class TextSegment:
    """文本段落，包含文本和样式"""
    def __init__(self, text, style):
        self.text = text
        self.style = style

def is_emoji(char):
    """检查字符是否为emoji"""
    return emoji.is_emoji(char)

def get_system_font():
    """获取系统中可用的中文字体"""
    # 直接使用项目目录下的字体文件
    regular_font = './msyh.ttc'
    if os.path.exists(regular_font):
        return regular_font
    
    # 兼容性代码，以防字体文件路径不正确
    current_dir = os.path.dirname(os.path.abspath(__file__))
    regular_font = os.path.join(current_dir, 'msyh.ttc')
    if os.path.exists(regular_font):
        return regular_font
    
    return None

def get_bold_font():
    """获取粗体字体"""
    # 直接使用项目目录下的粗体字体文件
    bold_font = './msyhbd.ttc'
    if os.path.exists(bold_font):
        return bold_font
    
    # 兼容性代码，以防字体文件路径不正确
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bold_font = os.path.join(current_dir, 'msyhbd.ttc')
    if os.path.exists(bold_font):
        return bold_font
    
    return None

def get_emoji_font():
    """获取emoji字体"""
    # 直接使用项目目录下的emoji字体文件
    emoji_font = './TwitterColorEmoji.ttf'
    if os.path.exists(emoji_font):
        return emoji_font
    
    # 兼容性代码，以防字体文件路径不正确
    current_dir = os.path.dirname(os.path.abspath(__file__))
    emoji_font = os.path.join(current_dir, 'TwitterColorEmoji.ttf')
    if os.path.exists(emoji_font):
        return emoji_font
    
    return None

def get_italic_font():
    """获取斜体字体，优先尝试msyhi.ttc (微软雅黑斜体)"""
    # 先尝试windows系统下常见的斜体字体路径
    possible_italic_paths = [
        "./msyhi.ttc",  # 当前目录下的微软雅黑斜体
        "C:/Windows/Fonts/msyhi.ttc",  # Windows系统微软雅黑斜体
        "C:/Windows/Fonts/simsuni.ttf",  # Windows系统宋体斜体
        "C:/Windows/Fonts/ariali.ttf",   # Arial斜体
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",  # Linux斜体字体
        "/System/Library/Fonts/STHeiti-Light.ttc"  # macOS斜体字体
    ]
    
    for path in possible_italic_paths:
        if os.path.exists(path):
            return path
    
    return None

def load_fonts():
    """加载字体"""
    fonts = {}
    
    font_path = get_system_font()
    bold_font_path = get_bold_font() or font_path
    italic_font_path = get_italic_font() or font_path  # 尝试获取斜体字体
    emoji_font_path = get_emoji_font()
    
    if font_path:
        print(f"使用常规字体: {font_path}")
        fonts['regular'] = ImageFont.truetype(font_path, size=30)
        fonts['h1'] = ImageFont.truetype(font_path, size=48)
        fonts['h2'] = ImageFont.truetype(font_path, size=36)
        fonts['h3'] = ImageFont.truetype(font_path, size=30)
        fonts['small'] = ImageFont.truetype(font_path, size=24)
        
        # 加载斜体字体
        if italic_font_path and italic_font_path != font_path:
            print(f"使用斜体字体: {italic_font_path}")
            fonts['italic'] = ImageFont.truetype(italic_font_path, size=30)
        else:
            # 如果没有专门的斜体字体，使用常规字体并应用斜体变换
            print("未找到斜体字体，将使用常规字体模拟斜体")
            fonts['italic'] = fonts['regular']
    else:
        print("警告: 未找到常规字体文件，使用默认字体")
        fonts['regular'] = ImageFont.load_default()
        fonts['italic'] = ImageFont.load_default()
        fonts['h1'] = ImageFont.load_default()
        fonts['h2'] = ImageFont.load_default()
        fonts['h3'] = ImageFont.load_default()
        fonts['small'] = ImageFont.load_default()
    
    if bold_font_path:
        print(f"使用粗体字体: {bold_font_path}")
        fonts['bold'] = ImageFont.truetype(bold_font_path, size=30)
    else:
        print("警告: 未找到粗体字体文件，使用常规字体代替")
        fonts['bold'] = fonts['regular']
    
    # 加载粗斜体字体 (如果没有专门的粗斜体字体，使用粗体字体模拟)
    fonts['bold_italic'] = fonts['bold']
    
    # 加载emoji字体
    if emoji_font_path:
        print(f"使用emoji字体: {emoji_font_path}")
        fonts['emoji'] = ImageFont.truetype(emoji_font_path, size=30)
    else:
        print("警告: 未找到emoji字体文件，使用常规字体代替")
        fonts['emoji'] = fonts['regular']
    
    return fonts

def draw_text_with_style(draw, fonts, pos, text, style):
    """绘制带样式的文本"""
    x, y = pos
    
    # 选择字体
    if style.is_bold and style.is_italic:
        font = fonts['bold_italic']
    elif style.is_bold:
        font = fonts['bold']
    elif style.is_italic:
        font = fonts['italic']
    else:
        font = fonts['regular']
    
    # 确保颜色值正确 - 强制转换为PIL可用的颜色
    color = style.color
    
    # 常见颜色名称到RGB元组的映射
    color_map = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'pink': (255, 192, 203),
        'brown': (165, 42, 42),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'teal': (0, 128, 128),
        'navy': (0, 0, 128),
        'olive': (128, 128, 0)
    }
    
    # 转换颜色格式
    if isinstance(color, str):
        color_lower = color.lower()
        # 检查是否是预定义颜色名称
        if color_lower in color_map:
            color = color_map[color_lower]
            print(f"使用预定义颜色: {color_lower} -> {color}")
        # 处理十六进制颜色码
        elif color.startswith('#'):
            try:
                color = color.lstrip('#')
                if len(color) == 3:  # #RGB 格式
                    r = int(color[0] + color[0], 16)
                    g = int(color[1] + color[1], 16)
                    b = int(color[2] + color[2], 16)
                    color = (r, g, b)
                    print(f"转换短格式十六进制颜色: {color}")
                elif len(color) == 6:  # #RRGGBB 格式
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    color = (r, g, b)
                    print(f"转换十六进制颜色: {color}")
                else:
                    print(f"无效的十六进制颜色格式: {color}, 使用默认黑色")
                    color = (0, 0, 0)
            except:
                print(f"无法解析颜色: {color}, 使用默认黑色")
                color = (0, 0, 0)
        else:
            print(f"未知颜色名称: {color}, 使用默认黑色")
            color = (0, 0, 0)
    
    # 打印出最终使用的颜色值，确保我们能看到实际应用的颜色
    print(f"绘制文本: '{text}', 使用颜色: {color}")
    
    # 检查是否包含emoji
    if any(is_emoji(char) for char in text):
        # 逐字符绘制，以支持emoji
        current_x = x
        for char in text:
            if is_emoji(char):
                emoji_font = fonts['emoji']
                draw.text((current_x, y), char, fill=color, font=emoji_font)
                current_x += draw.textlength(char, font=emoji_font)
            else:
                draw.text((current_x, y), char, fill=color, font=font)
                current_x += draw.textlength(char, font=font)
        
        return current_x - x
    
    # 绘制普通文本
    if text:
        draw.text((x, y), text, fill=color, font=font)
    
    # 返回文本宽度
    return draw.textlength(text, font=font)

def parse_html_to_segments(html):
    """解析HTML为文本段落列表，确保正确提取彩色文本"""
    soup = BeautifulSoup(html, 'html.parser')
    segments = []
    
    # 直接查找所有span标签，确认颜色标签是否存在
    color_spans = soup.find_all('span', style=re.compile(r'color\s*:\s*'))
    print(f"直接搜索到{len(color_spans)}个颜色标签")
    for span in color_spans[:3]:  # 仅显示前3个
        print(f"颜色标签: {span}")
    
    # 显示整个HTML结构，帮助调试
    print(f"HTML内容: {html[:500]}...")
    
    # 递归解析HTML元素
    def parse_element(element, parent_style=None):
        # 如果是字符串（文本节点），直接添加
        if isinstance(element, str):
            text = element.strip()
            if text:
                style = TextStyle(
                    color=parent_style.color if parent_style else 'black',
                    is_bold=parent_style.is_bold if parent_style else False,
                    is_italic=parent_style.is_italic if parent_style else False
                )
                segments.append(TextSegment(element, style))
            return
        
        # 创建一个新的样式对象
        current_style = TextStyle()
        if parent_style:
            current_style.color = parent_style.color
            current_style.is_bold = parent_style.is_bold
            current_style.is_italic = parent_style.is_italic
        
        # 分析元素的样式
        if element.name in ['strong', 'b']:
            current_style.is_bold = True
        elif element.name in ['em', 'i']:
            current_style.is_italic = True
        elif element.name == 'span' and element.get('style'):
            style_attr = element.get('style')
            # 打印每个span的样式以调试
            print(f"找到span标签，样式: {style_attr}")
            
            if 'color:' in style_attr:
                color_match = re.search(r'color\s*:\s*([^;]+)', style_attr)
                if color_match:
                    color_value = color_match.group(1).strip()
                    current_style.color = color_value
                    print(f"设置颜色为: {color_value}")
        
        # 处理子元素
        for child in element.contents:
            if isinstance(child, str):
                if child.strip():
                    segments.append(TextSegment(child, TextStyle(
                        color=current_style.color,
                        is_bold=current_style.is_bold,
                        is_italic=current_style.is_italic
                    )))
            else:
                parse_element(child, current_style)
    
    # 处理所有顶级元素
    if soup.body:
        for element in soup.body.children:
            if isinstance(element, str):
                if element.strip():
                    segments.append(TextSegment(element, TextStyle()))
            else:
                parse_element(element)
    else:
        # 如果没有body标签，尝试直接处理根元素的子元素
        print("找不到body标签，尝试直接处理HTML根元素")
        for element in soup.children:
            if isinstance(element, str):
                if element.strip():
                    segments.append(TextSegment(element, TextStyle()))
            else:
                parse_element(element)
    
    print(f"解析完成，共找到{len(segments)}个文本段落")
    for i, segment in enumerate(segments):
        if segment.style.color != 'black':
            print(f"段落{i}: '{segment.text}'，颜色: {segment.style.color}")
    
    return segments

def markdown_to_html(text):
    """将Markdown转换为HTML，确保保留颜色标签"""
    # 彻底重写，采用新策略来处理span标签
    
    # 步骤1: 保护所有HTML标签，特别是span颜色标签
    protected_text = text
    
    # 直接显示原始文本，帮助调试
    print(f"原始Markdown文本: {text[:300]}...")
    
    # 查找所有颜色span标签
    span_matches = re.findall(r'(<span\s+style\s*=\s*["\']color:\s*([^;"\']+)["\']>(.+?)</span>)', 
                             text, flags=re.DOTALL)
    
    print(f"找到{len(span_matches)}个颜色span标签")
    for i, match in enumerate(span_matches[:3]):  # 显示前3个
        print(f"颜色标签{i}: {match[0]}, 颜色: {match[1]}")
    
    # 生成唯一的替换标记
    placeholders = {}
    
    # 替换所有span标签为占位符
    for span_text, color, content in span_matches:
        placeholder = f"SPAN_{uuid.uuid4().hex}"
        placeholders[placeholder] = span_text
        protected_text = protected_text.replace(span_text, placeholder)
    
    # 步骤2: 转换为HTML
    html_content = markdown.markdown(protected_text, extensions=['extra', 'sane_lists'])
    
    # 步骤3: 还原所有span标签
    for placeholder, original in placeholders.items():
        html_content = html_content.replace(placeholder, original)
    
    # 检查最终HTML是否包含span标签
    final_span_count = html_content.count('<span style="color:')
    print(f"最终HTML中包含{final_span_count}个颜色span标签")
    
    # 确保返回完整的HTML结构
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
{html_content}
</body>
</html>
"""
    return html

def get_gradient_styles():
    """
    获取精心设计的背景渐变样式
    """
    return [
        # Mac 高级白
        {
            "start_color": (246, 246, 248),  # 珍珠白
            "end_color": (250, 250, 252)  # 云雾白
        },
        {
            "start_color": (245, 245, 247),  # 奶白色
            "end_color": (248, 248, 250)  # 象牙白
        },
        # macOS Monterey 风格
        {
            "start_color": (191, 203, 255),  # 淡蓝紫
            "end_color": (255, 203, 237)  # 浅粉红
        },
        {
            "start_color": (168, 225, 255),  # 天空蓝
            "end_color": (203, 255, 242)  # 清新薄荷
        },

        # 优雅渐变系列
        {
            "start_color": (255, 209, 209),  # 珊瑚粉
            "end_color": (243, 209, 255)  # 淡紫色
        },
        {
            "start_color": (255, 230, 209),  # 奶橘色
            "end_color": (255, 209, 247)  # 粉紫色
        },

        # 清新通透
        {
            "start_color": (213, 255, 219),  # 嫩绿色
            "end_color": (209, 247, 255)  # 浅蓝色
        },
        {
            "start_color": (255, 236, 209),  # 杏橘色
            "end_color": (255, 209, 216)  # 浅玫瑰
        },

        # 高级灰调
        {
            "start_color": (237, 240, 245),  # 珍珠灰
            "end_color": (245, 237, 245)  # 薰衣草灰
        },
        {
            "start_color": (240, 245, 255),  # 云雾蓝
            "end_color": (245, 240, 245)  # 淡紫灰
        },

        # 梦幻糖果色
        {
            "start_color": (255, 223, 242),  # 棉花糖粉
            "end_color": (242, 223, 255)  # 淡紫丁香
        },
        {
            "start_color": (223, 255, 247),  # 薄荷绿
            "end_color": (223, 242, 255)  # 天空蓝
        },

        # 高饱和度系列
        {
            "start_color": (255, 192, 203),  # 粉红色
            "end_color": (192, 203, 255)  # 淡紫蓝
        },
        {
            "start_color": (192, 255, 238),  # 碧绿色
            "end_color": (238, 192, 255)  # 淡紫色
        },

        # 静谧系列
        {
            "start_color": (230, 240, 255),  # 宁静蓝
            "end_color": (255, 240, 245)  # 柔粉色
        },
        {
            "start_color": (245, 240, 255),  # 淡紫色
            "end_color": (240, 255, 240)  # 清新绿
        },

        # 温柔渐变
        {
            "start_color": (255, 235, 235),  # 温柔粉
            "end_color": (235, 235, 255)  # 淡雅紫
        },
        {
            "start_color": (235, 255, 235),  # 嫩芽绿
            "end_color": (255, 235, 245)  # 浅粉红
        }
    ]

def create_gradient_background(width: int, height: int) -> Image.Image:
    """创建渐变背景 - 从左上到右下的对角线渐变"""
    gradient_styles = get_gradient_styles()
    style = random.choice(gradient_styles)
    start_color = style["start_color"]
    end_color = style["end_color"]

    # 创建基础图像
    base = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(base)

    # 计算渐变
    for y in range(height):
        for x in range(width):
            # 计算当前位置到左上角的相对距离 (对角线渐变)
            # 使用 position 在 0 到 1 之间表示渐变程度
            position = (x + y) / (width + height)

            # 为每个颜色通道计算渐变值
            r = int(start_color[0] * (1 - position) + end_color[0] * position)
            g = int(start_color[1] * (1 - position) + end_color[1] * position)
            b = int(start_color[2] * (1 - position) + end_color[2] * position)

            # 绘制像素
            draw.point((x, y), fill=(r, g, b))

    return base

def get_theme_colors():
    """获取主题颜色配置"""
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute

    if (current_hour == 8 and current_minute >= 30) or (9 <= current_hour < 19):
        use_dark = random.random() < 0.1
    else:
        use_dark = True

    if use_dark:
        # 深色毛玻璃效果: 深色半透明背景(50%透明度) + 白色文字
        return ((50, 50, 50, 128), "#FFFFFF", True)  # alpha值调整为128实现50%透明度
    else:
        # 浅色毛玻璃效果: 白色半透明背景(50%透明度) + 黑色文字
        return ((255, 255, 255, 128), "#000000", False)  # alpha值调整为128实现50%透明度

def create_rounded_rectangle(image: Image.Image, x: int, y: int, w: int, h: int, radius: int, bg_color: tuple):
    """创建圆角毛玻璃矩形"""
    # 创建透明背景的矩形
    rectangle = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rectangle)

    # 绘制带透明度的圆角矩形
    draw.rounded_rectangle(
        [(0, 0), (int(w), int(h))],
        radius,
        fill=bg_color  # 使用带透明度的背景色
    )

    # 使用alpha通道混合方式粘贴到背景上
    image.paste(rectangle, (int(x), int(y)), rectangle)

def round_corner_image(image: Image.Image, radius: int) -> Image.Image:
    """将图片转为圆角"""
    # 创建一个带有圆角的蒙版
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

    # 创建一个完整的蒙版
    mask = Image.new('L', image.size, 255)

    # 添加四个圆角
    mask.paste(circle.crop((0, 0, radius, radius)), (0, 0))  # 左上
    mask.paste(circle.crop((radius, 0, radius * 2, radius)), (image.width - radius, 0))  # 右上
    mask.paste(circle.crop((0, radius, radius, radius * 2)), (0, image.height - radius))  # 左下
    mask.paste(circle.crop((radius, radius, radius * 2, radius * 2)),
               (image.width - radius, image.height - radius))  # 右下

    # 创建一个空白的透明图像
    output = Image.new('RGBA', image.size, (0, 0, 0, 0))

    # 将原图和蒙版合并
    output.paste(image, (0, 0))
    output.putalpha(mask)

    return output

def crop_excess_whitespace(image):
    """裁剪图像底部多余的空白"""
    # 将图像转换为numpy数组
    img_array = np.array(image)
    
    # 查找最后一个非空（非白色）像素的行
    height, width, _ = img_array.shape
    threshold = 245  # 近似白色的阈值
    
    # 从底部往上扫描
    last_content_row = 0
    for y in range(height-1, 0, -1):
        row = img_array[y]
        # 如果该行有非白色像素
        if np.any(row[:, :3] < threshold):
            last_content_row = y
            break
    
    # 如果找到了内容的末尾，在其下方添加一些边距并裁剪
    if last_content_row > 0:
        # 添加100像素的底部边距
        crop_height = min(last_content_row + 100, height)
        return image.crop((0, 0, width, crop_height))
    
    return image

# 添加以下辅助函数用于更精确的文本布局计算
def calculate_text_dimensions(draw, text, font, max_width):
    """计算文本实际所需的宽度和高度，考虑文本换行"""
    if not text.strip():
        return 0, 0
    
    # 特殊处理：如果文本中有换行符，分别计算每一行
    if '\n' in text:
        lines = text.split('\n')
        total_width = 0
        total_height = 0
        for line in lines:
            if not line.strip():  # 空行
                total_height += int(font.size * 0.5)  # 空行高度，转为整数
                continue
            width, height = calculate_text_dimensions(draw, line, font, max_width)
            total_width = max(total_width, width)
            total_height += height
        return total_width, total_height
    
    # 获取文本宽度
    text_width = draw.textlength(text, font=font)
    
    # 如果宽度小于最大宽度，不需要换行
    if text_width <= max_width:
        return text_width, font.size
    
    # 需要换行，进行文本分行计算
    words = split_text_for_wrapping(text)
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = draw.textlength(word, font=font)
        
        # 检查添加这个词是否会超出最大宽度
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            # 当前行已满，开始新行
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
    
    # 添加最后一行
    if current_line:
        lines.append(' '.join(current_line))
    
    # 计算总高度
    line_height = int(font.size * 1.2)  # 行高略大于字体大小，转为整数
    total_height = len(lines) * line_height
    
    return max_width, total_height

def calculate_element_height(draw, element, fonts, max_width, style=None):
    """计算HTML元素所需的高度"""
    if not element or not element.name:
        return 0
    
    # 获取元素内的文本
    element_text = element.get_text().strip()
    if not element_text:
        return 0
    
    # 不同类型元素的处理
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        # 标题元素
        level = int(element.name[1])
        font_size = max(24, 48 - (level - 1) * 6)  # h1: 48, h2: 42, ...
        font_key = 'h1' if level == 1 else ('h2' if level == 2 else 'h3')
        font = fonts[font_key]
        _, height = calculate_text_dimensions(draw, element_text, font, max_width)
        # 标题额外间距
        return height + (50 - level * 5)
    
    elif element.name == 'p':
        # 段落
        font = fonts['regular']
        if style and style.is_bold:
            font = fonts['bold']
        _, height = calculate_text_dimensions(draw, element_text, font, max_width)
        # 段落间距
        return height + 20
    
    elif element.name in ['ul', 'ol']:
        # 列表
        total_height = 10  # 列表前间距
        list_items = element.find_all('li', recursive=False)
        
        for item in list_items:
            item_text = item.get_text().strip()
            # 列表项的缩进宽度
            indent_width = 40
            effective_width = max_width - indent_width
            
            # 计算列表项高度
            _, item_height = calculate_text_dimensions(draw, item_text, fonts['regular'], effective_width)
            total_height += item_height + 10  # 每项之间的间距
            
            # 处理嵌套列表
            nested_lists = item.find_all(['ul', 'ol'], recursive=False)
            for nested_list in nested_lists:
                nested_height = calculate_element_height(draw, nested_list, fonts, effective_width - 20)
                total_height += nested_height
        
        return total_height + 10  # 列表后间距
    
    elif element.name == 'li':
        # 单独的列表项（通常不会单独处理，但为了完整性）
        _, height = calculate_text_dimensions(draw, element_text, fonts['regular'], max_width - 40)
        return height + 10
    
    elif element.name == 'pre':
        # 代码块
        code_lines = element_text.split('\n')
        line_height = 25  # 代码行高
        code_height = len(code_lines) * line_height
        # 代码块边距
        return code_height + 40
    
    elif element.name == 'blockquote':
        # 引用块
        # 引用块内的内容可能有多个元素，需要递归计算
        quote_height = 0
        for child in element.children:
            if hasattr(child, 'name') and child.name:
                quote_height += calculate_element_height(draw, child, fonts, max_width - 40)
            elif hasattr(child, 'strip') and child.strip():
                _, height = calculate_text_dimensions(draw, child, fonts['regular'], max_width - 40)
                quote_height += height
        
        # 引用块边距
        return quote_height + 30
    
    # 默认元素处理
    _, height = calculate_text_dimensions(draw, element_text, fonts['regular'], max_width)
    return height

def estimate_precise_height(html, width, fonts):
    """精确估算渲染HTML所需的高度"""
    # 创建用于计算的临时图像
    temp_image = Image.new('RGBA', (width, 100))
    temp_draw = ImageDraw.Draw(temp_image)
    
    # 解析HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # 计算内容区域的宽度
    content_width = width - 180  # 减去左右边距
    
    # 顶部和底部边距
    top_margin = 60
    bottom_margin = 60
    
    # 计算所有顶级元素的总高度
    total_height = top_margin
    
    # 处理每个顶级元素
    if soup.body:
        for element in soup.body.children:
            if hasattr(element, 'name') and element.name:
                element_height = calculate_element_height(temp_draw, element, fonts, content_width)
                total_height += element_height
    else:
        # 如果没有body标签，则直接处理所有顶级元素
        for element in soup.children:
            if hasattr(element, 'name') and element.name:
                element_height = calculate_element_height(temp_draw, element, fonts, content_width)
                total_height += element_height
    
    # 添加底部边距
    total_height += bottom_margin
    
    # 确保最小高度
    min_height = 1000
    total_height = max(total_height, min_height)
    
    return total_height

def handle_multiline_text(draw, text, font, max_width):
    """处理多行文本，分行计算宽度和绘制"""
    # 如果文本包含换行符，分别处理每一行
    if '\n' in text:
        lines = text.split('\n')
        text_height = 0
        processed_lines = []
        
        for line in lines:
            if not line.strip():  # 空行
                processed_lines.append(line)
                text_height += int(font.size * 0.5)
            else:
                # 对每一行进行换行处理
                line_width = draw.textlength(line, font=font)
                if line_width <= max_width:
                    processed_lines.append(line)
                    text_height += font.size
                else:
                    # 需要再次换行
                    wrapped_words = split_text_for_wrapping(line)
                    current_line = []
                    current_width = 0
                    
                    for word in wrapped_words:
                        word_width = draw.textlength(word + ' ' if word else '', font=font)
                        if current_width + word_width <= max_width:
                            current_line.append(word)
                            current_width += word_width
                        else:
                            if current_line:
                                processed_lines.append(' '.join(current_line))
                                text_height += font.size
                            current_line = [word]
                            current_width = word_width
                    
                    if current_line:
                        processed_lines.append(' '.join(current_line))
                        text_height += font.size
        
        return processed_lines, text_height
    
    # 文本不包含换行符
    line_width = draw.textlength(text, font=font)
    if line_width <= max_width:
        return [text], font.size
    
    # 需要换行
    words = split_text_for_wrapping(text)
    wrapped_lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = draw.textlength(word + ' ' if word else '', font=font)
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:
                wrapped_lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
    
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    text_height = len(wrapped_lines) * font.size
    
    return wrapped_lines, text_height

# 完全重写render_markdown_to_image函数
def render_markdown_to_image(markdown_text, output_path, width=720, height=None):
    """双阶段渲染Markdown文本为图像"""
    # 第一阶段：转换Markdown为HTML并估算精确高度
    html = markdown_to_html(markdown_text)
    print(f"HTML长度: {len(html)}")
    
    # 加载字体
    fonts = load_fonts()
    
    # 如果没有指定高度，计算精确高度
    if height is None:
        height = estimate_precise_height(html, width, fonts)
        print(f"精确估算高度: {height}像素")
    
    # 第二阶段：使用计算出的精确高度进行实际渲染
    # 解析HTML，提取文本和样式
    soup = BeautifulSoup(html, 'html.parser')
    
    # 获取主题颜色
    background_color, text_color, is_dark_theme = get_theme_colors()
    
    # 创建渐变背景
    background = create_gradient_background(width, height)
    background = background.convert('RGBA')  # 转换为带Alpha通道的模式
    
    # 创建最终图像
    final_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # 粘贴背景图像
    final_image.paste(background, (0, 0))
    
    # 设置内容区域参数
    rect_width = width - 90  # 左右各留45像素边距
    rect_height = height - 120  # 上下各留60像素边距
    rect_x = (width - rect_width) // 2
    rect_y = 60
    
    # 创建卡片背景 - 半透明毛玻璃效果
    create_rounded_rectangle(
        final_image, rect_x, rect_y, rect_width, rect_height,
        radius=30, bg_color=background_color
    )
    
    # 创建绘图对象
    draw = ImageDraw.Draw(final_image)
    
    # 设置绘制参数
    x_margin = 45  # 左右边距
    content_y = rect_y + 30  # 内容起始y坐标
    content_width = rect_width - 90  # 内容区域宽度（减去左右内边距）
    current_y = content_y
    
    # 处理每个段落并绘制
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'blockquote', 'pre'], recursive=True):
        # 跳过已在父标签中处理的列表项
        if tag.name == 'li' and tag.parent and tag.parent.name in ['ul', 'ol']:
            continue
            
        tag_html = str(tag)
        tag_text = tag.get_text()
        
        # 不同类型标签的处理
        if tag.name.startswith('h'):
            # 标题样式
            level = int(tag.name[1])
            font_size = max(24, 48 - (level - 1) * 6)  # h1: 48, h2: 42, ...
            
            # 标题前添加更多空间，尤其是h2和h3
            if level > 1:  # 对于h2, h3等二级以下标题
                current_y += 30  # 在标题前增加额外间距
            else:  # h1标题
                current_y += 15  # h1也增加一些间距，但不需要那么多
            
            # 设置标题样式和颜色
            style = TextStyle(color=text_color, is_bold=True, font_size=font_size)
            
            # 根据级别选择字体
            font_key = 'h1' if level == 1 else ('h2' if level == 2 else 'h3')
            font = fonts[font_key]
            
            # 创建标题文本分段并绘制
            segments = parse_html_to_segments(tag_html)
            text_x = rect_x + x_margin
            for segment in segments:
                # 使用handle_multiline_text函数处理可能的多行文本
                lines, _ = handle_multiline_text(draw, segment.text, font, content_width)
                
                # 绘制每行
                for line in lines:
                    draw_text_with_style(draw, fonts, (text_x, current_y), line, segment.style)
                    current_y += int(font_size * 1.2)
            
            # 标题后增加空间
            current_y += 20 - (level * 2)
            
        elif tag.name == 'p':
            # 段落样式 - 完全重写，专注于解决混合颜色文本问题
            segments = parse_html_to_segments(tag_html)
            text_x = rect_x + x_margin
            current_y += 5  # 确保段落有一些额外的顶部间距
            
            # 更为简洁的渲染逻辑
            current_x = text_x
            line_height = 35
            line_segments = []  # 当前行的所有段落
            line_width = 0  # 当前行已使用的宽度
            max_width = content_width  # 最大可用宽度
            
            print(f"渲染段落，共{len(segments)}个片段")
            
            # 逐个处理文本片段
            for i, segment in enumerate(segments):
                # 选择字体
                font_key = 'bold' if segment.style.is_bold else 'regular'
                if segment.style.is_italic:
                    font_key = 'italic' if not segment.style.is_bold else 'bold_italic'
                font = fonts[font_key]
                
                # 处理可能包含换行符的文本
                if '\n' in segment.text:
                    # 有换行符，先处理当前行
                    if line_segments:
                        # 绘制当前行所有段落
                        render_line_segments(draw, fonts, text_x, current_y, line_segments)
                        current_y += line_height
                        line_segments = []
                        line_width = 0
                        current_x = text_x
                    
                    # 按换行符分割并处理
                    parts = segment.text.split('\n')
                    for j, part in enumerate(parts):
                        if j > 0:  # 不是第一部分，强制换行
                            if line_segments:
                                render_line_segments(draw, fonts, text_x, current_y, line_segments)
                                line_segments = []
                                line_width = 0
                            current_y += line_height
                            current_x = text_x
                        
                        if not part:  # 空行
                            continue
                        
                        # 处理这一部分文本
                        text_width = draw.textlength(part, font=font)
                        if line_width + text_width <= max_width:
                            # 可以放在当前行
                            line_segments.append((part, segment.style))
                            line_width += text_width
                            current_x += text_width
                        else:
                            # 需要换行
                            if line_segments:
                                render_line_segments(draw, fonts, text_x, current_y, line_segments)
                                line_segments = []
                                line_width = 0
                                current_y += line_height
                            
                            # 检查单个文本是否需要拆分
                            if text_width > max_width:
                                # 文本太长，需要拆分
                                words = split_text_for_wrapping(part)
                                current_part = []
                                current_part_width = 0
                                
                                for word in words:
                                    word_width = draw.textlength(word + ' ' if word != words[-1] else word, font=font)
                                    if current_part_width + word_width <= max_width:
                                        current_part.append(word)
                                        current_part_width += word_width
                                    else:
                                        # 绘制当前部分
                                        if current_part:
                                            part_text = ' '.join(current_part)
                                            draw_text_with_style(draw, fonts, (text_x, current_y), part_text, segment.style)
                                            current_y += line_height
                                        
                                        # 开始新行
                                        current_part = [word]
                                        current_part_width = word_width
                                
                                # 绘制最后一部分
                                if current_part:
                                    part_text = ' '.join(current_part)
                                    draw_text_with_style(draw, fonts, (text_x, current_y), part_text, segment.style)
                                    current_x = text_x + draw.textlength(part_text, font=font)
                                    line_width = draw.textlength(part_text, font=font)
                                    line_segments = [(part_text, segment.style)]
                            else:
                                # 单行可以放下，放到下一行
                                line_segments.append((part, segment.style))
                                line_width = text_width
                                current_x = text_x + text_width
                else:
                    # 没有换行符的普通文本
                    text_width = draw.textlength(segment.text, font=font)
                    
                    # 检查是否需要换行
                    if line_width + text_width > max_width:
                        # 当前行放不下，需要换行
                        if line_segments:
                            render_line_segments(draw, fonts, text_x, current_y, line_segments)
                            line_segments = []
                            line_width = 0
                            current_y += line_height
                        
                        # 检查单个文本是否需要拆分
                        if text_width > max_width:
                            # 文本太长，需要拆分
                            words = split_text_for_wrapping(segment.text)
                            current_part = []
                            current_part_width = 0
                            
                            for word in words:
                                word_width = draw.textlength(word + ' ' if word != words[-1] else word, font=font)
                                if current_part_width + word_width <= max_width:
                                    current_part.append(word)
                                    current_part_width += word_width
                                else:
                                    # 绘制当前部分
                                    if current_part:
                                        part_text = ' '.join(current_part)
                                        draw_text_with_style(draw, fonts, (text_x, current_y), part_text, segment.style)
                                        current_y += line_height
                                    
                                    # 开始新行
                                    current_part = [word]
                                    current_part_width = word_width
                            
                            # 绘制最后一部分
                            if current_part:
                                part_text = ' '.join(current_part)
                                draw_text_with_style(draw, fonts, (text_x, current_y), part_text, segment.style)
                                current_x = text_x + draw.textlength(part_text, font=font)
                                line_width = draw.textlength(part_text, font=font)
                                line_segments = [(part_text, segment.style)]
                        else:
                            # 单行可以放下，放到下一行
                            line_segments.append((segment.text, segment.style))
                            line_width = text_width
                            current_x = text_x + text_width
                    else:
                        # 当前行能放下
                        line_segments.append((segment.text, segment.style))
                        line_width += text_width
                        current_x += text_width
            
            # 绘制最后一行
            if line_segments:
                render_line_segments(draw, fonts, text_x, current_y, line_segments)
                current_y += line_height
            
            # 段落结束，增加行间距
            current_y += 5
            
        elif tag.name in ('ul', 'ol'):
            # 列表样式
            list_items = tag.find_all('li', recursive=False)
            list_type = 'ordered' if tag.name == 'ol' else 'unordered'
            
            # 列表前添加一些空间
            current_y += 15
            
            for i, item in enumerate(list_items):
                # 设置列表项标记
                if list_type == 'ordered':
                    bullet = f"{i+1}. "
                else:
                    bullet = "• "
                
                # 绘制列表项标记
                bullet_x = rect_x + x_margin
                item_x = bullet_x + 30  # 列表项缩进
                
                # 绘制列表项标记
                draw.text((bullet_x, current_y), bullet, fill=text_color, font=fonts['regular'])
                
                # 处理列表项内容 - 使用与段落相同的混合文本处理逻辑
                item_segments = parse_html_to_segments(str(item))
                
                # 计算可用宽度
                available_width = content_width - 30
                
                # 使用与段落相同的混合文本逻辑
                current_line_segments = []
                remaining_width = available_width
                line_y = current_y
                
                # 收集所有段内的文本段落，确保不同颜色的文本连续显示
                for segment in item_segments:
                    # 判断字体
                    font_key = 'bold' if segment.style.is_bold else 'regular'
                    font = fonts[font_key]
                    
                    # 处理文本
                    if '\n' in segment.text:
                        # 略过换行符处理，列表项通常不处理换行
                        text = segment.text.replace('\n', ' ')
                        text_width = draw.textlength(text, font=font)
                        
                        if text_width <= remaining_width:
                            # 可以放在当前行
                            current_line_segments.append((text, segment.style, text_width))
                            remaining_width -= text_width
                        else:
                            # 不能放在当前行，绘制当前行并开始新行
                            if current_line_segments:
                                draw_line_with_segments(draw, fonts, item_x, line_y, current_line_segments)
                                line_y += 35
                            
                            # 尝试分行显示
                            lines, _ = handle_multiline_text(draw, text, font, available_width)
                            for i, line in enumerate(lines):
                                if i == 0:
                                    draw_text_with_style(draw, fonts, (item_x, line_y), line, segment.style)
                                else:
                                    draw_text_with_style(draw, fonts, (item_x, line_y), line, segment.style)
                                line_y += 35
                            
                            current_line_segments = []
                            remaining_width = available_width
                    else:
                        # 没有换行符，添加到当前行
                        text_width = draw.textlength(segment.text, font=font)
                        if text_width <= remaining_width:
                            # 可以放在当前行
                            current_line_segments.append((segment.text, segment.style, text_width))
                            remaining_width -= text_width
                        else:
                            # 不能放在当前行，绘制当前行并开始新行
                            if current_line_segments:
                                draw_line_with_segments(draw, fonts, item_x, line_y, current_line_segments)
                                line_y += 35
                            
                            # 检查是否需要多行来显示这个文本
                            if text_width > available_width:
                                # 需要多行
                                lines, _ = handle_multiline_text(draw, segment.text, font, available_width)
                                for line in lines:
                                    draw_text_with_style(draw, fonts, (item_x, line_y), line, segment.style)
                                    line_y += 35
                                current_line_segments = []
                                remaining_width = available_width
                            else:
                                # 单行即可
                                current_line_segments = [(segment.text, segment.style, text_width)]
                                remaining_width = available_width - text_width
            
                # 绘制最后一行
                if current_line_segments:
                    draw_line_with_segments(draw, fonts, item_x, line_y, current_line_segments)
                    line_y += 35
                
                # 更新当前Y位置为列表项绘制的最后位置
                current_y = line_y
                
                # 检查是否有嵌套列表 - 保留原有的嵌套列表处理逻辑
                nested_lists = item.find_all(['ul', 'ol'], recursive=False)
                if nested_lists:
                    # 递归处理嵌套列表
                    for nested_list in nested_lists:
                        nested_type = 'ordered' if nested_list.name == 'ol' else 'unordered'
                        nested_items = nested_list.find_all('li', recursive=False)
                        
                        for j, nested_item in enumerate(nested_items):
                            # 设置嵌套列表项标记
                            if nested_type == 'ordered':
                                nested_bullet = f"{j+1}. "
                            else:
                                nested_bullet = "◦ "  # 使用不同的符号
                            
                            # 嵌套列表缩进更多
                            nested_bullet_x = item_x + 20
                            nested_item_x = nested_bullet_x + 30
                            
                            # 绘制嵌套列表项标记
                            draw.text((nested_bullet_x, current_y), nested_bullet, fill=text_color, font=fonts['regular'])
                            
                            # 处理嵌套列表项内容 - 使用相同的混合文本处理逻辑
                            nested_segments = parse_html_to_segments(str(nested_item))
                            nested_available_width = available_width - 50
                            
                            # 嵌套列表项的混合文本处理
                            nested_line_segments = []
                            nested_remaining_width = nested_available_width
                            nested_line_y = current_y
                            
                            for nested_segment in nested_segments:
                                nested_font_key = 'bold' if nested_segment.style.is_bold else 'regular'
                                nested_font = fonts[nested_font_key]
                                
                                # 处理文本
                                if '\n' in nested_segment.text:
                                    # 略过换行符处理
                                    nested_text = nested_segment.text.replace('\n', ' ')
                                    nested_text_width = draw.textlength(nested_text, font=nested_font)
                                    
                                    if nested_text_width <= nested_remaining_width:
                                        nested_line_segments.append((nested_text, nested_segment.style, nested_text_width))
                                        nested_remaining_width -= nested_text_width
                                    else:
                                        # 不能放在当前行，绘制当前行并开始新行
                                        if nested_line_segments:
                                            draw_line_with_segments(draw, fonts, nested_item_x, nested_line_y, nested_line_segments)
                                            nested_line_y += 35
                                        
                                        # 尝试分行显示
                                        nested_lines, _ = handle_multiline_text(draw, nested_text, nested_font, nested_available_width)
                                        for line in nested_lines:
                                            draw_text_with_style(draw, fonts, (nested_item_x, nested_line_y), line, nested_segment.style)
                                            nested_line_y += 35
                                        
                                        nested_line_segments = []
                                        nested_remaining_width = nested_available_width
                                else:
                                    # 没有换行符，添加到当前行
                                    nested_text_width = draw.textlength(nested_segment.text, font=nested_font)
                                    if nested_text_width <= nested_remaining_width:
                                        # 可以放在当前行
                                        nested_line_segments.append((nested_segment.text, nested_segment.style, nested_text_width))
                                        nested_remaining_width -= nested_text_width
                                    else:
                                        # 不能放在当前行，绘制当前行并开始新行
                                        if nested_line_segments:
                                            draw_line_with_segments(draw, fonts, nested_item_x, nested_line_y, nested_line_segments)
                                            nested_line_y += 35
                                        
                                        # 检查是否需要多行来显示这个文本
                                        if nested_text_width > nested_available_width:
                                            # 需要多行
                                            nested_lines, _ = handle_multiline_text(draw, nested_segment.text, nested_font, nested_available_width)
                                            for line in nested_lines:
                                                draw_text_with_style(draw, fonts, (nested_item_x, nested_line_y), line, nested_segment.style)
                                                nested_line_y += 35
                                            nested_line_segments = []
                                            nested_remaining_width = nested_available_width
                                        else:
                                            # 单行即可
                                            nested_line_segments = [(nested_segment.text, nested_segment.style, nested_text_width)]
                                            nested_remaining_width = nested_available_width - nested_text_width
                        
                            # 绘制最后一行
                            if nested_line_segments:
                                draw_line_with_segments(draw, fonts, nested_item_x, nested_line_y, nested_line_segments)
                                nested_line_y += 35
                            
                            # 更新当前Y位置
                            current_y = nested_line_y
                
                # 在列表项之间添加一些间距
                current_y += 10
            
            # 列表后增加空间
            current_y += 15
            
        elif tag.name == 'blockquote':
            # 引用块样式
            quote_x = rect_x + x_margin + 20
            quote_width = content_width - 40
            
            # 使用更明显的颜色
            quote_color = (120, 120, 120) if is_dark_theme else (100, 100, 100)
            
            # 绘制引用块边框
            quote_start_y = current_y
            quote_segments = parse_html_to_segments(tag_html)
            
            # 计算引用块总高度
            quote_height = 0
            for segment in quote_segments:
                font_key = 'bold' if segment.style.is_bold else 'regular'
                font = fonts[font_key]
                
                # 使用handle_multiline_text函数计算高度
                _, segment_height = handle_multiline_text(draw, segment.text, font, quote_width)
                quote_height += segment_height
            
            # 确保至少有最小高度
            quote_height = max(quote_height, 35)
            
            # 绘制引用块的左侧边框 - 使用更粗的线条
            quote_bar_x = quote_x - 15
            # 增加边框宽度和明显性
            draw.rectangle([quote_bar_x, quote_start_y, quote_bar_x + 5, quote_start_y + quote_height + 20], fill=quote_color)
            
            # 绘制引用内容
            for segment in quote_segments:
                font_key = 'bold' if segment.style.is_bold else 'regular'
                font = fonts[font_key]
                segment_style = TextStyle(color=quote_color, is_bold=segment.style.is_bold, is_italic=segment.style.is_italic)
                
                # 使用handle_multiline_text函数处理可能的多行文本
                lines, _ = handle_multiline_text(draw, segment.text, font, quote_width)
                
                # 绘制每行
                for line in lines:
                    draw_text_with_style(draw, fonts, (quote_x, current_y), line, segment_style)
                    current_y += 35
            
            # 引用块后增加空间
            current_y += 20
            
        elif tag.name == 'pre':
            # 代码块样式
            code_block_x = rect_x + x_margin
            code_block_width = content_width
            code_block_padding = 20
            
            # 提取代码内容
            code_tag = tag.find('code')
            code_content = code_tag.get_text() if code_tag else tag.get_text()
            
            # 确保代码内容没有前后空白行
            code_lines = [line for line in code_content.split('\n') if line.strip() or line in code_content.split('\n')]
            
            # 计算代码块高度
            code_line_height = 30
            code_block_height = max(len(code_lines) * code_line_height, code_line_height) + 2 * code_block_padding
            
            # 绘制代码块背景 - 使用更深的背景色
            code_block_y = current_y
            code_bg_color = (30, 30, 30) if is_dark_theme else (240, 240, 240)  # 更深的背景色
            code_text_color = (230, 230, 230) if is_dark_theme else (60, 60, 60)  # 更亮的文字颜色
            
            # 创建圆角代码块 - 圆角半径减小
            create_rounded_rectangle(
                final_image, 
                code_block_x, code_block_y, 
                code_block_width, code_block_height,
                radius=5,  # 减小圆角半径
                bg_color=code_bg_color
            )
            
            # 绘制代码内容
            text_y = code_block_y + code_block_padding
            
            # 处理每行代码
            for line in code_lines:
                # 安全绘制代码行，避免多行文本问题
                if line.strip():
                    available_code_width = code_block_width - 2 * code_block_padding
                    
                    # 检查行是否需要换行
                    line_width = safe_textlength(draw, line, fonts['regular'])
                    if line_width <= available_code_width:
                        # 无需换行
                        draw.text((code_block_x + code_block_padding, text_y), line, fill=code_text_color, font=fonts['regular'])
                    else:
                        # 需要换行处理
                        words = split_text_for_wrapping(line)
                        current_line = []
                        current_width = 0
                        
                        for word in words:
                            word_width = safe_textlength(draw, word + ' ', fonts['regular'])
                            if current_width + word_width <= available_code_width:
                                current_line.append(word)
                                current_width += word_width
                            else:
                                # 绘制当前行
                                if current_line:
                                    draw.text(
                                        (code_block_x + code_block_padding, text_y),
                                        ' '.join(current_line),
                                        fill=code_text_color,
                                        font=fonts['regular']
                                    )
                                    text_y += code_line_height
                                current_line = [word]
                                current_width = word_width
                        
                        # 绘制最后一行
                        if current_line:
                            draw.text(
                                (code_block_x + code_block_padding, text_y),
                                ' '.join(current_line),
                                fill=code_text_color,
                                font=fonts['regular']
                            )
            
                text_y += code_line_height
            
            # 更新当前位置
            current_y = code_block_y + code_block_height + 30
    
    # 保存结果
    final_image.save(output_path)
    print(f"图片已保存到: {output_path}")
    
    return final_image

def is_cjk(char):
    """检查字符是否为中日韩文字"""
    # 中日韩统一表意文字基本区域
    if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:
        return True
    # 中日韩统一表意文字扩展A区
    if ord(char) >= 0x3400 and ord(char) <= 0x4DBF:
        return True
    # 中日韩统一表意文字扩展B区
    if ord(char) >= 0x20000 and ord(char) <= 0x2A6DF:
        return True
    # 中日韩统一表意文字扩展C区
    if ord(char) >= 0x2A700 and ord(char) <= 0x2B73F:
        return True
    # 中日韩统一表意文字扩展D区
    if ord(char) >= 0x2B740 and ord(char) <= 0x2B81F:
        return True
    # 中日韩统一表意文字扩展E区
    if ord(char) >= 0x2B820 and ord(char) <= 0x2CEAF:
        return True
    # 中日韩兼容表意文字
    if ord(char) >= 0xF900 and ord(char) <= 0xFAFF:
        return True
    return False

def split_text_for_wrapping(text):
    """将文本分割成适合换行的单元"""
    words = []
    current_word = ''
    max_word_length = 15  # 限制连续字符的最大长度
    
    for char in text:
        # 处理换行符
        if char == '\n':
            if current_word:
                words.append(current_word)
                current_word = ''
            words.append('\n')  # 将换行符作为单独的标记
        # 处理emoji
        elif is_emoji(char):
            if current_word:
                words.append(current_word)
                current_word = ''
            words.append(char)  # emoji作为单独的词
        # 处理标点符号和空格
        elif char in [' ', '，', '。', '：', '、', '！', '？', '；', ',', '.', ':', ';', '!', '?']:
            if current_word:
                words.append(current_word)
            words.append(char)
            current_word = ''
        # 处理中文字符
        elif is_cjk(char):
            if current_word:
                words.append(current_word)
                current_word = ''
            words.append(char)  # 中文字符单独成词
        # 处理连续数字和字母
        else:
            current_word += char
            # 如果连续字符过长，则强制分割
            if len(current_word) >= max_word_length:
                words.append(current_word)
                current_word = ''
    
    if current_word:
        words.append(current_word)
    
    return words

def safe_textlength(draw, text, font):
    """安全地测量文本长度，处理可能包含换行符的情况"""
    if '\n' in text:
        # 如果文本包含换行符，只测量第一行
        return draw.textlength(text.split('\n')[0], font=font)
    return draw.textlength(text, font=font)

# 兼容接口，供测试使用
def generate_image(text, output_path):
    """兼容原有generate_image函数的接口"""
    return render_markdown_to_image(text, output_path)

# 测试函数
def test_enhanced_renderer():
    """测试增强版渲染器"""
    # 测试文本，包含各种Markdown元素和颜色标签
    text = """# Markdown元素完整测试

## 1. 标题样式
# 一级标题
## 二级标题
### 三级标题

## 2. 文本格式
**粗体文本** 和 *斜体文本* 以及 ***粗斜体文本***
~~删除线文本~~ 和 `行内代码`

## 3. 彩色文本
<span style="color:red">红色文本</span>
<span style="color:blue">蓝色文本</span>
<span style="color:green">绿色文本</span>
<span style="color:orange">橙色文本</span>
<span style="color:purple">紫色文本</span>
<span style="color:teal">青色文本</span>

## 4. 混合格式
<span style="color:red">**红色粗体**</span> 和 <span style="color:blue">*蓝色斜体*</span>

## 5. 列表
### 无序列表:
* 苹果
* 香蕉
* 橙子

### 有序列表:
1. 第一项
2. 第二项
3. 第三项

## 6. 表格
| 姓名 | 年龄 | 职业 |
|------|------|------|
| 张三 | 28 | <span style="color:blue">工程师</span> |
| 李四 | 32 | <span style="color:green">设计师</span> |
| 王五 | 45 | <span style="color:red">经理</span> |

## 7. 引用
> 这是一段引用文本
> 引用可以有多行

## 8. Emoji表情
🎉 🚀 🌟 🔥 💡 📝 👍 🌈

—By 飞天"""
    
    output_path = "enhanced_test.png"
    render_markdown_to_image(text, output_path)
    print(f"增强版渲染测试完成！图片已保存到: {output_path}")

# 添加一个辅助函数来绘制包含多个文本段的一行
def draw_line_with_segments(draw, fonts, x, y, segments):
    """绘制包含多个文本段（可能有不同颜色）的一行"""
    current_x = x
    
    # 添加调试信息
    print(f"绘制行，共{len(segments)}个段落：")
    
    # 实际绘制每个片段，确保它们紧密相连
    for i, (text, style, _) in enumerate(segments):
        # 为每个片段选择正确的字体
        font_key = 'bold' if style.is_bold else 'regular'
        if style.is_italic:
            font_key = 'italic' if not style.is_bold else 'bold_italic'
        font = fonts[font_key]
        
        # 重新计算文本宽度以确保精确定位
        text_width = draw.textlength(text, font=font)
        
        # 确保颜色正确
        color = style.color
        print(f"段落{i}: '{text}', 颜色: {color}, 字体: {font_key}")
        
        # 绘制文本
        draw_text_with_style(draw, fonts, (current_x, y), text, style)
        current_x += text_width

# 添加一个函数专门用于渲染一行中的所有文本段落
def render_line_segments(draw, fonts, x, y, segments):
    """绘制一行中的所有文本段落，确保它们正确连接"""
    current_x = x
    
    for text, style in segments:
        # 获取正确的字体
        font_key = 'bold' if style.is_bold else 'regular'
        if style.is_italic:
            font_key = 'italic' if not style.is_bold else 'bold_italic'
        font = fonts[font_key]
        
        # 绘制文本
        draw_text_with_style(draw, fonts, (current_x, y), text, style)
        
        # 更新位置
        current_x += draw.textlength(text, font=font)

if __name__ == "__main__":
    test_enhanced_renderer() 