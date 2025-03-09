import os
import re
import random
import time
import uuid
import io
import requests
from typing import Optional, Tuple, List, Dict
from PIL import Image, ImageDraw, ImageFont, ImageColor
import emoji

class TextStyle:
    """文本样式定义"""
    def __init__(self, font_name='regular', font_size=30, color='black', is_bold=False, is_italic=False):
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.is_bold = is_bold
        self.is_italic = is_italic

class TextSegment:
    """文本段落定义"""
    def __init__(self, text, style):
        self.text = text
        self.style = style

def get_random_gradient():
    """获取随机渐变背景颜色和方向"""
    # 确保每次生成真正随机的结果
    random.seed(time.time() + random.random() * 1000 + hash(uuid.uuid4()))
    
    gradients = [
        # 柔和渐变对
        ((245, 245, 245), (230, 230, 240)),  # 浅灰到淡紫
        ((245, 255, 250), (230, 240, 255)),  # 浅绿到淡蓝
        ((255, 245, 245), (255, 230, 240)),  # 浅粉到淡红
        ((250, 250, 255), (240, 240, 250)),  # 淡蓝到浅灰
        ((255, 250, 240), (255, 240, 220)),  # 淡橙到浅黄
        ((240, 255, 240), (220, 245, 220)),  # 淡绿到浅绿
        ((250, 240, 255), (240, 230, 250)),  # 淡紫到浅紫
        ((240, 250, 255), (230, 240, 250)),  # 淡青到浅蓝
    ]
    
    # 随机渐变方向：0=垂直, 1=水平, 2=对角线左上到右下, 3=对角线右上到左下
    direction = random.randint(0, 3)
    
    return random.choice(gradients), direction

def create_gradient_background(width, height):
    """创建渐变背景"""
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    (start_color, end_color), direction = get_random_gradient()
    
    if direction == 0:  # 垂直渐变
        for y in range(height):
            r = int(start_color[0] * (1 - y/height) + end_color[0] * (y/height))
            g = int(start_color[1] * (1 - y/height) + end_color[1] * (y/height))
            b = int(start_color[2] * (1 - y/height) + end_color[2] * (y/height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    elif direction == 1:  # 水平渐变
        for x in range(width):
            r = int(start_color[0] * (1 - x/width) + end_color[0] * (x/width))
            g = int(start_color[1] * (1 - x/width) + end_color[1] * (x/width))
            b = int(start_color[2] * (1 - x/width) + end_color[2] * (x/width))
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    elif direction == 2:  # 对角线左上到右下
        max_dist = (width**2 + height**2)**0.5
        for y in range(height):
            for x in range(width):
                dist = ((x**2 + y**2)**0.5) / max_dist
                r = int(start_color[0] * (1 - dist) + end_color[0] * dist)
                g = int(start_color[1] * (1 - dist) + end_color[1] * dist)
                b = int(start_color[2] * (1 - dist) + end_color[2] * dist)
                draw.point((x, y), fill=(r, g, b))
    
    else:  # 对角线右上到左下
        max_dist = (width**2 + height**2)**0.5
        for y in range(height):
            for x in range(width):
                dist = (((width-x)**2 + y**2)**0.5) / max_dist
                r = int(start_color[0] * (1 - dist) + end_color[0] * dist)
                g = int(start_color[1] * (1 - dist) + end_color[1] * dist)
                b = int(start_color[2] * (1 - dist) + end_color[2] * dist)
                draw.point((x, y), fill=(r, g, b))
    
    return image

def load_fonts():
    """加载字体"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fonts = {
        'regular': ImageFont.truetype(os.path.join(current_dir, 'msyh.ttc'), 30),
        'bold': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 30),
        'title': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 40),
        'list': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 30),
        'h1': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 45),
        'h2': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 36),
        'h3': ImageFont.truetype(os.path.join(current_dir, 'msyhbd.ttc'), 32),
        'emoji': ImageFont.truetype(os.path.join(current_dir, 'TwitterColorEmoji.ttf'), 30),
        'code': ImageFont.truetype(os.path.join(current_dir, 'msyh.ttc'), 28),  # 代码字体稍小
    }
    return fonts

def is_emoji(char):
    """检查字符是否为emoji，支持组合emoji"""
    if not char:
        return False
    if len(char) == 1:
        return emoji.is_emoji(char) or ord(char) > 0x1F000
    else:
        # 尝试检测多字符emoji (如国旗等)
        return any(emoji.is_emoji(c) or ord(c) > 0x1F000 for c in char if c)

def simple_draw_emoji(draw, image, x, y, emoji_char, size=30):
    """使用简单方法绘制emoji，避免复杂处理"""
    try:
        # 直接使用emoji字体绘制
        font = ImageFont.truetype(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TwitterColorEmoji.ttf'), 
            size
        )
        
        # 多次绘制以增强可见性
        colors = ['black', '#333333', '#666666']
        for color in colors:
            draw.text((x, y), emoji_char, fill=color, font=font)
        
        return size  # 返回标准emoji宽度
    except Exception as e:
        # 回退到系统字体
        font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'msyh.ttc'), size)
        draw.text((x, y), emoji_char, fill='black', font=font)
        return draw.textlength(emoji_char, font=font)

def draw_text_with_color(draw, image, fonts, pos, text, color='black', is_bold=False, is_italic=False):
    """绘制带颜色和样式的文本，支持emoji"""
    x, y = pos
    total_width = 0
    
    # 逐字符绘制，确保支持emoji
    i = 0
    while i < len(text):
        char = text[i]
        
        # 尝试检测emoji（可能是由多个字符组成的）
        emoji_end = i + 1
        emoji_detected = False
        
        # 优先尝试更长的字符串组合，因为有些emoji由多个Unicode组成
        for j in range(min(i + 4, len(text)), i, -1):
            if is_emoji(text[i:j]):
                emoji_char = text[i:j]
                char_width = simple_draw_emoji(draw, image, x, y, emoji_char, 30)
                i = j
                emoji_detected = True
                break
        
        if not emoji_detected:
            # 单字符是emoji
            if is_emoji(char):
                char_width = simple_draw_emoji(draw, image, x, y, char, 30)
            else:
                # 普通文本
                if is_bold:
                    font = fonts['bold']
                else:
                    font = fonts['regular']
                
                # 测量字符宽度
                char_width = draw.textlength(char, font=font)
                
                # 绘制字符
                draw.text((x, y), char, fill=color, font=font)
                
                # 绘制粗体效果（如果需要且没有专门的粗体字体）
                if is_bold and font == fonts['regular']:
                    draw.text((x+1, y), char, fill=color, font=font)  # 简单粗体效果
                
                # 绘制斜体效果（通过稍微调整位置）
                if is_italic:
                    slant_factor = 0.2
                    try:
                        char_height = font.getbbox(char)[3]  # 使用getbbox代替getsize
                        draw.text((x + int(char_height * slant_factor), y), char, fill=color, font=font)
                    except:
                        # 如果无法获取字符高度，使用字体大小代替
                        char_height = 30
                        draw.text((x + int(char_height * slant_factor), y), char, fill=color, font=font)
            
            i += 1
        
        # 更新位置
        x += char_width
        total_width += char_width
        
    return total_width

def apply_color_to_text(text, color_name):
    """根据颜色名称应用HTML颜色标签"""
    color_map = {
        '红色': 'red',
        '蓝色': 'blue',
        '绿色': 'green',
        '黄色': 'yellow',
        '紫色': 'purple',
        '橙色': 'orange',
        '粉色': 'pink',
        '青色': 'cyan',
        '灰色': 'gray',
        '棕色': 'brown',
        '黑色': 'black',
        '白色': 'white',
        '珊瑚色': 'coral',
    }
    
    # 查找中文颜色名或直接使用英文名
    color_code = color_map.get(color_name, color_name)
    
    return f'<span style="color:{color_code}">{text}</span>'

def process_markdown(text):
    """预处理Markdown文本，转换为内部标记格式"""
    # 先处理HTML特殊字符转义，避免后续干扰
    processed_text = text.replace('&lt;', '<').replace('&gt;', '>')
    
    # 特殊处理颜色标记的组合形式
    # 粗体+颜色组合
    processed_text = re.sub(r'\*\*(蓝色|红色|绿色|黄色|紫色|橙色|粉色|青色|灰色|棕色|黑色|白色|珊瑚色)(.*?)\*\*', 
                           lambda m: f'<span style="bold"><span style="color:{apply_color_to_text("", m.group(1)).split("color:")[1].split("}")[0]}">{m.group(2)}</span></span>', 
                           processed_text)
    
    # 斜体+颜色组合
    processed_text = re.sub(r'\*(蓝色|红色|绿色|黄色|紫色|橙色|粉色|青色|灰色|棕色|黑色|白色|珊瑚色)(.*?)\*', 
                           lambda m: f'<span style="italic"><span style="color:{apply_color_to_text("", m.group(1)).split("color:")[1].split("}")[0]}">{m.group(2)}</span></span>', 
                           processed_text)
    
    # 处理加粗 **text** 或 __text__
    processed_text = re.sub(r'\*\*(.*?)\*\*|__(.*?)__', 
                           lambda m: f'<span style="bold">{m.group(1) or m.group(2)}</span>', 
                           processed_text)
    
    # 处理斜体 *text* 或 _text_
    processed_text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.*?)(?<!_)_(?!_)', 
                           lambda m: f'<span style="italic">{m.group(1) or m.group(2)}</span>', 
                           processed_text)
    
    # 处理删除线 ~~text~~
    processed_text = re.sub(r'~~(.*?)~~', 
                           lambda m: f'<span style="strikethrough">{m.group(1)}</span>', 
                           processed_text)
    
    # 处理代码 `text`
    processed_text = re.sub(r'`(.*?)`', 
                           lambda m: f'<span style="code">{m.group(1)}</span>', 
                           processed_text)
    
    # 处理链接 [text](url)
    processed_text = re.sub(r'\[(.*?)\]\((.*?)\)', 
                           lambda m: f'{m.group(1)} (链接: {m.group(2)})', 
                           processed_text)
    
    
    # 保留HTML颜色标签
    color_span_pattern = r'<span\\s+style=[\"\']color:\\s*([^;\"\'\\s]+)[;\"\'].*?>(.*?)</span>'
    placeholders = {}
    
    # 临时替换颜色标签，避免被其他处理干扰
    for i, match in enumerate(re.finditer(color_span_pattern, processed_text)):
        placeholder = f"__COLOR_SPAN_{i}__"
        placeholders[placeholder] = match.group(0)
        processed_text = processed_text.replace(match.group(0), placeholder)
    
    # 处理完其他Markdown标签后，恢复颜色标签
    for placeholder, original in placeholders.items():
        processed_text = processed_text.replace(placeholder, original)
    
    return processed_text

def clean_html_tags(text):
    """清理文本中未处理的HTML标签，但保留颜色和样式标记"""
    # 保留我们特殊处理的标签
    preserved_tags = [
        r'<span\s+style=["\']color:\s*([^;"\'\s]+)[;"\'](.*?)>(.*?)</span>',
        r'<span\s+style=["\']bold["\']>(.*?)</span>',
        r'<span\s+style=["\']italic["\']>(.*?)</span>',
        r'<span\s+style=["\']strikethrough["\']>(.*?)</span>',
        r'<span\s+style=["\']code["\']>(.*?)</span>'
    ]
    
    # 创建占位符字典和替换后的文本
    placeholders = {}
    processed_text = text
    
    # 替换需要保留的标签为占位符
    for i, pattern in enumerate(preserved_tags):
        matches = list(re.finditer(pattern, processed_text, re.DOTALL))
        for j, match in enumerate(matches):
            placeholder = f"__PRESERVED_TAG_{i}_{j}__"
            placeholders[placeholder] = match.group(0)
            processed_text = processed_text.replace(match.group(0), placeholder, 1)
    
    # 清理其他HTML标签
    processed_text = re.sub(r'<[^>]*>', '', processed_text)
    
    # 恢复保留的标签
    for placeholder, original in placeholders.items():
        processed_text = processed_text.replace(placeholder, original)
    
    return processed_text

def split_text_to_paragraphs(text):
    """分割文本为段落列表，支持更多Markdown格式"""
    # 预处理Markdown标记
    processed_text = process_markdown(text)
    
    # 清理不需要直接显示的HTML标签
    processed_text = clean_html_tags(processed_text)
    
    paragraphs = []
    
    # 按空行分割文本
    raw_paragraphs = re.split(r'\n\s*\n', processed_text)
    
    for p in raw_paragraphs:
        p = p.strip()
        if not p:
            continue
            
        # 检查是否是标题
        if p.startswith('# '):
            paragraphs.append(('h1', p[2:]))
        elif p.startswith('## '):
            paragraphs.append(('h2', p[3:]))
        elif p.startswith('### '):
            paragraphs.append(('h3', p[4:]))
        # 检查是否是有序列表项组
        elif re.match(r'^\d+\.\s+', p):
            list_items = p.split('\n')
            in_list = False
            
            for item in list_items:
                item = item.strip()
                if not item:
                    continue
                    
                if re.match(r'^\d+\.\s+', item):
                    in_list = True
                    paragraphs.append(('list_item', item))
                elif in_list and item.startswith('  '):
                    # 列表项下的子内容，作为普通段落但缩进
                    paragraphs.append(('indented_paragraph', item.strip()))
                else:
                    paragraphs.append(('paragraph', item))
        # 检查是否是无序列表项组
        elif re.match(r'^[\*\-\+]\s+', p):
            list_items = p.split('\n')
            in_list = False
            
            for item in list_items:
                item = item.strip()
                if not item:
                    continue
                    
                if re.match(r'^[\*\-\+]\s+', item):
                    in_list = True
                    # 提取无序列表项内容
                    content = re.sub(r'^[\*\-\+]\s+', '', item)
                    paragraphs.append(('unordered_list_item', content))
                elif in_list and item.startswith('  '):
                    # 列表项下的子内容，作为普通段落但缩进
                    paragraphs.append(('indented_paragraph', item.strip()))
                else:
                    paragraphs.append(('paragraph', item))
        # 检查是否是代码块
        elif p.startswith('```') and p.endswith('```'):
            if p.startswith('```javascript') or p.startswith('```python') or p.startswith('```java'):
                language = p.split('\n')[0][3:].strip()
                code_content = '\n'.join(p.split('\n')[1:-1])
                paragraphs.append(('code_block', {'language': language, 'content': code_content}))
            else:
                code_content = p[3:-3].strip()
                paragraphs.append(('code_block', {'language': '', 'content': code_content}))
        # 检查是否是表格
        elif '|' in p and ('----|' in p or p.count('|') >= 2):
            paragraphs.append(('table', p))
        else:
            # 普通段落
            paragraphs.append(('paragraph', p))
    
    # 优化布局
    return optimize_layout(paragraphs)

def has_signature(text, signature="—By 飞天"):
    """检查文本是否已包含签名"""
    return signature in text

def calculate_dynamic_height(content_height, card_margin=40):
    """计算动态高度，根据内容自适应"""
    # 内容高度加上上下边距
    total_height = content_height + card_margin * 2 + 80  # 上下内边距各40
    
    # 设置最小和最大高度
    min_height = 600
    max_height = 1200
    
    # 自适应高度(600-1200之间)
    height = max(min(total_height, max_height), min_height)
    
    # 对高度进行取整，确保是8的倍数(美观)
    height = (height // 8) * 8
    
    return height

def smart_text_wrap(draw, text, max_width, font, indent=0):
    """智能文本换行，考虑中文和英文单词边界"""
    if not text:
        return []
    
    # 对于纯ASCII文本，按单词换行
    if all(ord(c) < 128 for c in text):
        lines = []
        # 先按换行符分割
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph:  # 空段落直接添加空行
                lines.append('')
                continue
                
            words = paragraph.split()
            if not words:  # 如果段落只有空格
                lines.append('')
                continue
                
            current_line = []
            current_width = indent
            
            for word in words:
                try:
                    word_width = draw.textlength(word, font=font)
                    space_width = draw.textlength(' ', font=font)
                except ValueError:
                    # 如果出现错误，使用估计值
                    word_width = sum(font.getsize(c)[0] for c in word) if hasattr(font, 'getsize') else len(word) * 10
                    space_width = font.getsize(' ')[0] if hasattr(font, 'getsize') else 5
                
                if current_width + word_width <= max_width:
                    current_line.append(word)
                    current_width += word_width + space_width
                else:
                    if current_line:  # 如果当前行有内容
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = indent + word_width + space_width
            
            if current_line:  # 添加最后一行
                lines.append(' '.join(current_line))
        
        return lines
    
    # 对于包含中文的文本，按字符尝试换行
    else:
        lines = []
        current_line = ''
        current_width = indent
        
        i = 0
        while i < len(text):
            char = text[i]
            # 确保只对单个字符进行测量，避免多行文本错误
            if '\n' in char:
                # 如果字符包含换行符，直接添加当前行并开始新行
                lines.append(current_line)
                current_line = ''
                current_width = indent
                i += 1
                continue
            
            try:
                char_width = draw.textlength(char, font=font)
            except ValueError:
                # 如果出现错误，使用估计值
                char_width = font.getsize(char)[0] if hasattr(font, 'getsize') else 10
            
            # 如果添加这个字符会超出最大宽度，则开始新行
            if current_width + char_width > max_width:
                lines.append(current_line)
                current_line = ''
                current_width = indent
                # 非中文单词不拆分
                if not is_cjk_char(char) and i > 0 and not is_cjk_char(text[i-1]):
                    # 找到前一个单词的开始位置
                    word_start = i
                    while word_start > 0 and not is_cjk_char(text[word_start-1]) and not text[word_start-1].isspace():
                        word_start -= 1
                    # 如果这个单词已经在当前行，则将整个单词移到下一行
                    if word_start < i and not text[word_start-1].isspace():
                        current_line = text[word_start:i]
                        current_width = sum(draw.textlength(c, font=font) for c in current_line)
                        continue
            
            current_line += char
            current_width += char_width
            i += 1
        
        if current_line:  # 添加最后一行
            lines.append(current_line)
        
        return lines

def is_cjk_char(char):
    """判断是否为中日韩文字"""
    if not char:
        return False
    
    # CJK统一汉字 + 中日韩符号和标点 + 全角ASCII、半角片假名、半角谚文字母
    cjk_ranges = [
        (0x4E00, 0x9FFF),   # CJK统一汉字
        (0x3000, 0x303F),   # CJK符号和标点
        (0xFF00, 0xFFEF),   # 全角ASCII、半角片假名、半角谚文字母
        (0x3040, 0x309F),   # 平假名
        (0x30A0, 0x30FF),   # 片假名
        (0x3100, 0x312F),   # 注音符号
        (0xAC00, 0xD7AF)    # 谚文
    ]
    
    code = ord(char)
    return any(start <= code <= end for start, end in cjk_ranges)

def optimize_line_breaks(lines, max_width, max_lines=None):
    """优化断行，使文本更美观"""
    if not lines:
        return lines
    
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines-1]
        if len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-3] + '...'
        else:
            lines[-1] += '...'
    
    return lines

def generate_simple_image_with_color(text, output_path, title_image=None):
    """使用PIL生成带彩色文本的图像"""
    # 设置图像宽度
    width = 800
    
    # 加载字体
    fonts = load_fonts()
    
    # 分割文本为段落
    paragraphs = split_text_to_paragraphs(text)
    
    # 检查文本是否已包含签名
    contains_signature = has_signature(text)
    
    # 预设卡片外边距
    card_margin = 40
    card_width = width - 2 * card_margin
    
    # 计算内容高度
    content_height = 0
    test_image = Image.new('RGB', (width, 1), color=(255, 255, 255))
    test_draw = ImageDraw.Draw(test_image)
    
    x = card_margin + 40
    y = card_margin + 40
    max_width = card_width - 80  # 减少最大宽度，确保文本不会超出边界
    
    # 模拟逐段落绘制以计算高度
    for p_type, p_text in paragraphs:
        if p_type == 'h1':
            content_height += 70  # 大标题更高
        elif p_type == 'h2':
            content_height += 60  # 二级标题
        elif p_type == 'h3':
            content_height += 50  # 三级标题
        elif p_type == 'spacing':
            content_height += p_text  # 添加特定高度的空间
        elif p_type == 'list_item' or p_type == 'unordered_list_item':
            # 解析列表项
            if p_type == 'list_item':
                match = re.match(r'^(\d+)\.(\s+)(.+)$', p_text)
                if match:
                    number = match.group(1)
                    content = match.group(3)
                    
                    # 测量序号宽度
                    number_width = test_draw.textlength(f"{number}.", font=fonts['list'])
            else:
                content = p_text
                number_width = test_draw.textlength("• ", font=fonts['list'])
            
            # 解析内容中的颜色标签
            segments = parse_color_tags(content)
            
            # 使用智能文本换行
            wrapped_lines = []
            for segment in segments:
                font_key = 'bold' if segment.style.is_bold else 'regular'
                segment_lines = smart_text_wrap(
                    test_draw, 
                    segment.text, 
                    max_width - number_width - 20,  # 减少宽度，确保不会超出边界
                    fonts[font_key], 
                    indent=0
                )
                wrapped_lines.extend(segment_lines)
            
            # 计算列表项高度
            list_item_height = len(wrapped_lines) * 40
            content_height += list_item_height
        elif p_type == 'code_block':
            # 计算代码块高度
            if isinstance(p_text, dict):
                code_content = p_text.get('content', '')
            else:
                code_content = p_text
                
            code_lines = code_content.split('\n')
            code_height = len(code_lines) * 40 + 40  # 加上顶部和底部的间距
            content_height += code_height
        elif p_type == 'table':
            # 表格高度计算
            table_rows = p_text.split('\n')
            table_height = len(table_rows) * 40 + 20  # 每行40像素加上边距
            content_height += table_height
        else:
            # 普通段落 - 使用智能换行
            if isinstance(p_text, str):
                segments = parse_color_tags(p_text)
                
                wrapped_lines = []
                for segment in segments:
                    font_key = 'bold' if segment.style.is_bold else 'regular'
                    segment_lines = smart_text_wrap(
                        test_draw, 
                        segment.text, 
                        max_width, 
                        fonts[font_key]
                    )
                    wrapped_lines.extend(segment_lines)
                
                # 优化断行，使文本更美观
                wrapped_lines = optimize_line_breaks(wrapped_lines, max_width)
                
                # 计算段落总高度
                line_height = 40
                paragraph_height = len(wrapped_lines) * line_height + 10 if wrapped_lines else line_height + 10
                content_height += paragraph_height
    
    # 计算签名所需高度及底部边距
    signature_height = 60 if not contains_signature else 0
    bottom_margin = 40
    
    # 使用动态高度计算函数
    height = calculate_dynamic_height(content_height + bottom_margin + signature_height, card_margin)
    
    # 创建渐变背景
    image = create_gradient_background(width, height)
    draw = ImageDraw.Draw(image)
    
    # 计算自适应卡片高度
    card_height = height - 2 * card_margin
    card_x = card_margin
    card_y = card_margin
    
    # 创建圆角矩形函数
    def rounded_rectangle(draw, rect, radius, fill):
        x1, y1, x2, y2 = rect
        draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill)
        draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill)
        draw.pieslice((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=fill)
        draw.pieslice((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 0, fill=fill)
        draw.pieslice((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=fill)
        draw.pieslice((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=fill)
    
    # 绘制卡片背景
    rounded_rectangle(draw, (card_x, card_y, card_x + card_width, card_y + card_height), 20, (255, 255, 255, 220))
    
    # 设置绘制起点
    x = card_x + 40
    y = card_y + 40
    max_width = card_width - 80
    
    # 逐段落绘制
    for p_type, p_text in paragraphs:
        if p_type == 'h1':
            # 绘制大标题
            draw.text((x, y), p_text, fill='black', font=fonts['h1'])
            y += 70
        elif p_type == 'h2':
            # 绘制二级标题
            draw.text((x, y), p_text, fill='black', font=fonts['h2'])
            y += 60
        elif p_type == 'h3':
            # 绘制三级标题
            draw.text((x, y), p_text, fill='black', font=fonts['h3'])
            y += 50
        elif p_type == 'spacing':
            # 添加额外的垂直空间
            y += p_text
        elif p_type == 'list_item':
            # 解析列表项
            match = re.match(r'^(\d+)\.(\s+)(.+)$', p_text)
            if match:
                number = match.group(1)
                space = match.group(2)
                content = match.group(3)
                
                # 绘制序号，带光晕效果使其更醒目
                number_text = f"{number}."
                draw.text((x+1, y+1), number_text, fill='#333333', font=fonts['list'])  # 阴影
                draw.text((x, y), number_text, fill='black', font=fonts['list'])  # 前景
                
                # 测量序号宽度
                number_width = draw.textlength(number_text, font=fonts['list'])
                
                # 解析内容中的颜色标签
                segments = parse_color_tags(content)
                
                # 绘制内容
                content_x = x + number_width + 10
                line_height = 40
                line_y = y
                line_x = content_x
                remained_width = max_width - (number_width + 10)
                
                for segment in segments:
                    words = segment.text.split()
                    for word in words:
                        word_width = draw.textlength(word, font=fonts['bold' if segment.style.is_bold else 'regular'])
                        
                        # 检查是否需要换行
                        if line_x + word_width > x + max_width:
                            line_y += line_height
                            line_x = content_x
                        
                        # 绘制单词
                        draw_text_with_color(draw, image, fonts, (line_x, line_y), word, 
                                           segment.style.color, 
                                           segment.style.is_bold,
                                           segment.style.is_italic)
                        
                        # 更新位置
                        line_x += word_width + 10  # 加上词间距
                
                # 更新y坐标，确保移至本段最后一行之后
                y = line_y + line_height
        elif p_type == 'unordered_list_item':
            # 绘制无序列表项 - 使用实心圆点
            bullet = "• "
            
            # 绘制带阴影的项目符号让其更醒目
            draw.text((x+1, y+1), bullet, fill='#333333', font=fonts['list'])  # 阴影
            draw.text((x, y), bullet, fill='black', font=fonts['list'])  # 前景
            
            # 测量项目符号宽度
            bullet_width = draw.textlength(bullet, font=fonts['list'])
            
            # 解析内容中的颜色标签
            segments = parse_color_tags(p_text)
            
            # 绘制内容
            content_x = x + bullet_width + 10
            line_height = 40
            line_y = y
            line_x = content_x
            remained_width = max_width - (bullet_width + 10)
            
            for segment in segments:
                words = segment.text.split()
                for word in words:
                    word_width = draw.textlength(word, font=fonts['bold' if segment.style.is_bold else 'regular'])
                    
                    # 检查是否需要换行
                    if line_x + word_width > x + max_width:
                        line_y += line_height
                        line_x = content_x
                    
                    # 绘制单词
                    draw_text_with_color(draw, image, fonts, (line_x, line_y), word, 
                                       segment.style.color, 
                                       segment.style.is_bold,
                                       segment.style.is_italic)
                    
                    # 更新位置
                    line_x += word_width + 10  # 加上词间距
            
            # 更新y坐标，确保移至本段最后一行之后
            y = line_y + line_height
        elif p_type == 'indented_paragraph':
            # 绘制缩进段落
            segments = parse_color_tags(p_text)
            indented_x = x + 40  # 缩进40像素
            
            line_height = 40
            line_y = y
            line_x = indented_x
            
            for segment in segments:
                words = segment.text.split()
                for word in words:
                    word_width = draw.textlength(word, font=fonts['bold' if segment.style.is_bold else 'regular'])
                    
                    # 检查是否需要换行
                    if line_x + word_width > x + max_width:
                        line_y += line_height
                        line_x = indented_x
                    
                    # 绘制单词
                    draw_text_with_color(draw, image, fonts, (line_x, line_y), word, 
                                       segment.style.color, 
                                       segment.style.is_bold,
                                       segment.style.is_italic)
                    
                    # 更新位置
                    line_x += word_width + 10  # 加上词间距
            
            # 更新y坐标，确保移至本段最后一行之后
            y = line_y + line_height + 5
        elif p_type == 'code_block':
            # 绘制代码块
            code_margin = 15
            code_x = x + code_margin
            code_y = y + code_margin
            code_width = max_width - 2 * code_margin
            
            # 提取语言和内容
            if isinstance(p_text, dict):
                language = p_text.get('language', '')
                code_lines = p_text.get('content', '').split('\n')
            else:
                language = ''
                code_lines = p_text.split('\n')
                
            # 绘制代码块背景
            code_height = len(code_lines) * 40 + 2 * code_margin
            code_bg_color = (240, 240, 240)
            draw.rectangle((x, y, x + max_width, y + code_height), fill=code_bg_color)
            
            # 绘制语言标签（如果有）
            if language:
                lang_bg_color = (220, 220, 220)
                lang_width = draw.textlength(language, font=fonts['regular']) + 20
                draw.rectangle((x, y, x + lang_width, y + 30), fill=lang_bg_color)
                draw.text((x + 10, y + 5), language, fill='#333333', font=fonts['regular'])
            
            # 绘制代码行
            for i, line in enumerate(code_lines):
                line_y = code_y + i * 40
                # 使用等宽字体绘制代码
                draw.text((code_x, line_y), line, fill='#333333', font=fonts['regular'])
            
            y += code_height + 15  # 更新y坐标
        elif p_type == 'table':
            # 更美观的表格渲染
            rows = p_text.split('\n')
            row_height = 40
            table_y = y
            table_x = x  # 确保table_x在这里定义
            
            # 找出表头和内容行
            header_row = None
            separator_row = None
            content_rows = []
            
            for i, row in enumerate(rows):
                if '---' in row or '===' in row:
                    separator_row = i
                    header_row = i - 1 if i > 0 else None
                    break
            
            # 如果找到了分隔符行，将其之前的行视为表头，之后的行视为内容
            if separator_row is not None:
                if header_row is not None:
                    header = rows[header_row]
                else:
                    header = None
                content_rows = [row for i, row in enumerate(rows) if i != separator_row and (header_row is None or i != header_row)]
            else:
                # 没有分隔符行，第一行视为表头，其余为内容
                if len(rows) > 0:
                    header = rows[0]
                    content_rows = rows[1:]
                else:
                    header = None
                    content_rows = rows
            
            # 计算列宽
            all_rows = [header] + content_rows if header else content_rows
            max_columns = max([row.count('|') + 1 for row in all_rows])
            column_widths = [0] * max_columns
            
            # 为每列计算最大宽度
            for row in all_rows:
                cells = row.split('|')
                for i, cell in enumerate(cells):
                    if i < max_columns:
                        cell_width = draw.textlength(cell.strip(), font=fonts['regular'])
                        column_widths[i] = max(column_widths[i], cell_width)
            
            # 添加表格外边框
            total_table_width = sum(column_widths) + 20 * max_columns
            total_table_height = (len(all_rows) + 1) * row_height  # 加1用于底部边框
            
            # 绘制表格边框
            draw.rectangle(
                (table_x, table_y, table_x + total_table_width, table_y + total_table_height),
                outline='#CCCCCC',
                width=1
            )
            
            # 绘制表头
            if header:
                # 表头背景
                header_cells = header.split('|')
                header_bg_color = (240, 240, 240)
                draw.rectangle(
                    (table_x, table_y, table_x + total_table_width, table_y + row_height),
                    fill=header_bg_color
                )
                
                # 绘制表头单元格
                cell_x = table_x + 10
                for i, cell in enumerate(header_cells):
                    if i < max_columns:
                        # 处理单元格内容的颜色标签
                        cell_content = cell.strip()
                        segments = parse_color_tags(cell_content)
                        
                        # 绘制单元格内容
                        for segment in segments:
                            segment_width = draw_text_with_color(
                                draw, image, fonts,
                                (cell_x, table_y + 10),
                                segment.text,
                                '#000000',  # 表头文字用黑色
                                True,  # 表头加粗
                                segment.style.is_italic
                            )
                            cell_x += segment_width + 5
                        
                        # 移动到下一个单元格
                        cell_x += 15
                
                # 绘制表头下的分隔线
                draw.line(
                    [(table_x, table_y + row_height), 
                     (table_x + total_table_width, table_y + row_height)],
                    fill='#888888',
                    width=2  # 稍微粗一点的分隔线
                )
                
                table_y += row_height
            
            # 绘制内容行
            row_colors = [(255, 255, 255), (248, 248, 248)]  # 交替行颜色
            
            for row_idx, row in enumerate(content_rows):
                row_cells = row.split('|')
                cell_x = table_x + 10
                
                # 交替行背景色
                row_bg_color = row_colors[row_idx % 2]
                draw.rectangle(
                    (table_x, table_y, table_x + total_table_width, table_y + row_height),
                    fill=row_bg_color
                )
                
                # 绘制单元格内容
                for i, cell in enumerate(row_cells):
                    if i < max_columns:
                        # 处理单元格内容的颜色标签
                        cell_content = cell.strip()
                        segments = parse_color_tags(cell_content)
                        
                        # 绘制单元格内容
                        for segment in segments:
                            segment_width = draw_text_with_color(
                                draw, image, fonts,
                                (cell_x, table_y + 10),
                                segment.text,
                                segment.style.color,
                                segment.style.is_bold,
                                segment.style.is_italic
                            )
                            cell_x += segment_width + 5
                        
                        # 绘制单元格右边框
                        if i < max_columns - 1:
                            draw.line(
                                [(cell_x + 10, table_y), (cell_x + 10, table_y + row_height)],
                                fill='#DDDDDD',
                                width=1
                            )
                        
                        # 移动到下一个单元格
                        cell_x += 15
                
                # 绘制行分隔线
                if row_idx < len(content_rows) - 1:
                    draw.line(
                        [(table_x, table_y + row_height), 
                         (table_x + total_table_width, table_y + row_height)],
                        fill='#DDDDDD',
                        width=1
                    )
                
                table_y += row_height
            
            y = table_y + 15  # 更新y坐标，增加底部间距
        else:
            # 普通段落
            segments = parse_color_tags(p_text)
            
            line_height = 40
            line_y = y
            line_x = x
            
            for segment in segments:
                words = segment.text.split()
                for word in words:
                    word_width = draw.textlength(word, font=fonts['bold' if segment.style.is_bold else 'regular'])
                    
                    # 检查是否需要换行
                    if line_x + word_width > x + max_width:
                        line_y += line_height
                        line_x = x
                    
                    # 绘制单词
                    draw_text_with_color(draw, image, fonts, (line_x, line_y), word, 
                                       segment.style.color, 
                                       segment.style.is_bold,
                                       segment.style.is_italic)
                    
                    # 更新位置
                    line_x += word_width + 10  # 加上词间距
            
            # 更新y坐标，确保移至本段最后一行之后
            y = line_y + line_height + 10  # 段落间距
    
    # 仅在文本未包含签名时添加签名
    if not contains_signature:
        signature = "—By 飞天"
        signature_font = fonts['regular']
        signature_width = draw.textlength(signature, font=signature_font)
        # 完全靠右对齐，零距离
        signature_x = card_x + card_width - signature_width - 5
        signature_y = card_y + card_height - 30
        
        # 绘制签名
        draw.text((signature_x, signature_y), signature, fill='black', font=signature_font)
    
    # 保存图像
    image.save(output_path)
    print(f"图片已保存到: {output_path}")
    return image

# 兼容接口
def generate_image(text, output_path, title_image=None):
    """兼容原有generate_image函数的接口"""
    return generate_simple_image_with_color(text, output_path, title_image)

def parse_color_tags(text):
    """解析HTML颜色标签和样式标签"""
    segments = []
    
    # 正则表达式匹配标签
    color_pattern = r'<span\s+style=["\']color:\s*([^;"\'\s]+)[\'"]>(.*?)</span>'
    bold_pattern = r'<span\s+style=["\']bold["\']>(.*?)</span>'
    italic_pattern = r'<span\s+style=["\']italic["\']>(.*?)</span>'
    
    # 如果没有标签，返回原文本
    if '<span style=' not in text:
        return [TextSegment(text, TextStyle(color='black'))]
    
    # 处理文本
    current_pos = 0
    while current_pos < len(text):
        # 查找颜色标签
        color_match = re.search(color_pattern, text[current_pos:])
        bold_match = re.search(bold_pattern, text[current_pos:])
        italic_match = re.search(italic_pattern, text[current_pos:])
        
        # 找出最早出现的标签
        earliest_match = None
        match_type = None
        
        if color_match:
            earliest_match = color_match
            match_type = 'color'
            match_start = current_pos + color_match.start()
        
        if bold_match and (earliest_match is None or current_pos + bold_match.start() < match_start):
            earliest_match = bold_match
            match_type = 'bold'
            match_start = current_pos + bold_match.start()
        
        if italic_match and (earliest_match is None or current_pos + italic_match.start() < match_start):
            earliest_match = italic_match
            match_type = 'italic'
            match_start = current_pos + italic_match.start()
        
        if earliest_match:
            # 处理标签前的文本
            if match_start > current_pos:
                segments.append(
                    TextSegment(
                        text[current_pos:match_start],
                        TextStyle(color='black')
                    )
                )
                )
            
            # 处理标签
            if match_type == 'color':
                color = earliest_match.group(1)
                content = earliest_match.group(2)
                segments.append(
                    TextSegment(
                        content,
                        TextStyle(color=color)
                    )
                )
            elif match_type == 'bold':
                content = earliest_match.group(1)
                segments.append(
                    TextSegment(
                        content,
                        TextStyle(is_bold=True)
                    )
                )
            elif match_type == 'italic':
                content = earliest_match.group(1)
                segments.append(
                    TextSegment(
                        content,
                        TextStyle(is_italic=True)
                    )
                )
            
            # 更新位置
            current_pos = match_start + len(earliest_match.group(0))
        else:
            # 处理剩余文本
            if current_pos < len(text):
                segments.append(
                    TextSegment(
                        text[current_pos:],
                        TextStyle(color='black')
                    )
                )
                )
            break
    
    return segments

def optimize_layout(paragraphs):
    """优化段落布局"""
    optimized = []
    
    for p_type, p_text in paragraphs:
        # 标题后增加更多空间
        if p_type in ['h1', 'h2', 'h3']:
            optimized.append((p_type, p_text))
            # 添加额外的空间
            optimized.append(('spacing', 10))
        # 列表项之间紧凑一些
        elif p_type in ['list_item', 'unordered_list_item']:
            optimized.append((p_type, p_text))
        # 段落间有适当间距
        else:
            optimized.append((p_type, p_text))
            # 普通段落后添加适当空间
            if p_type == 'paragraph':
                optimized.append(('spacing', 5))
    
    return optimized 