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
        """初始化Markdown解析器"""
        self.reset()
        
        # 编译常用的正则表达式
        self.bold_pattern = re.compile(r'\*\*(.*?)\*\*')
        self.italic_pattern = re.compile(r'\*((?!\*).+?)\*|_(.+?)_')
        self.code_pattern = re.compile(r'`(.*?)`')
        self.link_pattern = re.compile(r'\[(.*?)\]\((.+?)\)')
        self.strikethrough_pattern = re.compile(r'~~(.*?)~~')
        # 添加匹配星号标记的正则表达式
        self.list_star_pattern = re.compile(r'^\* (.+)$')
        self.header_pattern = re.compile(r'^(\*+) (.+?)(\*+)$')
        
        # 添加HTML颜色标签的正则表达式 - 更精确的版本
        self.html_color_pattern = re.compile(
            r'<span\s+style=["\']color:\s*([^;"\']+)[;"\'](.*?)>(.*?)</span>', 
            re.DOTALL | re.IGNORECASE
        )
        
        # 引用组ID，用于跟踪连续的引用
        self.current_quote_group = 0

    def reset(self):
        self.segments = []
        self.current_section = None  # 当前处理的段落类型
        self.in_code_block = False   # 是否在代码块内
        self.in_quote_block = False  # 是否在引用块内
        self.quote_indent = 0        # 引用块缩进级别
        self.current_quote_group = 0  # 重置引用组ID

    def parse(self, text: str) -> List[TextSegment]:
        """解析整个文本"""
        self.reset()
        segments = []
        lines = text.splitlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 处理代码块
            if line.startswith('```'):
                if not self.in_code_block:
                    # 开始代码块
                    self.in_code_block = True
                    code_lang = line[3:].strip()
                    code_content = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith('```'):
                        # 完全保留原始代码，不做任何处理
                        code_content.append(lines[i])
                        i += 1
                    
                    if i < len(lines):  # 找到了结束标记
                        # 使用原始格式连接代码块内容
                        code_text = '\n'.join(code_content)
                        
                        # 确保代码块中的HTML标签正确显示
                        code_text = code_text.replace('<', '&lt;').replace('>', '&gt;')
                        
                        style = TextStyle(
                            font_name='regular',
                            indent=40,
                            line_spacing=10,
                            is_code=True  # 标记为代码样式
                        )
                        segments.append(TextSegment(
                            text=code_text,
                            style=style,
                            original_text=f"```{code_lang}\n{code_text}\n```"
                        ))
                        self.in_code_block = False
                    else:
                        # 没找到结束标记，但仍处理为代码块
                        code_text = '\n'.join(code_content)
                        
                        # 确保代码块中的HTML标签正确显示
                        code_text = code_text.replace('<', '&lt;').replace('>', '&gt;')
                        
                        style = TextStyle(
                            font_name='regular',
                            indent=40,
                            line_spacing=10,
                            is_code=True
                        )
                        segments.append(TextSegment(
                            text=code_text,
                            style=style,
                            original_text=f"```{code_lang}\n{code_text}"
                        ))
                        # 保持in_code_block为True，因为没有找到结束标记
                else:
                    # 结束代码块
                    self.in_code_block = False
                i += 1
                continue
                
            # 检查是否在引用块内或开始一个新的引用块
            if line.startswith('> ') or (line == '>' and not self.in_code_block):
                # 标记进入引用块状态
                self.in_quote_block = True
                
                # 处理引用内容
                quote_level = 0
                quote_content = line
                while quote_content.startswith('> '):
                    quote_level += 1
                    quote_content = quote_content[2:]
                
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
                            content = match.group(3).strip()
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
                                # 创建合并文本
                                combined_text = ""
                                for text_part, _, _ in text_parts:
                                    combined_text += text_part
                                
                                # 基础样式
                                base_style = TextStyle(
                                    font_name='regular',
                                    indent=40 + self.quote_indent,
                                    line_spacing=15,
                                    is_quote=True
                                )
                                
                                # 创建最终段落
                                result_segment = TextSegment(
                                    text=combined_text,
                                    style=base_style,
                                    original_text=""
                                )
                                
                                # 保存原始段落信息
                                original_segments = []
                                for text_part, color_value, format_styles in text_parts:
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
            # 非引用块处理
            else:
                # 退出引用块状态
                self.in_quote_block = False
                self.quote_indent = 0
                
                # 空行处理
                if not line:
                    # 只有当下一行有内容时才添加空行
                    next_has_content = False
                    for next_line in lines[i + 1:]:
                        if next_line.strip():
                            next_has_content = True
                            break
                    if next_has_content:
                        style = TextStyle(
                            line_spacing=20 if segments and segments[-1].style.is_title else 15
                        )
                        segments.append(TextSegment(text='', style=style))
                else:
                    # 处理常规行
                    line_segments = self.parse_line(line)
                    segments.extend(line_segments)
                    
                    # 只在确定有下一行内容时添加空行
                    # 但是避免在列表项之间添加空行
                    if i < len(lines) - 1:
                        has_next_content = False
                        for next_line in lines[i + 1:]:
                            if next_line.strip():
                                has_next_content = True
                                break
                        
                        # 检查当前行是否是列表项
                        current_is_list_item = False
                        if line_segments and hasattr(line_segments[-1].style, 'is_list_item'):
                            current_is_list_item = line_segments[-1].style.is_list_item
                        
                        # 检查下一行是否是列表项
                        next_is_list_item = False
                        if i + 1 < len(lines) and lines[i + 1].strip().startswith(('*', '-', '+', '1.', '2.', '3.')):
                            next_is_list_item = True
                        
                        # 如果当前行是列表项，并且下一行也是列表项，则不添加空行
                        if has_next_content and not (current_is_list_item and next_is_list_item):
                            style = line_segments[-1].style if line_segments else TextStyle()
                            segments.append(TextSegment(text='', style=TextStyle(line_spacing=style.line_spacing)))
            
            i += 1
            
        # 添加签名
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
            segments.append(TextSegment(text="—By 飞天", style=style))
            
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
        
        # 处理带序号的列表项
        number_match = re.match(r'^(\d+)\.\s+(.+)$', text)
        if number_match:
            number = number_match.group(1)
            content = number_match.group(2)
            
            # 检查是否包含HTML颜色标签
            if self.html_color_pattern.search(content):
                # 准备收集所有颜色段落
                text_parts = []
                last_end = 0
                
                # 处理所有颜色标签
                for match in self.html_color_pattern.finditer(content):
                    # 添加标签前的文本
                    if match.start() > last_end:
                        before_text = content[last_end:match.start()]
                        if before_text.strip():
                            processed_text, format_styles = self.process_inline_formats(before_text)
                            text_parts.append((processed_text, None, format_styles))
                    
                    # 提取颜色值和文本内容
                    color_value = match.group(1).strip()
                    color_content = match.group(3).strip()
                    processed_content, format_styles = self.process_inline_formats(color_content)
                    text_parts.append((processed_content, color_value, format_styles))
                    last_end = match.end()
                
                # 添加最后一段文本
                if last_end < len(content):
                    remaining_text = content[last_end:]
                    if remaining_text.strip():
                        processed_text, format_styles = self.process_inline_formats(remaining_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 合并所有文本部分
                if text_parts:
                    # 创建基础样式
                    base_style = TextStyle(
                        font_name='bold',
                        indent=0,
                        line_spacing=15,
                        is_list_item=True,
                        is_bold=True
                    )
                    
                    # 合并所有文本
                    combined_text = f"{number}. "
                    for text_part, _, _ in text_parts:
                        combined_text += text_part
                    
                    # 创建包含所有部分的主段落
                    result_segment = TextSegment(text=combined_text, style=base_style)
                    
                    # 构建原始片段
                    original_segments = []
                    
                    # 添加序号作为第一个片段
                    number_style = TextStyle(
                        font_name='bold',
                        line_spacing=15,
                        is_bold=True,
                        is_list_item=True
                    )
                    original_segments.append(TextSegment(
                        text=f"{number}. ",
                        style=number_style
                    ))
                    
                    # 添加每个颜色部分
                    for text_part, color_value, format_styles in text_parts:
                        part_style = TextStyle(
                            font_name='bold' if format_styles['is_bold'] else 'regular',
                            line_spacing=15,
                            text_color=color_value,
                            is_bold=format_styles['is_bold'],
                            is_italic=format_styles['is_italic'],
                            is_list_item=True
                        )
                        original_segments.append(TextSegment(
                            text=text_part,
                            style=part_style
                        ))
                    
                    # 将原始段落附加到结果段落
                    result_segment.original_segments = original_segments
                    
                    return [result_segment]
            
            # 如果不包含颜色标签，按普通方式处理
            processed_content, format_styles = self.process_inline_formats(content)
            style = TextStyle(
                font_name='bold',
                indent=0,
                line_spacing=15,
                is_list_item=True,
                is_bold=True
            )
            return [TextSegment(text=f"{number}. {processed_content}", style=style)]

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

        # 处理三级标题 - 确保去除###符号
        if text.strip().startswith('### '):
            processed_text, format_styles = self.process_inline_formats(text[4:].strip())
            style = TextStyle(
                font_name='bold',
                font_size=32,
                is_title=True,
                line_spacing=20,
                indent=0,
                is_bold=True
            )
            return [TextSegment(text=processed_text, style=style)]
            
        # 处理无序列表项，支持嵌套列表
        list_match = re.match(r'^(\s*)(\*|\-|\+)\s+(.+)$', text)
        if list_match:
            indent_space = len(list_match.group(1))
            list_content = list_match.group(3).strip()
            
            # 检查是否是任务列表项
            task_match = re.match(r'^\[([ xX])\]\s+(.+)$', list_content)
            is_task = False
            is_checked = False
            if task_match:
                is_task = True
                is_checked = task_match.group(1).lower() == 'x'
                list_content = task_match.group(2).strip()
            
            # 设置缩进级别
            indent_level = 40 + indent_space * 8  # 根据前导空格数量计算缩进
            
            # 检查列表项是否包含HTML颜色标签
            if self.html_color_pattern.search(list_content):
                color_segments = []
                last_end = 0
                
                # 标记是否已添加列表标记
                marker_added = False
                
                for match in self.html_color_pattern.finditer(list_content):
                    # 添加标签前的文本
                    if match.start() > last_end:
                        before_text = list_content[last_end:match.start()]
                        if before_text.strip():
                            processed_text, format_styles = self.process_inline_formats(before_text)
                            
                            # 添加列表标记（仅对第一段）
                            if not marker_added:
                                if is_task:
                                    if is_checked:
                                        # 使用原始颜色值而不是固定的绿色或灰色
                                        prefix = "[x] "
                                    else:
                                        prefix = "[ ] "
                                    marker_added = True
                                else:
                                    prefix = "• "
                                    marker_added = True
                            else:
                                prefix = ""
                            
                            style = TextStyle(
                                font_name='bold' if format_styles['is_bold'] else 'regular',
                                indent=indent_level,
                                line_spacing=15,
                                is_list_item=True,
                                is_bold=format_styles['is_bold'],
                                is_italic=format_styles['is_italic']
                            )
                            color_segments.append(TextSegment(text=prefix + processed_text, style=style))
                    
                    # 提取颜色值和文本内容
                    color_value = match.group(1).strip()
                    content = match.group(3).strip()
                    processed_content, format_styles = self.process_inline_formats(content)
                    
                    # 添加列表标记（仅对第一段）
                    if not marker_added:
                        if is_task:
                            if is_checked:
                                # 使用原始颜色值而不是固定的绿色或灰色
                                prefix = "[x] "
                            else:
                                prefix = "[ ] "
                            marker_added = True
                        else:
                            prefix = "• "
                            marker_added = True
                    else:
                        prefix = ""
                    
                    # 创建带颜色的文本段
                    color_style = TextStyle(
                        font_name='bold' if format_styles['is_bold'] else 'regular',
                        indent=indent_level,
                        line_spacing=15,
                        text_color=color_value,
                        is_list_item=True,
                        is_bold=format_styles['is_bold'],
                        is_italic=format_styles['is_italic']
                    )
                    color_segments.append(TextSegment(text=prefix + processed_content, style=color_style))
                    last_end = match.end()
                
                # 添加最后一段文本
                if last_end < len(list_content):
                    remaining_text = list_content[last_end:]
                    if remaining_text.strip():
                        processed_text, format_styles = self.process_inline_formats(remaining_text)
                        
                        # 添加列表标记（仅对第一段）
                        if not marker_added:
                            if is_task:
                                if is_checked:
                                    # 使用原始颜色值而不是固定的绿色或灰色
                                    prefix = "[x] "
                                else:
                                    prefix = "[ ] "
                                marker_added = True
                            else:
                                prefix = "• "
                                marker_added = True
                        else:
                            prefix = ""
                        
                        style = TextStyle(
                            font_name='bold' if format_styles['is_bold'] else 'regular',
                            indent=indent_level,
                            line_spacing=15,
                            is_list_item=True,
                            is_bold=format_styles['is_bold'],
                            is_italic=format_styles['is_italic']
                        )
                        color_segments.append(TextSegment(text=prefix + processed_text, style=style))
                
                # 确保所有段落都被标记为列表项
                for segment in color_segments:
                    segment.style.is_list_item = True
                
                # 如果有多个段落，合并它们
                if len(color_segments) > 1:
                    # 创建一个合并的文本段落
                    combined_text = ""
                    for segment in color_segments:
                        combined_text += segment.text
                    
                    # 基本样式
                    base_style = TextStyle(
                        font_name='regular',
                        indent=indent_level,
                        line_spacing=15,
                        is_list_item=True,
                    )
                    
                    # 创建最终段落
                    result_segment = TextSegment(text=combined_text, style=base_style)
                    result_segment.original_segments = color_segments
                    
                    return [result_segment]
                
                # 返回有颜色的列表项段落
                return color_segments
            
            # 处理不含颜色标签的列表项
            processed_content, format_styles = self.process_inline_formats(list_content)
            
            # 根据是否为任务列表添加不同的标记
            if is_task:
                if is_checked:
                    # 已完成使用绿色文本 [x]
                    style = TextStyle(
                        font_name='bold',
                        indent=indent_level,
                        line_spacing=15,
                        is_list_item=True,
                        text_color="#22AA22",  # 绿色
                        is_bold=True
                    )
                    return [TextSegment(text="[x] " + processed_content, style=style)]
                else:
                    # 未完成使用灰色文本 [ ]
                    style = TextStyle(
                        font_name='bold',
                        indent=indent_level,
                        line_spacing=15,
                        is_list_item=True,
                        text_color="#777777",  # 灰色
                        is_bold=True
                    )
                    return [TextSegment(text="[ ] " + processed_content, style=style)]
            else:
                style = TextStyle(
                    font_name='bold' if format_styles['is_bold'] else 'regular',
                    indent=indent_level,
                    line_spacing=15,
                    is_list_item=True,
                    is_bold=format_styles['is_bold'],
                    is_italic=format_styles['is_italic']
                )
                return [TextSegment(text="• " + processed_content, style=style)]
        
        # 检查普通文本中是否包含HTML颜色标签
        if self.html_color_pattern.search(text):
            color_segments = []
            last_end = 0
            
            # 创建基础样式
            base_style = TextStyle(
                font_name='regular',
                indent=40 if self.current_section else 0,
                line_spacing=15,
            )

            # 将所有颜色标签段落合并到一个列表中
            text_parts = []
            
            for match in self.html_color_pattern.finditer(text):
                # 添加标签前的文本
                if match.start() > last_end:
                    before_text = text[last_end:match.start()]
                    if before_text.strip():
                        processed_text, format_styles = self.process_inline_formats(before_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 提取颜色值和文本内容
                color_value = match.group(1).strip()
                content = match.group(3).strip()
                processed_content, format_styles = self.process_inline_formats(content)
                text_parts.append((processed_content, color_value, format_styles))
                last_end = match.end()
            
            # 添加最后一段文本
            if last_end < len(text):
                remaining_text = text[last_end:]
                if remaining_text.strip():
                    processed_text, format_styles = self.process_inline_formats(remaining_text)
                    text_parts.append((processed_text, None, format_styles))
            
            # 创建一个包含所有文本部分的段落
            if text_parts:
                # 合并所有文本部分到一个单一的TextSegment中
                combined_text = ""
                # 使用基础样式
                style = TextStyle(
                    font_name='regular',
                    indent=40 if self.current_section else 0,
                    line_spacing=15,
                )
                
                # 创建每个部分的TextSegment
                segments = []
                for text_part, color_value, format_styles in text_parts:
                    style = TextStyle(
                        font_name='bold' if format_styles['is_bold'] else 'regular',
                        indent=40 if self.current_section else 0,
                        line_spacing=15,
                        text_color=color_value,
                        is_bold=format_styles['is_bold'],
                        is_italic=format_styles['is_italic']
                    )
                    # 添加当前部分的文本到合并文本
                    combined_text += text_part
                    segments.append(TextSegment(text=text_part, style=style))
                
                # 如果只有一个部分，直接返回它
                if len(segments) == 1:
                    return segments
                
                # 否则收集并合并每个部分的文本内容，然后返回一个包含所有文本的TextSegment
                result_text = ""
                for segment in segments:
                    result_text += segment.text
                
                # 创建一个新的TextSegment，包含所有文本
                result_style = TextStyle(
                    font_name='regular',
                    indent=40 if self.current_section else 0,
                    line_spacing=15,
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
            # 检查内容是否包含HTML颜色标签
            if self.html_color_pattern.search(content):
                color_segments = []
                last_end = 0
                
                # 准备收集所有颜色段落
                text_parts = []
                
                # 处理所有颜色标签
                for match in self.html_color_pattern.finditer(content):
                    # 添加标签前的文本
                    if match.start() > last_end:
                        before_text = content[last_end:match.start()]
                        if before_text.strip():
                            processed_text, format_styles = self.process_inline_formats(before_text)
                            text_parts.append((processed_text, None, format_styles))
                    
                    # 提取颜色值和文本内容
                    color_value = match.group(1).strip()
                    colored_content = match.group(3).strip()
                    processed_content, format_styles = self.process_inline_formats(colored_content)
                    text_parts.append((processed_content, color_value, format_styles))
                    last_end = match.end()
                
                # 添加最后一段文本
                if last_end < len(content):
                    remaining_text = content[last_end:]
                    if remaining_text.strip():
                        processed_text, format_styles = self.process_inline_formats(remaining_text)
                        text_parts.append((processed_text, None, format_styles))
                
                # 创建一个带有序号的合并段落
                if text_parts:
                    # 合并所有文本为一个段落
                    combined_text = ""
                    for text_part, _, _ in text_parts:
                        combined_text += text_part
                    
                    # 基础样式
                    base_style = TextStyle(
                        font_name='bold',
                        indent=0,
                        line_spacing=15,
                        is_list_item=True,
                    )
                    
                    # 创建最终段落，包含序号
                    combined_text_with_number = f"{number}. {combined_text}"
                    result_segment = TextSegment(text=combined_text_with_number, style=base_style)
                    
                    # 创建原始段落信息
                    original_segments = []
                    
                    # 添加序号作为第一个段落
                    number_style = TextStyle(
                        font_name='bold',
                        indent=0,
                        line_spacing=15,
                        is_bold=True,
                        is_list_item=True
                    )
                    original_segments.append(TextSegment(
                        text=f"{number}. ",
                        style=number_style
                    ))
                    
                    # 添加每个颜色部分
                    for text_part, color_value, format_styles in text_parts:
                        part_style = TextStyle(
                            font_name='bold' if format_styles['is_bold'] else 'regular',
                            indent=0,
                            line_spacing=15,
                            text_color=color_value,
                            is_bold=format_styles['is_bold'],
                            is_italic=format_styles['is_italic'],
                            is_list_item=True
                        )
                        original_segments.append(TextSegment(
                            text=text_part,
                            style=part_style
                        ))
                    
                    # 将原始段落附加到结果
                    result_segment.original_segments = original_segments
                    return [result_segment]
            
            # 如果没有颜色标签，使用原来的逻辑处理
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
        """测量文本尺寸，考虑emoji和HTML标签"""
        # 移除HTML标签，只测量实际可见文本
        text_without_tags = re.sub(r'<[^>]*?>', '', text)
        
        total_width = 0
        max_height = 0

        for char in text_without_tags:
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
        if hasattr(style, '_source_segment') and hasattr(style._source_segment, 'original_segments'):
            # 使用原始段落进行绘制
            current_x = x
            for segment in style._source_segment.original_segments:
                segment_font = self.font_manager.get_font(segment.style)
                segment_style = segment.style
                segment_text = segment.text
                segment_color = fill
                if segment_style.text_color:
                    segment_color = segment_style.text_color
                
                # 绘制这个段落
                width = self.draw_text_with_emoji(
                    draw, (current_x, y), segment_text,
                    segment_font, emoji_font, segment_color, segment_style
                )
                current_x += width
                total_width += width
            
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

    def split_text_to_lines(self, segment: TextSegment, available_width: int) -> List[ProcessedLine]:
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
            emoji_font = self.font_manager.fonts.get('emoji_30')
            
            # 测量行高
            _, height = self.measure_text(segment.text, font, emoji_font)
            
            # 创建ProcessedLine时传递原始段落信息
            processed_line = ProcessedLine(
                text=segment.text,
                style=segment.style,
                height=height,
                line_count=1
            )
            # 附加原始段落信息
            processed_line.style._source_segment = segment
            
            processed_lines.append(processed_line)
            return processed_lines
        
        # 获取字体和emoji字体
        font = self.font_manager.get_font(segment.style)
        emoji_font = self.font_manager.fonts.get('emoji_30')
        
        # 代码块特殊处理 - 保留原始换行符
        if segment.style.is_code:
            lines = segment.text.split('\n')
            for line in lines:
                if not line:  # 对于空行，添加一个空行
                    height = font.size
                    processed_lines.append(ProcessedLine(
                        text='',
                        style=segment.style,
                        height=height,
                        line_count=1
                    ))
                    continue
                
                # 测量行高
                _, height = self.measure_text(line, font, emoji_font)
                
                # 如果行内容太长，需要自动换行
                current_line = ''
                words = []
                current_word = ''
                
                # 分词处理
                for char in line:
                    if emoji.is_emoji(char):
                        if current_word:
                            words.append(current_word)
                            current_word = ''
                        words.append(char)  # emoji作为单独的词
                    elif char in [' ', '\t']:
                        if current_word:
                            words.append(current_word)
                        words.append(char)
                        current_word = ''
                    else:
                        current_word += char
                
                if current_word:
                    words.append(current_word)
                
                current_line = ''
                for word in words:
                    test_line = current_line + word
                    width, _ = self.measure_text(test_line, font, emoji_font)
                    
                    if width <= available_width:
                        current_line = test_line
                    else:
                        # 如果当前行不为空，添加为独立行
                        if current_line:
                            processed_lines.append(ProcessedLine(
                                text=current_line,
                                style=segment.style,
                                height=height,
                                line_count=1
                            ))
                        # 开始新行
                        current_line = word
                
                # 添加最后一行
                if current_line:
                    processed_lines.append(ProcessedLine(
                        text=current_line,
                        style=segment.style,
                        height=height,
                        line_count=1
                    ))
            
            return processed_lines

        # 获取字体和emoji字体
        font = self.font_manager.get_font(segment.style)
        emoji_font = self.font_manager.fonts.get('emoji_30')
        
        # 获取单词列表
        words = []
        current_word = ''
        for char in segment.text:
            if emoji.is_emoji(char):
                if current_word:
                    words.append(current_word)
                    current_word = ''
                words.append(char)  # emoji作为单独的词
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

        current_line = ''
        line_height = 0

        for word in words:
            test_line = current_line + word
            width, height = self.measure_text(test_line, font, emoji_font)
            line_height = max(line_height, height)

            if width <= available_width:
                current_line = test_line
            else:
                if current_line:
                    processed_lines.append(ProcessedLine(
                        text=current_line,
                        style=segment.style,
                        height=line_height,
                        line_count=1
                    ))
                current_line = word

        if current_line:
            processed_lines.append(ProcessedLine(
                text=current_line,
                style=segment.style,
                height=line_height,
                line_count=1
            ))

        return processed_lines

    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont, available_width: int) -> List[str]:
        """将文本换行为适合宽度的多行，保持HTML标签完整性"""
        if not text:
            return ['']
        
        # 检查是否是列表项
        is_list_item = False
        list_prefix = ""
        list_content = text
        
        # 检查数字列表和其他列表类型
        match = re.match(r'^(\d+\.\s+)(.+)$', text)
        if match:
            is_list_item = True
            list_prefix = match.group(1)
            list_content = match.group(2)
            
            # 缩短前缀宽度，考虑到缩进
            prefix_width, _ = self.measure_text(list_prefix, font, emoji_font)
            # 减少可用宽度，但确保至少有300像素
            available_width = max(300, available_width - prefix_width)
        else:
            # 检查无序列表
            match = re.match(r'^([•●◦○※·]\s+)(.+)$', text)
            if match:
                is_list_item = True
                list_prefix = match.group(1)
                list_content = match.group(2)
                
                # 计算列表前缀的宽度
                prefix_width, _ = self.measure_text(list_prefix, font, emoji_font)
                # 减少可用宽度，但确保至少有300像素
                available_width = max(300, available_width - prefix_width)
        
        # 预处理：将所有HTML标签替换为特殊标记，避免在标签内部分词
        html_tags = []
        
        def replace_tag(match):
            tag = match.group(0)
            placeholder = f"__HTML_TAG_{len(html_tags)}__"
            html_tags.append(tag)
            return placeholder
        
        # 更精确的颜色标签匹配模式
        color_tag_pattern = re.compile(r'<span\s+style=["\']color:\s*[^;"\']+[;"\'](.*?)>.*?</span>', re.DOTALL | re.IGNORECASE)
        
        # 替换所有HTML标签为占位符
        processed_content = re.sub(color_tag_pattern, replace_tag, list_content)
        
        # 分词处理，使用更智能的分词策略
        words = []
        current_word = ''
        
        # 特殊处理中文、英文、标点和emoji
        for char in processed_content:
            if emoji.is_emoji(char):
                # Emoji作为单独词处理
                if current_word:
                    words.append(current_word)
                    current_word = ''
                words.append(char)
            elif char in [' ', '\t', '\n', '，', '。', '！', '？', '；', '：', '、']:
                # 空格和标点作为分隔符
                if current_word:
                    words.append(current_word)
                words.append(char)
                current_word = ''
            elif '__HTML_TAG_' in current_word:
                # 如果当前单词包含占位符，添加并重新开始
                words.append(current_word)
                current_word = char
            elif ord(char) > 0x4E00 and ord(char) < 0x9FFF:
                # 中文字符单独处理
                if current_word:
                    words.append(current_word)
                    current_word = ''
                words.append(char)
            else:
                # 其他字符（主要是英文和数字）累积为单词
                current_word += char
        
        if current_word:
            words.append(current_word)
        
        # 过滤空词
        words = [w for w in words if w.strip() or '__HTML_TAG_' in w]
        
        # 恢复HTML标签
        for i, word in enumerate(words):
            for j, tag in enumerate(html_tags):
                if f"__HTML_TAG_{j}__" in word:
                    words[i] = word.replace(f"__HTML_TAG_{j}__", tag)
        
        # 换行处理
        lines = []
        current_line = ''
        
        for i, word in enumerate(words):
            # 处理换行符
            if word == '\n':
                if is_list_item and not lines:
                    lines.append(list_prefix + current_line)
                else:
                    lines.append(current_line)
                current_line = ''
                continue
            
            # 检查是否包含HTML标签
            contains_tag = '<span' in word and '</span>' in word
            
            # 获取实际文本内容（不含标签）
            text_without_tags = re.sub(r'<[^>]*?>', '', word)
            
            # 测量单词宽度
            word_width, _ = self.measure_text(text_without_tags, font, emoji_font)
            
            # HTML标签内容可能很长，给它更多空间
            if contains_tag:
                word_width += 10  # 稍微增加宽度，确保标签完整显示
            
            # 测试行宽度
            test_line = current_line + word
            test_line_without_tags = re.sub(r'<[^>]*?>', '', test_line)
            line_width, _ = self.measure_text(test_line_without_tags, font, emoji_font)
            
            # 判断是否需要换行
            if line_width <= available_width:
                # 宽度足够，继续当前行
                current_line = test_line
            else:
                # 需要换行
                if current_line:
                    # 添加当前行到结果
                    if is_list_item and not lines:
                        lines.append(list_prefix + current_line)
                        is_list_item = False  # 只有第一行添加前缀
                    else:
                        lines.append(current_line)
                    current_line = word
                else:
                    # 单词本身超过行宽度
                    if contains_tag:
                        # 处理超长的带标签单词，尝试按字符分割但保持标签完整
                        tag_match = re.match(r'(<span[^>]*>)(.*?)(</span>)', word)
                        if tag_match:
                            open_tag = tag_match.group(1)
                            content = tag_match.group(2)
                            close_tag = tag_match.group(3)
                            
                            # 尝试按字符分割内容
                            chars = list(content)
                            current_chunk = ''
                            
                            for char in chars:
                                test_chunk = current_chunk + char
                                chunk_width, _ = self.measure_text(test_chunk, font, emoji_font)
                                
                                if chunk_width <= available_width - 60:  # 预留标签空间
                                    current_chunk = test_chunk
                                else:
                                    # 将当前块添加为一行
                                    if current_chunk:
                                        full_tag = open_tag + current_chunk + close_tag
                                        if is_list_item and not lines:
                                            lines.append(list_prefix + full_tag)
                                            is_list_item = False
                                        else:
                                            lines.append(full_tag)
                                    current_chunk = char
                            
                            # 添加最后一块
                            if current_chunk:
                                full_tag = open_tag + current_chunk + close_tag
                                current_line = full_tag
                            else:
                                current_line = ''
                        else:
                            # 无法解析标签，作为一整行添加
                            if is_list_item and not lines:
                                lines.append(list_prefix + word)
                                is_list_item = False
                            else:
                                lines.append(word)
                    else:
                        # 普通长单词，按字符分割
                        char_line = ''
                        for char in word:
                            test_char = char_line + char
                            char_width, _ = self.measure_text(test_char, font, emoji_font)
                            
                            if char_width <= available_width:
                                char_line = test_char
                            else:
                                if char_line:
                                    if is_list_item and not lines:
                                        lines.append(list_prefix + char_line)
                                        is_list_item = False
                                    else:
                                        lines.append(char_line)
                                char_line = char
                        
                        # 添加最后部分
                        if char_line:
                            current_line = char_line
        
        # 添加最后一行
        if current_line:
            if is_list_item and not lines:
                lines.append(list_prefix + current_line)
            else:
                lines.append(current_line)
        
        # 如果没有任何行，返回空字符串或前缀
        if not lines:
            if is_list_item:
                return [list_prefix]
            else:
                return ['']
        
        return lines


def compress_image(image_path: str, output_path: str, max_size: int = 3145728):  # 3MB in bytes
    """
    Compress an image to ensure it's under a certain file size.

    :param image_path: The path to the image to be compressed.
    :param output_path: The path where the compressed image will be saved.
    :param max_size: The maximum file size in bytes (default is 3MB).
    """
    # Open the image
    with Image.open(image_path) as img:
        # Convert to RGB if it's not already
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Define the quality to start with
        quality = 95  # Start with a high quality

        # Save the image with different qualities until the file size is acceptable
        while True:
            # Save the image with the current quality
            img.save(output_path, "PNG", optimize=True, compress_level=0)

            # Check the file size
            if os.path.getsize(output_path) <= max_size:
                break  # The file size is acceptable, break the loop

            # If the file is still too large, decrease the quality
            quality -= 5
            if quality < 10:  # To prevent an infinite loop, set a minimum quality
                break

        # If the quality is too low, you might want to handle it here
        if quality < 10:
            print("The image could not be compressed enough to meet the size requirements.")


def preprocess_text(input_text: str) -> Tuple[Optional[str], str]:
    """预处理输入文本，解析JSON并提取可用的文本内容
    
    Args:
        input_text: 输入文本，可能是JSON格式或普通文本
        
    Returns:
        Tuple[Optional[str], str]: (logo_url, content_text)
        logo_url可能为None，content_text为处理后的文本内容
    """
    # 处理HTML标签中的转义字符，确保所有标签都能被正确解析
    
    # 统一处理HTML标签中的各种可能的转义情况
    def clean_html_tags(text):
        # 使用正则表达式查找所有<span>标签
        span_pattern = re.compile(r'<span\s+[^>]*?style=[\\"]?[^>]*?>[^<]*?</span>', re.DOTALL | re.IGNORECASE)
        
        def clean_tag(match):
            tag = match.group(0)
            # 替换所有转义的引号
            tag = tag.replace('\\"', '"').replace("\\'", "'")
            
            # 提取style属性，确保格式统一
            style_match = re.search(r'style\s*=\s*["\']([^"\']*)["\']', tag)
            if style_match:
                style_content = style_match.group(1)
                
                # 提取color属性，规范化颜色格式
                color_match = re.search(r'color\s*:\s*([^;"\'\s]+)', style_content)
                if color_match:
                    color_value = color_match.group(1).strip()
                    
                    # 规范化颜色值格式
                    if not color_value.startswith('#') and not re.match(r'^[a-zA-Z]+$', color_value):
                        color_value = '#' + color_value  # 添加井号
                    
                    # 构建新的标签，确保格式统一
                    new_style = f'color: {color_value}'
                    new_tag = f'<span style="{new_style}">'
                    
                    # 提取内容
                    content_match = re.search(r'>(.*?)</span>', tag)
                    if content_match:
                        content = content_match.group(1)
                        new_tag += content + '</span>'
                        return new_tag
            
            return tag
        
        # 应用标签清理
        cleaned_text = span_pattern.sub(clean_tag, text)
        
        # 修复可能的标签嵌套错误
        open_tags = []
        result = []
        i = 0
        while i < len(cleaned_text):
            # 查找开始标签
            if cleaned_text[i:i+5] == '<span':
                tag_end = cleaned_text.find('>', i)
                if tag_end != -1:
                    open_tag = cleaned_text[i:tag_end+1]
                    open_tags.append(open_tag)
                    result.append(open_tag)
                    i = tag_end + 1
                    continue
            
            # 查找结束标签
            if cleaned_text[i:i+7] == '</span>':
                if open_tags:
                    open_tags.pop()  # 弹出最近的开始标签
                result.append('</span>')
                i += 7
                continue
            
            # 普通字符
            result.append(cleaned_text[i])
            i += 1
        
        # 处理未闭合的标签
        for _ in open_tags:
            result.append('</span>')
        
        return ''.join(result)
    
    # 应用HTML标签清理
    input_text = clean_html_tags(input_text)
    
    # 首先检查是否包含|LOGO|分隔符（大写）
    logo_url = None
    content_text = input_text
    
    if "|LOGO|" in input_text:
        parts = input_text.split("|LOGO|", 1)
        if len(parts) == 2:
            logo_url = parts[0].strip()
            content_text = parts[1].strip()
            
            # 如果剩余内容为空，使用默认文本
            if not content_text:
                content_text = "图片卡片"
    
    # 如果没有使用分隔符，则检查文本内容开头是否为图片URL
    elif content_text:
        url_pattern = r'^(https?://\S+\.(jpg|jpeg|png|gif|webp))(.*)$'
        match = re.match(url_pattern, content_text, re.IGNORECASE | re.DOTALL)
        
        if match:
            # 如果消息内容以图片URL开头，则将其作为logo
            logo_url = match.group(1)
            remaining_text = match.group(3).strip()
            
            # 如果剩余内容为空，使用默认文本
            if not remaining_text:
                remaining_text = "图片卡片"
                
            # 更新内容
            content_text = remaining_text
    
    # 尝试解析为JSON
    try:
        # 检查是否是JSON格式
        if content_text.strip().startswith('{') and content_text.strip().endswith('}'):
            data = json.loads(content_text)
            result_text = ""
            
            # 提取"result"字段
            if "result" in data:
                result_content = data["result"]
                # 处理转义的换行符
                result_content = result_content.replace('\\n', '\n')
                result_text += result_content + "\n\n"
            
            # 提取"text"字段
            if "text" in data:
                text_content = data["text"]
                # 处理转义的换行符
                text_content = text_content.replace('\\n', '\n')
                # 去除HTML标签
                text_content = re.sub(r'<[^>]+>', '', text_content)
                # 处理HTML实体
                text_content = html.unescape(text_content)
                result_text += text_content
            
            # 处理特殊标记
            result_text = result_text.replace('!~!', '\n')
            
            return logo_url, result_text
    except (json.JSONDecodeError, AttributeError, TypeError):
        # 如果不是有效的JSON或解析出错，返回原始文本
        pass
    
    return logo_url, content_text


def generate_image(text: str, output_path: str, title_image: Optional[str] = None):
    """生成图片主函数 - 修复彩色emoji渲染"""
    try:
        # 预处理输入文本 - 只处理文本内容，不处理logo
        _, text = preprocess_text(text)
        
        width = 720
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = {
            'regular': os.path.join(current_dir, "msyh.ttc"),
            'bold': os.path.join(current_dir, "msyhbd.ttc"),
            'emoji': os.path.join(current_dir, "TwitterColorEmoji.ttf")  # 彩色emoji字体
        }
        
        # 验证字体文件
        for font_type, path in font_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Font file not found: {path}")
    
        # 获取主题颜色 - 在解析文本前获取，用于传递给TextStyle
        background_color, text_color, is_dark_theme = get_theme_colors()
        
        # 初始化组件
        font_manager = FontManager(font_paths)
        rect_width = width - 80
        
        # 获取渐变样式
        gradient_styles = get_gradient_styles()
        selected_style = random.choice(gradient_styles)
        
        # 设置文本区域宽度
        rect_width = 640
        
        # 创建文本渲染器
        max_content_width = rect_width - 80
        parser = MarkdownParser()
        renderer = TextRenderer(font_manager, max_content_width)

        # 如果有标题图片，在文本前添加分隔符
        if title_image:
            # 添加一个空行作为分隔
            text = "\n\n" + text
        
        # 解析文本
        segments = parser.parse(text)
        # 设置主题信息
        for segment in segments:
            segment.style.is_dark_theme = is_dark_theme
            
        processed_lines = []

        for segment in segments:
            available_width = max_content_width - segment.style.indent
            if segment.text.strip():
                lines = renderer.split_text_to_lines(segment, available_width)
                processed_lines.extend(lines)
            else:
                processed_lines.append(ProcessedLine(
                    text='',
                    style=segment.style,
                    height=0,
                    line_count=1
                ))

        # 计算高度
        title_height = 0
        if title_image:
            try:
                if isinstance(title_image, str) and title_image.startswith(('http://', 'https://')):
                    response = requests.get(title_image)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(title_image)
                aspect_ratio = img.height / img.width
                title_height = int((rect_width - 40) * aspect_ratio) + 40
            except Exception as e:
                print(f"Title image processing error: {e}")

        content_height = renderer.calculate_height(processed_lines)
        
        # 确保最小高度，使短文本也有合适的显示空间
        min_content_height = 300  # 最小内容高度
        content_height = max(content_height, min_content_height)
        
        rect_height = content_height + title_height
        rect_x = (width - rect_width) // 2
        rect_y = 40
        total_height = rect_height + 80  # 上下各添加40像素的边距

        # 创建RGBA背景
        background = create_gradient_background(width, total_height)
        draw = ImageDraw.Draw(background)

        if len(background_color) == 3:
            background_color = background_color + (128,)  # 添加alpha通道

        # 创建卡片背景
        create_rounded_rectangle(
            background, rect_x, rect_y, rect_width, rect_height,
            radius=30, bg_color=background_color
        )

        # 绘制内容
        current_y = rect_y + 30
        if title_image:
            current_y = add_title_image(background, title_image, rect_x, rect_y, rect_width)

        # 逐行渲染文本
        for i, line in enumerate(processed_lines):
            if not line.text.strip():
                if i < len(processed_lines) - 1 and any(l.text.strip() for l in processed_lines[i + 1:]):
                    current_y += line.style.line_spacing
                continue

            # 计算文本起始位置
            base_x = rect_x + 40
            
            # 处理对齐方式
            if hasattr(line.style, 'alignment') and line.style.alignment == 'right':
                # 右对齐：先计算文本宽度
                font = font_manager.get_font(line.style)
                text_width = 0
                for char in line.text:
                    if emoji.is_emoji(char):
                        emoji_font = font_manager.fonts['emoji_30']
                        bbox = draw.textbbox((0, 0), char, font=emoji_font)
                    else:
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

        # 直接保存为PNG，保持RGBA模式
        background = background.convert('RGB')
        background.save(output_path, "PNG", optimize=False, compress_level=0)

    except Exception as e:
        print(f"Error generating image: {e}")
        raise


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
