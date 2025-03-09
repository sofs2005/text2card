# utf-8
# image_generator.py
"""
Advanced image card generator with markdown and emoji support
"""
import math
import random
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import emoji
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import requests
from io import BytesIO
import time
from PIL import UnidentifiedImageError
import json
import html

# 导入配置
try:
    from config import config
except ImportError:
    # 如果无法导入配置，使用默认签名
    class DummyConfig:
        SIGNATURE_TEXT = "—飞天"
    config = DummyConfig()
@dataclass
class TextStyle:
    """文本样式定义"""
    font_name: str = 'regular'  # regular, bold, emoji
    font_size: int = 30  # 字体大小
    indent: int = 0  # 缩进像素
    line_spacing: int = 15  # 行间距
    is_title: bool = False  # 是否为标题
    is_category: bool = False  # 是否为分类标题
    keep_with_next: bool = False  # 是否与下一行保持在一起
    is_code: bool = False  # 是否为代码样式
    is_quote: bool = False  # 是否为引用样式
    alignment: str = 'left'  # 对齐方式
    is_dark_theme: bool = False  # 是否为深色主题
    is_list_item: bool = False  # 是否为列表项
    text_color: Optional[str] = None  # 文本颜色，可以是十六进制颜色代码
    is_bold: bool = False  # 是否为粗体
    is_italic: bool = False  # 是否为斜体
@dataclass
class TextSegment:
    """文本片段定义"""
    text: str  # 文本内容
    style: TextStyle  # 样式
    original_text: str = ''  # 原始文本（用于调试）
@dataclass
class ProcessedLine:
    """处理后的行信息"""
    text: str  # 实际文本内容
    style: TextStyle  # 样式信息
    height: int = 0  # 行高
    line_count: int = 1  # 实际占用行数
class FontManager:
    """字体管理器"""

    def __init__(self, font_paths: Dict[str, str]):
        self.fonts = {}
        self.font_paths = font_paths
        self._initialize_fonts()

    def _initialize_fonts(self):
        """初始化基础字体"""
        sizes = [30, 35, 40]  # 基础字号
        for size in sizes:
            self.fonts[f'regular_{size}'] = ImageFont.truetype(self.font_paths['regular'], size)
            self.fonts[f'bold_{size}'] = ImageFont.truetype(self.font_paths['bold'], size)
        # emoji字体
        self.fonts['emoji_30'] = ImageFont.truetype(self.font_paths['emoji'], 30)

    def get_font(self, style: TextStyle) -> ImageFont.FreeTypeFont:
        """获取对应样式的字体"""
        if style.font_name == 'emoji':
            return self.fonts['emoji_30']

        # 根据粗体和斜体属性选择合适的字体
        if style.is_bold or style.font_name == 'bold' or style.is_title or style.is_category:
            base_name = 'bold'
        else:
            base_name = 'regular'
        
        font_key = f'{base_name}_{style.font_size}'

        if font_key not in self.fonts:
            # 动态创建新字号的字体
            font_path = self.font_paths['bold'] if base_name == 'bold' else self.font_paths['regular']
            self.fonts[font_key] = ImageFont.truetype(font_path, style.font_size)

        return self.fonts[font_key]
def get_gradient_styles() -> List[Dict[str, tuple]]:
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
def get_theme_colors() -> Tuple[tuple, str, bool]:
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
def add_title_image(background: Image.Image, title_image_path: str, rect_x: int, rect_y: int, rect_width: int) -> int:
    """添加标题图片
    
    Args:
        background: 背景图片
        title_image_path: 图片路径或URL
        rect_x: 矩形x坐标
        rect_y: 矩形y坐标
        rect_width: 矩形宽度
        
    Returns:
        int: 图片底部位置加上间距
    """
    try:
        # 判断是否为URL
        if title_image_path.startswith(('http://', 'https://')):
            # 从URL下载图像，增加超时时间和重试次数
            title_img = download_image_with_timeout(title_image_path, timeout=15, max_retries=5)
            if title_img is None:
                print(f"无法加载标题图像: {title_image_path}")
                return rect_y + 30
        else:
            # 从本地文件加载
            try:
                title_img = Image.open(title_image_path)
            except (FileNotFoundError, IOError) as e:
                print(f"无法加载本地图像: {e}")
                return rect_y + 30
        
        # 如果图片不是RGBA模式，转换为RGBA
        if title_img.mode != 'RGBA':
            title_img = title_img.convert('RGBA')

        # 设置图片宽度等于文字区域宽度
        target_width = rect_width - 40  # 左右各留20像素边距

        # 计算等比例缩放后的高度
        aspect_ratio = title_img.height / title_img.width
        target_height = int(target_width * aspect_ratio)
        
        # 限制最大高度（不超过卡片宽度的一半）
        max_height = rect_width // 2
        if target_height > max_height:
            target_height = max_height
            target_width = int(max_height / aspect_ratio)

        # 调整图片大小
        resized_img = title_img.resize((int(target_width), target_height), Image.Resampling.LANCZOS)

        # 添加圆角
        rounded_img = round_corner_image(resized_img, radius=20)  # 可以调整圆角半径

        # 计算居中位置
        x = rect_x + (rect_width - target_width) // 2  # 水平居中
        y = rect_y + 20  # 顶部边距20像素

        # 粘贴图片（使用图片自身的alpha通道）
        background.paste(rounded_img, (x, y), rounded_img)

        return y + target_height + 20  # 返回图片底部位置加上20像素间距
    except Exception as e:
        print(f"Error loading title image: {e}")
        return rect_y + 30
class MarkdownParser:
    """Markdown解析器"""

    def __init__(self):
        self.reset()
        # 编译常用的正则表达式
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(.+?)\*|_(.+?)_')
        self.code_pattern = re.compile(r'`(.+?)`')
        self.link_pattern = re.compile(r'\[(.+?)\]\((.+?)\)')
        self.strikethrough_pattern = re.compile(r'~~(.+?)~~')
        # 添加匹配星号标记的正则表达式
        self.list_star_pattern = re.compile(r'^\* (.+)$')
        self.header_pattern = re.compile(r'^(\*+) (.+?)(\*+)$')
        # 添加HTML颜色标签的正则表达式
        self.html_color_pattern = re.compile(r'<span\s+style=["\']color:\s*([^;\'"]+);?["\'](?:.*?)>(.*?)</span>', re.IGNORECASE)
        # 引用组ID，用于跟踪连续的引用
        self.current_quote_group = 0
        
    def reset(self):
        self.segments = []
        self.current_section = None  # 当前处理的段落类型
        self.in_code_block = False   # 是否在代码块内
        self.in_quote_block = False  # 是否在引用块内
        self.quote_indent = 0        # 引用块缩进级别
        self.current_quote_group = 0  # 重置引用组ID

    def parse(self, text: str, add_signature: bool = True) -> List[TextSegment]:
        """解析整个文本"""
        self.reset()  # 重置解析器状态
        segments = []
        lines = text.split('\n')
        
        # 处理每一行
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 处理代码块标记 ```
            if line.strip() == '```':
                if not self.in_code_block:
                    # 开始一个代码块
                    self.in_code_block = True
                    i += 1
                    code_content = []
                    # 收集代码块的所有行，直到遇到结束标记
                    while i < len(lines) and not lines[i].strip() == '```':
                        code_content.append(lines[i])
                        i += 1
                    
                    # 创建代码块样式
                    style = TextStyle(
                        font_name='regular',  # 使用等宽字体
                        indent=40,  # 缩进
                        line_spacing=10,  # 紧凑的行间距
                        is_code=True  # 标记为代码样式
                    )
                    
                    # 使用单个TextSegment包含整个代码块
                    code_text = '\n'.join(code_content)
                    segments.append(TextSegment(text=code_text, style=style))
                    
                    # 如果找到了结束标记，跳过它
                    if i < len(lines) and lines[i].strip() == '```':
                        self.in_code_block = False
                        i += 1
                    continue
                else:
                    # 结束当前代码块
                    self.in_code_block = False
                    i += 1
                    continue
            
            # 处理引用块 >
            if line.strip().startswith('>'):
                # 提取引用级别和内容
                quote_parts = re.match(r'^(>+)\s*(.*)$', line.strip())
                if quote_parts:
                    quote_level = len(quote_parts.group(1))
                    quote_content = quote_parts.group(2)
                    
                    # 设置引用缩进级别
                    self.quote_indent = quote_level * 20
                    
                    # 空引用行处理 - 作为引用块内的空行而不是显示出来
                    if not quote_content.strip():
                        # 只添加一个带引用样式的空行，不显示 ">"
                        quote_style = TextStyle(
                            font_name='regular',
                            indent=40 + self.quote_indent,
                            line_spacing=8,  # 减小空行间距
                            is_quote=True
                        )
                        # 使用空文本，但保持引用块样式
                        segments.append(TextSegment(
                            text="",
                            style=quote_style,
                            original_text=""  # 使用空原始文本
                        ))
                    # 正常引用内容处理
                    else:
                        # 检查引用内容是否包含颜色标签
                        if self.html_color_pattern.search(quote_content.strip()):
                            # 准备收集所有颜色段落
                            text_parts = []
                            last_end = 0
                            
                            # 处理所有颜色标签
                            for match in self.html_color_pattern.finditer(quote_content.strip()):
                                # 处理标签前的文本
                                if match.start() > last_end:
                                    before_text = quote_content.strip()[last_end:match.start()]
                                    if before_text.strip():
                                        processed_text, format_styles = self.process_inline_formats(before_text)
                                        text_parts.append((processed_text, None, format_styles))
                                
                                # 处理颜色标签内的文本
                                color_value = match.group(1).strip()
                                content = match.group(2).strip()
                                processed_content, format_styles = self.process_inline_formats(content)
                                text_parts.append((processed_content, color_value, format_styles))
                                last_end = match.end()
                            
                            # 处理最后剩余的文本
                            if last_end < len(quote_content.strip()):
                                remaining_text = quote_content.strip()[last_end:]
                                if remaining_text.strip():
                                    processed_text, format_styles = self.process_inline_formats(remaining_text)
                                    text_parts.append((processed_text, None, format_styles))
                            
                            # 创建组合的段落
                            if text_parts:
                                # 如果只有一个部分无颜色
                                if len(text_parts) == 1 and text_parts[0][1] is None:
                                    text_part, _, format_styles = text_parts[0]
                                    style = TextStyle(
                                        font_name='bold' if format_styles['is_bold'] else 'regular',
                                        indent=40 + self.quote_indent,
                                        line_spacing=15,
                                        is_quote=True,
                                        is_bold=format_styles['is_bold'],
                                        is_italic=format_styles['is_italic']
                                    )
                                    segments.append(TextSegment(
                                        text=text_part,
                                        style=style,
                                        original_text=""
                                    ))
                                else:
                                    # 如果有多个部分，创建一个合并的段落
                                    # 创建一个包含所有内容的段落
                                    combined_text = ""
                                    for text_part, _, _ in text_parts:
                                        combined_text += text_part
                                    
                                    # 基本样式
                                    base_style = TextStyle(
                                        font_name='regular',
                                        indent=40 + self.quote_indent,
                                        line_spacing=15,
                                        is_quote=True
                                    )
                                    
                                    # 创建结果段落
                                    result_segment = TextSegment(
                                        text=combined_text,
                                        style=base_style,
                                        original_text=""
                                    )
                                    
                                    # 创建每个部分的TextSegment用于渲染
                                    original_segments = []
                                    for text_part, _, _ in text_parts:
                                        style = TextStyle(
                                            font_name='bold' if format_styles['is_bold'] else 'regular',
                                            indent=40 + self.quote_indent,
                                            line_spacing=15,
                                            is_quote=True,
                                            text_color=color_value,
                                            is_bold=format_styles['is_bold'],
                                            is_italic=format_styles['is_italic']
                                        )
                                        original_segments.append(TextSegment(
                                            text=text_part,
                                            style=style,
                                            original_text=""
                                        ))
                                    
                                    result_segment.original_segments = original_segments
                                    segments.append(result_segment)
                        else:
                            # 简单引用内容处理
                            processed_content, format_styles = self.process_inline_formats(quote_content.strip())
                            style = TextStyle(
                                font_name='bold' if format_styles['is_bold'] else 'regular',
                                indent=40 + self.quote_indent,
                                line_spacing=15,
                                is_quote=True,
                                is_bold=format_styles['is_bold'],
                                is_italic=format_styles['is_italic']
                            )
                            segments.append(TextSegment(
                                text=processed_content,
                                style=style,
                                original_text=""
                            ))
                i += 1
            else:
                # 处理其他行
                line_segments = self.parse_line(line)
                segments.extend(line_segments)
                i += 1
        
        # 添加签名
        if add_signature:
            try:
                signature_text = config.SIGNATURE_TEXT
                style = TextStyle(
                    alignment='right',
                )
                segments.append(TextSegment(text=signature_text, style=style))
            except:
                # 使用默认签名
                style = TextStyle(
                    alignment='right',
                )
                segments.append(TextSegment(text="—飞天", style=style))
        
        return segments

    def is_category_title(self, text: str) -> bool:
        """判断是否为分类标题"""
        return text.strip() in ['国内要闻', '国际动态']

    def process_inline_formats(self, text: str) -> Tuple[str, Dict[str, bool]]:
        """处理行内Markdown格式，返回处理后的文本和样式信息"""
        # 初始化样式信息
        styles = {
            'is_bold': False,
            'is_italic': False
        }
        
        # 处理标题格式 *一、标题*
        header_match = self.header_pattern.match(text)
        if header_match:
            return header_match.group(2), styles  # 只保留标题内容
            
        # 处理列表项标记 * 列表项
        list_match = self.list_star_pattern.match(text)
        if list_match:
            return "• " + list_match.group(1), styles  # 将星号替换为实际的圆点符号
        
        # HTML颜色标签不在这里处理，因为我们需要保留它们
        # 在parse_line方法中专门处理
        
        # 检查加粗 **text**
        if self.bold_pattern.search(text):
            styles['is_bold'] = True
            text = self.bold_pattern.sub(r'\1', text)
        
        # 检查斜体 *text* 或 _text_
        if self.italic_pattern.search(text):
            styles['is_italic'] = True
            text = self.italic_pattern.sub(lambda m: m.group(1) or m.group(2), text)
        
        # 处理链接 [text](url)
        text = self.link_pattern.sub(r'\1', text)
        
        # 处理行内代码 `code`
        text = self.code_pattern.sub(r'\1', text)
        
        # 处理删除线 ~~text~~
        text = self.strikethrough_pattern.sub(r'\1', text)
        
        return text, styles

    def process_title_marks(self, text: str) -> str:
        """处理标题标记"""
        # 应用所有行内格式处理
        processed_text, _ = self.process_inline_formats(text)
        return processed_text

    def split_number_and_content(self, text: str) -> Tuple[str, str]:
        """分离序号和内容"""
        match = re.match(r'(\d+)\.\s*(.+)', text)
        if match:
            return match.group(1), match.group(2)
        return '', text

    def split_title_and_content(self, text: str) -> Tuple[str, str]:
        """分离标题和内容"""
        parts = text.split('：', 1)
        if len(parts) == 2:
            return parts[0] + '：', parts[1].strip()
        return text, ''

    def parse_line(self, text: str) -> List[TextSegment]:
        """解析单行文本"""
        if not text.strip():
            return [TextSegment(text='', style=TextStyle())]
        
        # 如果是代码块内的文本，直接按原样处理，不进行任何HTML解析
        if self.in_code_block:
            style = TextStyle(
                font_name='regular',
                indent=40,
                line_spacing=10,
                is_code=True  # 标记为代码样式
            )
            return [TextSegment(text=text, style=style)]
        
        # 处理一级标题 - 确保去除#符号
        if text.strip().startswith('# '):
            title_text = text[2:].strip()
            # 现在处理标题内的emoji和格式（而不是直接调用process_inline_formats）
            # 这样可以保留emoji字符
            processed_text = title_text
            format_styles = {'is_bold': True, 'is_italic': False}
            
            style = TextStyle(
                font_name='bold',
                font_size=40,
                is_title=True,
                indent=0,
                is_bold=True
            )
            return [TextSegment(text=processed_text, style=style)]

        # 处理二级标题 - 确保去除##符号
        if text.strip().startswith('## '):
            processed_text, format_styles = self.process_inline_formats(text[3:].strip())
            style = TextStyle(
                font_name='bold',
                font_size=35,
                is_title=True,
                line_spacing=25,
                indent=0,
                is_bold=True
            )
            self.current_section = processed_text
            return [TextSegment(text=processed_text, style=style)]
        
        # 处理任务列表项 - [ ] 或 [x]
        task_match = re.match(r'^\s*[-*+]\s+\[([ xX])\]\s+(.+)$', text)
        if task_match:
            is_checked = task_match.group(1).lower() == 'x'
            list_content = task_match.group(2)
            # 计算缩进级别
            indent_level = len(text) - len(text.lstrip())
            indent_level = indent_level + 20  # 额外增加缩进来容纳复选框
            
            # 检查列表项是否包含HTML颜色标签
            if self.html_color_pattern.search(list_content):
                # 颜色处理代码...
                pass
            else:
                # 处理不含颜色标签的任务列表项
                processed_content, format_styles = self.process_inline_formats(list_content)
                prefix = "[x] " if is_checked else "[ ] "
                style = TextStyle(
                    font_name='bold' if format_styles['is_bold'] else 'regular',
                    indent=indent_level,
                    line_spacing=15,
                    is_list_item=True,
                    is_bold=format_styles['is_bold'],
                    is_italic=format_styles['is_italic']
                )
                return [TextSegment(text=prefix + processed_content, style=style, original_text=text)]
        
        # 处理无序列表项 - *, -, +
        list_match = re.match(r'^\s*[-*+]\s+(.+)$', text)
        if list_match:
            list_content = list_match.group(1)
            # 计算缩进级别
            indent_level = len(text) - len(text.lstrip())
            
            # 检查列表项是否包含HTML颜色标签
            if self.html_color_pattern.search(list_content):
                color_segments = []
                last_end = 0
                
                # 准备收集所有颜色段落
                text_parts = []
                
                # 处理所有颜色标签
                for match in self.html_color_pattern.finditer(list_content):
                    # 处理标签前的文本
                    if match.start() > last_end:
                        before_text = list_content[last_end:match.start()]
                        if before_text.strip():
                            processed_text, format_styles = self.process_inline_formats(before_text)
                            text_parts.append((processed_text, None, format_styles))
                    
                    # 处理颜色标签内的文本
                    color_value = match.group(1).strip()
                    content = match.group(2).strip()
                    processed_content, format_styles = self.process_inline_formats(content)
                    text_parts.append((processed_content, color_value, format_styles))
                    last_end = match.end()
                
                # 处理最后剩余的文本
                if last_end < len(list_content):
                    remaining_text = list_content[last_end:]
                    if remaining_text.strip():
                        processed_text, format_styles = self.process_inline_formats(remaining_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 如果有颜色部分，创建一个合并的段落
                if text_parts:
                    # 创建一个包含所有内容的段落
                    combined_text = "• "
                    for text_part, _, _ in text_parts:
                        combined_text += text_part
                    
                    # 基本样式
                    base_style = TextStyle(
                        font_name='regular',
                        indent=indent_level,
                        line_spacing=15,
                        is_list_item=True
                    )
                    
                    # 创建结果段落
                    result_segment = TextSegment(
                        text=combined_text,
                        style=base_style,
                        original_text=text
                    )
                    
                    # 使用一个特殊的标记，稍后在渲染过程中处理
                    # 将包含所有原始段落的列表附加到新段落
                    result_segment = TextSegment(text=result_text, style=result_style)
                    result_segment.original_segments = segments
                    
                    return [result_segment]
            
            return []

        # 检查是否匹配标题模式: *标题* 或 **标题**
        header_match = re.match(r'^\*+\s*(.+?)\s*\*+$', text)
        if header_match:
            title_text = header_match.group(1)
            # 根据星号数量或前缀确定标题级别
            if title_text.startswith("一、") or title_text.startswith("二、") or title_text.startswith("三、") or title_text.startswith("四、"):
                style = TextStyle(
                    font_name='bold',
                    font_size=38,  # 加大字号
                    is_title=True,
                    line_spacing=25,
                    indent=0,
                    is_bold=True
                )
            else:
                style = TextStyle(
                    font_name='bold',
                    font_size=35,
                    is_title=True,
                    line_spacing=20,
                    indent=0,
                    is_bold=True
                )
            return [TextSegment(text=title_text, style=style)]

        # 处理分类标题
        if self.is_category_title(text):
            style = TextStyle(
                font_name='bold',
                font_size=35,
                is_category=True,
                line_spacing=25,
                indent=0,
                is_bold=True
            )
            return [TextSegment(text=text.strip(), style=style)]

        # 处理emoji标题格式
        if text.strip() and emoji.is_emoji(text[0]):
            # 移除文本中的加粗标记 **
            content = text.strip()
            processed_content, format_styles = self.process_inline_formats(content)

            style = TextStyle(
                font_name='bold',
                font_size=40,  # 使用H1的字体大小
                is_title=True,
                line_spacing=25,
                indent=0,
                is_bold=True
            )
            return [TextSegment(text=processed_content, style=style)]

        # 处理带序号的新闻条目
        number, content = self.split_number_and_content(text)
        if number:
            # 检查列表内容是否包含HTML颜色标签
            if self.html_color_pattern.search(content):
                # 准备收集所有颜色段落
                text_parts = []
                last_end = 0
                
                # 处理所有颜色标签
                for match in self.html_color_pattern.finditer(content):
                    # 处理标签前的文本
                    if match.start() > last_end:
                        before_text = content[last_end:match.start()]
                        if before_text.strip():
                            processed_text, format_styles = self.process_inline_formats(before_text)
                            text_parts.append((processed_text, None, format_styles))
                    
                    # 处理颜色标签内的文本
                    color_value = match.group(1).strip()
                    content_text = match.group(2).strip()
                    processed_content, format_styles = self.process_inline_formats(content_text)
                    text_parts.append((processed_content, color_value, format_styles))
                    last_end = match.end()
                
                # 处理最后剩余的文本
                if last_end < len(content):
                    remaining_text = content[last_end:]
                    if remaining_text.strip():
                        processed_text, format_styles = self.process_inline_formats(remaining_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 如果有颜色部分，创建一个合并的段落
                if text_parts:
                    # 创建一个包含所有内容的段落
                    combined_text = f"{number}. "
                    for text_part, _, _ in text_parts:
                        combined_text += text_part
                    
                    # 基本样式
                    base_style = TextStyle(
                        font_name='regular',
                        indent=0,
                        line_spacing=15,
                        is_title=True
                    )
                    
                    # 创建结果段落
                    result_segment = TextSegment(
                        text=combined_text,
                        style=base_style,
                        original_text=text
                    )
                    
                    # 创建每个部分的TextSegment用于渲染
                    original_segments = []
                    
                    # 首先添加序号部分
                    number_style = TextStyle(
                        font_name='bold',
                        indent=0,
                        line_spacing=15,
                        is_title=True,
                        is_bold=True
                    )
                    original_segments.append(TextSegment(
                        text=f"{number}. ",
                        style=number_style,
                        original_text=""
                    ))
                    
                    # 然后添加各颜色部分
                    for text_part, color_value, format_styles in text_parts:
                        style = TextStyle(
                            font_name='bold' if format_styles['is_bold'] else 'regular',
                            indent=0,
                            line_spacing=15,
                            text_color=color_value,
                            is_title=True,
                            is_bold=format_styles['is_bold'],
                            is_italic=format_styles['is_italic']
                        )
                        original_segments.append(TextSegment(
                            text=text_part,
                            style=style,
                            original_text=""
                        ))
                    
                    result_segment.original_segments = original_segments
                    return [result_segment]
            else:
                # 处理不含颜色标签的情况
                content = self.process_title_marks(content)
                title, body = self.split_title_and_content(content)
                segments = []

                title_style = TextStyle(
                    font_name='bold',
                    indent=0,
                    is_title=True,
                    line_spacing=15 if body else 20,
                    is_bold=True
                )
                segments.append(TextSegment(
                    text=f"{number}. {title}",
                    style=title_style
                ))

                if body:
                    # 处理内容部分的格式
                    processed_body, format_styles = self.process_inline_formats(body)
                    content_style = TextStyle(
                        font_name='bold' if format_styles['is_bold'] else 'regular',
                        indent=40,
                        line_spacing=20,
                        is_bold=format_styles['is_bold'],
                        is_italic=format_styles['is_italic']
                    )
                    segments.append(TextSegment(
                        text=processed_body,
                        style=content_style
                    ))
                return segments

        # 处理破折号开头的内容
        if text.strip().startswith('-'):
            processed_text, format_styles = self.process_inline_formats(text.strip())
            style = TextStyle(
                font_name='bold' if format_styles['is_bold'] else 'regular',
                indent=40,
                line_spacing=15,
                is_bold=format_styles['is_bold'],
                is_italic=format_styles['is_italic']
            )
            return [TextSegment(text=processed_text, style=style)]

        # 处理普通文本，应用行内格式
        # 检查是否包含HTML颜色标签
        if self.html_color_pattern.search(text):
            # 处理带颜色标签的文本
            text_parts = []
            last_end = 0
            
            # 处理所有颜色标签
            for match in self.html_color_pattern.finditer(text):
                # 处理标签前的文本
                if match.start() > last_end:
                    before_text = text[last_end:match.start()]
                    if before_text.strip():
                        processed_text, format_styles = self.process_inline_formats(before_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 处理颜色标签内的文本
                color_value = match.group(1).strip()
                content = match.group(2).strip()
                processed_content, format_styles = self.process_inline_formats(content)
                text_parts.append((processed_content, color_value, format_styles))
                last_end = match.end()
            
            # 处理最后剩余的文本
            if last_end < len(text):
                remaining_text = text[last_end:]
                if remaining_text.strip():
                    processed_text, format_styles = self.process_inline_formats(remaining_text)
                    text_parts.append((processed_text, None, format_styles))
            
            # 如果有颜色部分，创建一个合并的段落
            if text_parts:
                # 创建一个包含所有内容的段落
                combined_text = ""
                for text_part, _, _ in text_parts:
                    combined_text += text_part
                
                # 基本样式
                base_style = TextStyle(
                    font_name='regular',
                    indent=40 if self.current_section else 0,
                    line_spacing=15
                )
                
                # 创建结果段落
                result_segment = TextSegment(
                    text=combined_text,
                    style=base_style,
                    original_text=text
                )
                
                # 创建每个部分的TextSegment用于渲染
                original_segments = []
                for text_part, color_value, format_styles in text_parts:
                    style = TextStyle(
                        font_name='bold' if format_styles['is_bold'] else 'regular',
                        indent=40 if self.current_section else 0,
                        line_spacing=15,
                        text_color=color_value,
                        is_bold=format_styles['is_bold'],
                        is_italic=format_styles['is_italic']
                    )
                    original_segments.append(TextSegment(
                        text=text_part,
                        style=style,
                        original_text=""
                    ))
                
                result_segment.original_segments = original_segments
                return [result_segment]
        else:
            # 处理普通文本，应用行内格式
            processed_text, format_styles = self.process_inline_formats(text.strip())
            style = TextStyle(
                font_name='bold' if format_styles['is_bold'] else 'regular',
                indent=40 if self.current_section else 0,
                line_spacing=15,
                is_bold=format_styles['is_bold'],
                is_italic=format_styles['is_italic']
            )
            return [TextSegment(text=processed_text, style=style)]
class TextRenderer:
    """文本渲染器"""

    def __init__(self, font_manager: FontManager, max_width: int):
        self.font_manager = font_manager
        self.max_width = max_width
        self.temp_image = Image.new('RGBA', (2000, 100))
        self.temp_draw = ImageDraw.Draw(self.temp_image)

    def measure_text(self, text: str, font: ImageFont.FreeTypeFont,
                     emoji_font: Optional[ImageFont.FreeTypeFont] = None) -> Tuple[int, int]:
        """测量文本尺寸，考虑emoji"""
        total_width = 0
        max_height = 0

        for char in text:
            if emoji.is_emoji(char) and emoji_font:
                bbox = self.temp_draw.textbbox((0, 0), char, font=emoji_font)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
            else:
                bbox = self.temp_draw.textbbox((0, 0), char, font=font)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

            total_width += width
            max_height = max(max_height, height)

        return total_width, max_height

    def draw_text_with_emoji(self, draw: ImageDraw.ImageDraw, pos: Tuple[int, int], text: str,
                             font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont,
                             fill: str = "white", style: TextStyle = None) -> int:
        """绘制包含emoji的文本，返回绘制宽度"""
        x, y = pos
        total_width = 0
        
        # 检查是否是带有original_segments的合并段落
        if style and hasattr(style, '_source_segment') and hasattr(style._source_segment, 'original_segments'):
            # 使用原始段落进行绘制
            current_x = x
            # 使用集合跟踪已渲染的段落ID
            rendered_ids = set()
            
            # 确保original_segments不为None
            original_segments = style._source_segment.original_segments
            if original_segments is None:
                original_segments = []
                
            for segment in original_segments:
                if segment is None or not hasattr(segment, "style") or segment.style is None:
                    continue
                    
                # 创建唯一标识符避免重复渲染
                segment_id = id(segment)
                if segment_id in rendered_ids:
                    continue
                
                # 记录ID
                rendered_ids.add(segment_id)
                
                try:
                    segment_font = self.font_manager.get_font(segment.style)
                    segment_style = segment.style
                    segment_text = segment.text if hasattr(segment, "text") else ""
                    segment_color = fill
                    if segment_style and hasattr(segment_style, "text_color") and segment_style.text_color:
                        segment_color = segment_style.text_color
                    
                    # 直接渲染文本，而不是递归调用
                    for char in segment_text:
                        if emoji.is_emoji(char):
                            # 使用emoji字体
                            bbox = draw.textbbox((current_x, y), char, font=emoji_font)
                            draw.text((current_x, y), char, font=emoji_font, embedded_color=True)
                            char_width = bbox[2] - bbox[0]
                        else:
                            # 使用常规字体
                            bbox = draw.textbbox((current_x, y), char, font=segment_font)
                            # 如果是斜体，稍微移动绘制位置
                            if segment_style and hasattr(segment_style, "is_italic") and segment_style.is_italic:
                                char_height = bbox[3] - bbox[1]
                                slant_offset = char_height * 0.2
                                draw.text((current_x + slant_offset/2, y), char, font=segment_font, fill=segment_color)
                            else:
                                draw.text((current_x, y), char, font=segment_font, fill=segment_color)
                            char_width = bbox[2] - bbox[0]
                        
                        current_x += char_width
                        total_width += char_width
                except Exception as e:
                    print(f"Error rendering segment: {e}")
                    continue
            
            return total_width
        
        # 使用样式中的颜色（如果有）
        text_color = fill
        if style and style.text_color:
            text_color = style.text_color

        # 处理斜体（通过变换实现）
        is_italic = style and style.is_italic
        
        # 为代码块和引用块添加背景
        if style and (style.is_code or style.is_quote):
            # 先测量整行文本宽度
            text_width, text_height = self.measure_text(text, font, emoji_font)
            
            # 对于空文本的引用行，确保有最小高度以保持连续性
            if style.is_quote and not text.strip():
                text_height = max(text_height, 20)  # 设置最小高度
            
            # 绘制背景
            if style.is_code:
                # 代码块使用浅灰色背景
                code_bg_color = (50, 50, 50, 60) if style.is_dark_theme else (230, 230, 230, 100)
                draw.rounded_rectangle(
                    [(x-10, y-5), (x + text_width + 10, y + text_height + 5)], 
                    radius=5, 
                    fill=code_bg_color
                )
            elif style.is_quote:
                # 引用块左侧添加竖线
                quote_color = (100, 180, 255, 200)  # 浅蓝色
                # 对于空文本，确保至少有最小高度的竖线
                min_height = max(text_height + 10, 20)
                draw.rectangle(
                    [(x-15, y-5), (x-10, y + min_height)],
                    fill=quote_color
                )
                # 引用块背景
                quote_bg_color = (70, 70, 70, 40) if style.is_dark_theme else (240, 240, 255, 70)
                draw.rounded_rectangle(
                    [(x-10, y-5), (x + max(text_width, 30) + 10, y + min_height)], 
                    radius=5, 
                    fill=quote_bg_color
                )

        # 代码块文本的特殊处理
        if style and style.is_code:
            # 代码块中的特殊字符处理
            # 对于代码块，我们需要确保所有字符按原样显示
            
            # 按原样渲染文本
            current_x = x
            for char in text:
                if char == '\n':
                    # 如果是换行符，不进行渲染，因为TextRenderer.split_text_to_lines已经处理了换行
                    continue
                if emoji.is_emoji(char):
                    bbox = draw.textbbox((current_x, y), char, font=emoji_font)
                    draw.text((current_x, y), char, font=emoji_font, embedded_color=True)
                    current_x += bbox[2] - bbox[0]
                else:
                    bbox = draw.textbbox((current_x, y), char, font=font)
                    draw.text((current_x, y), char, font=font, fill=text_color)
                    current_x += bbox[2] - bbox[0]
            return current_x - x

        # 改进列表项渲染
        if style and style.is_list_item and text.startswith(('•', '-', '+')):
            # 提取列表标记和内容
            parts = text.split(' ', 1)
            marker = parts[0]
            content = parts[1] if len(parts) > 1 else ""
            
            # 绘制列表标记
            # 使用加粗字体绘制列表标记
            marker_font = self.font_manager.get_font(TextStyle(font_name='bold', font_size=style.font_size))
            bbox = draw.textbbox((x, y), marker, font=marker_font)
            draw.text((x, y), marker, font=marker_font, fill=text_color)
            marker_width = bbox[2] - bbox[0]
            
            # 绘制内容，缩进10像素
            for char in content:
                if emoji.is_emoji(char):
                    # 使用emoji字体
                    bbox = draw.textbbox((x + marker_width + 10, y), char, font=emoji_font)
                    draw.text((x + marker_width + 10, y), char, font=emoji_font, fill=text_color, embedded_color=True)
                    char_width = bbox[2] - bbox[0]
                else:
                    # 使用常规字体
                    bbox = draw.textbbox((x + marker_width + 10, y), char, font=font)
                    # 如果是斜体，稍微移动绘制位置以模拟斜体效果
                    if is_italic:
                        # 移动的距离取决于字符高度
                        char_height = bbox[3] - bbox[1]
                        slant_offset = char_height * 0.2  # 斜体倾斜程度
                        draw.text((x + marker_width + 10 + slant_offset/2, y), char, font=font, fill=text_color)
                    else:
                        draw.text((x + marker_width + 10, y), char, font=font, fill=text_color)
                    char_width = bbox[2] - bbox[0]
                
                x += char_width
                total_width += char_width
                
            # 添加列表标记和缩进的宽度
            total_width += marker_width + 10
            return total_width
        
        # 常规文本绘制
        for char in text:
            if emoji.is_emoji(char):
                # 使用emoji字体
                bbox = draw.textbbox((x, y), char, font=emoji_font)
                draw.text((x, y), char, font=emoji_font, fill=text_color, embedded_color=True)
                char_width = bbox[2] - bbox[0]
            else:
                # 使用常规字体
                bbox = draw.textbbox((x, y), char, font=font)
                # 如果是斜体，稍微移动绘制位置以模拟斜体效果
                if is_italic:
                    # 移动的距离取决于字符高度
                    char_height = bbox[3] - bbox[1]
                    slant_offset = char_height * 0.2  # 斜体倾斜程度
                    draw.text((x + slant_offset/2, y), char, font=font, fill=text_color)
                else:
                    draw.text((x, y), char, font=font, fill=text_color)
                char_width = bbox[2] - bbox[0]

            x += char_width
            total_width += char_width

        return total_width

    def calculate_height(self, processed_lines: List[ProcessedLine]) -> int:
        """计算总高度，确保不在最后添加额外间距"""
        total_height = 0
        prev_line = None

        for i, line in enumerate(processed_lines):
            if not line.text.strip():
                # 只有当不是最后一行，且后面还有内容时才添加间距
                if i < len(processed_lines) - 1 and any(l.text.strip() for l in processed_lines[i + 1:]):
                    if prev_line:
                        total_height += prev_line.style.line_spacing
                continue

            # 计算当前行高度
            line_height = line.height * line.line_count
            
            # 代码块需要额外间距
            if hasattr(line.style, 'is_code') and line.style.is_code:
                line_height += 20  # 代码块上下各加10px的内边距
            
            # 引用块需要额外间距
            if hasattr(line.style, 'is_quote') and line.style.is_quote:
                line_height += 10  # 引用块上下各加5px的内边距

            # 签名的高度
            if i == len(processed_lines) - 1:
                line_height += 40

            # 添加行间距，但不在最后一行后添加
            if prev_line and i < len(processed_lines) - 1:
                if prev_line.style.is_category:
                    total_height += 30
                elif prev_line.style.is_title and not line.style.is_title:
                    total_height += 20
                else:
                    total_height += line.style.line_spacing

            total_height += line_height
            prev_line = line

        return total_height

    def split_text_to_lines(self, segment: TextSegment, available_width: int) -> List[ProcessedLine]: -> List[ProcessedLine]:
        """将文本分割成合适宽度的行，支持emoji"""
        processed_lines = []
        
        # 处理换行符
        if segment.text == "\n":
            # 直接返回一个空行，强制换行
            processed_lines.append(ProcessedLine(
                text='',
                style=segment.style,
                height=20,  # 设置一个固定的行高
                line_count=1
            ))
            return processed_lines
        
        # 处理带有original_segments的合并段落
        if hasattr(segment, 'original_segments'):
            # 获取基础字体用于测量
            font = self.font_manager.get_font(segment.style)
            # 如果文本很短，不需要换行，直接返回
            if len(segment.text) < 30:  # 短文本不拆分
                _, height = self.measure_text(segment.text, font, emoji_font)
                processed_line = ProcessedLine(
                    text=segment.text,
                    style=segment.style,
                    height=height,
                    line_count=1
                )
                processed_line.style._source_segment = segment
                processed_lines.append(processed_line)
                return processed_lines

            emoji_font = self.font_manager.fonts.get('emoji_30')
            
            # 如果文本很短，不需要换行，直接返回
            if len(segment.text) < 30:  # 短文本不拆分
                _, height = self.measure_text(segment.text, font, emoji_font)
                processed_line = ProcessedLine(
                    text=segment.text,
                    style=segment.style,
                    height=height,
                    line_count=1
                )
                processed_line.style._source_segment = segment
                processed_lines.append(processed_line)
                return processed_lines
            
            # 测量原始段落总宽度
            total_width = 0
            for seg in segment.original_segments:
                if seg is None or seg.style is None:
                    continue
                width, _ = self.measure_text(seg.text, self.font_manager.get_font(seg.style), emoji_font)
                total_width += width
            
            # 如果宽度超过可用宽度，需要创建多行
            if total_width > available_width:
                # 使用更简单的分词策略，尽量保持颜色标签内的文本完整
                # 首先尝试把彩色文本作为一个整体，只在非彩色部分尝试换行
                current_line = []
                current_width = 0
                max_height = 0
                colored_segments = []  # 存储彩色段落
                non_colored_segments = []  # 存储非彩色段落
                
                # 区分彩色和非彩色段落
                for seg in segment.original_segments:
                    if seg is None or seg.style is None:
                        continue
                    if seg.style.text_color:
                        colored_segments.append(seg)
                    else:
                        # 对非彩色段落进行分词
                        if seg.text:
                            words = []
                            current_word = ''
                            for char in seg.text:
                                if emoji.is_emoji(char):
                                    if current_word:
                                        words.append(current_word)
                                        current_word = ''
                                    words.append(char)
                                elif char in [' ', '，', '。', '：', '、', '！', '？', '；']:
                                    if current_word:
                                        words.append(current_word)
                                    words.append(char)
                                    current_word = ''
                                else:
                                    if ord(char) > 0x4e00:  # 中文字符
                                        if current_word:
                                            words.append(current_word)
                                            current_word = ''
                                        words.append(char)
                                    else:
                                        current_word += char
                            
                            if current_word:
                                words.append(current_word)
                            
                            # 为每个词创建段落
                            for word in words:
                                word_seg = TextSegment(
                                    text=word,
                                    style=seg.style,
                                    original_text=''
                                )
                                non_colored_segments.append(word_seg)
                
                # 合并所有段落，保持彩色段落完整
                all_segments = []
                for seg in segment.original_segments:
                    if seg is None or seg.style is None:
                        continue
                    if seg.style.text_color:
                        all_segments.append(seg)
                    else:
                        # 找到对应的分词段落
                        found = False
                        for word_seg in non_colored_segments:
                            if word_seg.style == seg.style and word_seg.text in seg.text:
                                if not found:
                                    found = True
                                all_segments.append(word_seg)
                        
                        # 如果没找到，添加原始段落
                        if not found and seg.text.strip():
                            all_segments.append(seg)
                
                # 现在进行换行
                for seg in all_segments:
                    if seg is None or seg.style is None:
                        continue
                    
                    seg_font = self.font_manager.get_font(seg.style)
                    seg_width, seg_height = self.measure_text(seg.text, seg_font, emoji_font)
                    
                    # 如果这个段落会导致当前行超过可用宽度
                    if current_width + seg_width > available_width:
                        # 如果是彩色段落，尝试单独放一行
                        if seg.style.text_color and current_line:
                            # 先创建当前行
                            combined_text = "".join([s.text for s in current_line if s is not None])
                            if combined_text.strip():  # 确保不是空行
                                line = ProcessedLine(
                                    text=combined_text,
                                    style=segment.style,
                                    height=max_height,
                                    line_count=1
                                )
                                line.style._source_segment = TextSegment(
                                    text=combined_text,
                                    style=segment.style
                                )
                                line.style._source_segment.original_segments = [s for s in current_line if s is not None]
                                processed_lines.append(line)
                            
                            # 重置行
                            current_line = []
                            current_width = 0
                            max_height = 0
                            
                            # 检查彩色段落自身是否需要换行
                            if seg_width > available_width:
                                # 需要对彩色段落进行分词
                                words = []
                                remaining_text = seg.text
                                current_line_width = 0
                                
                                for char in remaining_text:
                                    char_width, char_height = self.measure_text(char, seg_font, emoji_font)
                                    
                                    if current_line_width + char_width <= available_width:
                                        words.append(char)
                                        current_line_width += char_width
                                    else:
                                        # 创建一行
                                        word_text = "".join(words)
                                        if word_text.strip():
                                            colored_line = ProcessedLine(
                                                text=word_text,
                                                style=segment.style,
                                                height=seg_height,
                                                line_count=1
                                            )
                                            colored_line.style._source_segment = TextSegment(
                                                text=word_text,
                                                style=segment.style
                                            )
                                            colored_line.style._source_segment.original_segments = [TextSegment(
                                                text=word_text,
                                                style=seg.style
                                            )]
                                            processed_lines.append(colored_line)
                                        
                                        # 重置
                                        words = [char]
                                        current_line_width = char_width
                                
                                # 添加最后一行
                                if words:
                                    word_text = "".join(words)
                                    if word_text.strip():
                                        colored_line = ProcessedLine(
                                            text=word_text,
                                            style=segment.style,
                                            height=seg_height,
                                            line_count=1
                                        )
                                        colored_line.style._source_segment = TextSegment(
                                            text=word_text,
                                            style=segment.style
                                        )
                        bbox = draw.textbbox((0, 0), char, font=font)
                    text_width += bbox[2] - bbox[0]
                # 从右边计算起始x位置
                x = rect_x + rect_width - 40 - text_width
            else:
                # 默认左对齐
                x = base_x + line.style.indent
            
            # 设置字体和特殊样式
            font = font_manager.get_font(line.style)
            emoji_font = font_manager.fonts['emoji_30']
            
            # 确保样式中包含theme信息
            line.style.is_dark_theme = is_dark_theme
            
            # 为所有类型的文本使用draw_text_with_emoji方法，确保emoji能正确显示
            renderer.draw_text_with_emoji(
                draw, (x, current_y), line.text, 
                font, emoji_font, text_color, line.style
            )

            if i < len(processed_lines) - 1:
                current_y += line.height + line.style.line_spacing
            else:
                current_y += line.height

        

def 
def download_image_with_timeout(url: str, timeout: int = 10, max_retries: int = 3) -> Optional[Image.Image]:
    """
    从URL下载图像，支持超时和重试
    
    Args:
        url: 图像URL
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        
    Returns:
        PIL.Image对象或None（如果下载失败）
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 200:
                try:
                    return Image.open(BytesIO(response.content))
                except UnidentifiedImageError:
                    print(f"URL内容不是有效的图像: {url}")
                    return None
            else:
                print(f"下载图像失败，状态码: {response.status_code}, URL: {url}")
            retry_count += 1
            time.sleep(1)  # 等待1秒后重试
        except (requests.RequestException, IOError) as e:
            print(f"下载图像出错: {e}, URL: {url}")
            retry_count += 1
            time.sleep(1)  # 等待1秒后重试
    
    print(f"达到最大重试次数，无法下载图像: {url}")
    return None

def generate_image(text: str, output_path: str, title_image: Optional[str] = None)::
    """生成图片主函数"""
    try:
        # 创建解析器和渲染器
        parser = MarkdownParser()
        
        # 解析文本
        segments = parser.parse(text)
        
        # 设置字体路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = {
            'regular': os.path.join(current_dir, "msyh.ttc"),
            'bold': os.path.join(current_dir, "msyhbd.ttc"),
            'emoji': os.path.join(current_dir, "TwitterColorEmoji.ttf")
        }
        
        # 创建字体管理器
        font_manager = FontManager(font_paths)
        
        # 设置图片宽度
        width = 720
        
        # 创建渲染器
        renderer = TextRenderer(font_manager, width - 80)  # 留出左右边距
        
        # 处理文本段落，分割成行
        processed_lines = []
        for segment in segments:
            lines = renderer.split_text_to_lines(segment, width - 80)
            processed_lines.extend(lines)
        
        # 计算总高度
        total_height = renderer.calculate_height(processed_lines)
        
        # 创建背景图片
        background = create_gradient_background(width, total_height + 120)  # 添加上下边距
        
        # 如果有标题图片，添加到顶部
        rect_y = 40  # 初始Y坐标
        if title_image:
            try:
                # 添加标题图片，并获取新的Y坐标
                rect_y = add_title_image(background, title_image, 40, rect_y, width - 80)
            except Exception as e:
                print(f"添加标题图片失败: {e}")
        
        # 创建绘图对象
        draw = ImageDraw.Draw(background)
        
        # 获取主题颜色
        bg_color, text_color, is_dark_theme = get_theme_colors()
        
        # 绘制文本
        current_y = rect_y + 20  # 文本起始Y坐标
        
        for i, line in enumerate(processed_lines):
            # 设置对齐方式
            if line.style.alignment == 'center':
                # 居中对齐
                text_width = 0
                font = font_manager.get_font(line.style)
                emoji_font = font_manager.fonts['emoji_30']
                
                # 计算文本宽度
                for char in line.text:
                    if emoji.is_emoji(char):
                        bbox = draw.textbbox((0, 0), char, font=emoji_font)
                    else:
                        bbox = draw.textbbox((0, 0), char, font=font)
                    text_width += bbox[2] - bbox[0]
                
                # 计算起始x位置
                x = (width - text_width) // 2
            elif line.style.alignment == 'right':
                # 右对齐
                rect_x = 40  # 左边距
                rect_width = width - 80  # 可用宽度
                
                text_width = 0
                font = font_manager.get_font(line.style)
                emoji_font = font_manager.fonts['emoji_30']
                
                # 计算文本宽度
                for char in line.text:
                    if emoji.is_emoji(char):
                        bbox = draw.textbbox((0, 0), char, font=emoji_font)
                    else:
                        bbox = draw.textbbox((0, 0), char, font=font)
                    text_width += bbox[2] - bbox[0]
                # 从右边计算起始x位置
                x = rect_x + rect_width - 40 - text_width
            else:
                # 默认左对齐
                x = 40 + line.style.indent
            
            # 设置字体和特殊样式
            font = font_manager.get_font(line.style)
            emoji_font = font_manager.fonts['emoji_30']
            
            # 确保样式中包含theme信息
            line.style.is_dark_theme = is_dark_theme
            
            # 为所有类型的文本使用draw_text_with_emoji方法，确保emoji能正确显示
            renderer.draw_text_with_emoji(
                draw, (x, current_y), line.text, 
                font, emoji_font, text_color, line.style
            )

            if i < len(processed_lines) - 1:
                current_y += line.height + line.style.line_spacing
            else:
                current_y += line.height

        # 直接保存为PNG，保持RGBA模式
        background = background.convert('RGB')
        background.save(output_path, "PNG", optimize=False, compress_level=0)
        
        return output_path
        
    except Exception as e:
        print(f"Error generating image: {e}")
        raise
