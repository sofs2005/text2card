# utf-8
# image_generator.py
"""
Advanced image card generator with markdown and emoji support
"""
import math
import random
import os
import io
from io import BytesIO  # 显式导入BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import emoji
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import time
from PIL import UnidentifiedImageError
import json
import html
import gc

# 导入配置
try:
    from config import config
except ImportError:
    # 如果无法导入配置，使用默认签名
    class DummyConfig:
        SIGNATURE_TEXT = "—飞天"
    config = DummyConfig()

# 使用国内CDN替代jsdelivr
# 按优先级排序的CDN列表
EMOJI_CDN_URLS = [
    # 国内CDN源
    "https://npm.elemecdn.com/twemoji@latest/assets/72x72/",  # 饿了么CDN (国内较快)
    "https://cdn.bootcdn.net/ajax/libs/twemoji/14.0.2/assets/72x72/",  # BootCDN (国内较快)
    "https://lib.baomitu.com/twemoji/latest/assets/72x72/",  # 360 前端静态资源库
    # 国际CDN源 (作为备选)
    "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/",  # jsDelivr
    "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/assets/72x72/"  # Cloudflare
]

# 全局变量记录可用的CDN
working_cdn_url = None
emoji_image_cache = {}

def codepoint_to_twemoji(codepoint):
    """将Unicode码点转换为Twemoji文件名格式"""
    if '-' in codepoint:
        # 处理多个码点的情况
        return '-'.join([cp.lower() for cp in codepoint.split('-')])
    else:
        return codepoint.lower()

def get_emoji_codepoint(emoji_char):
    """获取emoji的Unicode码点，格式化为Twemoji URL所需格式"""
    if len(emoji_char) == 1:
        # 单个码点
        return format(ord(emoji_char), 'x')
    else:
        # 复合emoji (如表情+肤色修饰符)
        return '-'.join([format(ord(c), 'x') for c in emoji_char])

def get_twemoji_image(emoji_char: str, size: int = 30) -> Optional[Image.Image]:
    """从多个CDN源获取emoji图片"""
    global working_cdn_url
    cache_key = f"{emoji_char}_{size}"
    if cache_key in emoji_image_cache:
        return emoji_image_cache[cache_key].copy()
        
    try:
        # 获取emoji的Unicode码点
        codepoint = get_emoji_codepoint(emoji_char)
        twemoji_codepoint = codepoint_to_twemoji(codepoint)
        
        # 依次尝试所有CDN直到成功
        cdn_urls = EMOJI_CDN_URLS.copy()
        
        # 如果已知有工作的CDN，优先使用
        if working_cdn_url and working_cdn_url in cdn_urls:
            cdn_urls.remove(working_cdn_url)
            cdn_urls.insert(0, working_cdn_url)
        
        success = False
        for cdn_url in cdn_urls:
            # 构建URL (Twemoji使用.png文件)
            url = f"{cdn_url}{twemoji_codepoint}.png"
            
            try:
                # 尝试获取图片，设置更长的超时时间
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    # 创建图像对象
                    img = Image.open(io.BytesIO(response.content))
                    # 确保转换为RGBA模式 - 修复透明度问题
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    # 调整大小
                    img = img.resize((size, size))
                    # 存入缓存
                    emoji_image_cache[cache_key] = img.copy()
                    # 记录有效的CDN
                    working_cdn_url = cdn_url
                    print(f"成功获取Twemoji: {emoji_char} (URL: {url})")
                    success = True
                    return img
            except Exception as e:
                print(f"从 {cdn_url} 获取emoji失败: {e}")
                continue
        
        if not success:
            # 所有CDN都失败，尝试处理多码点emoji
            if len(emoji_char) > 1:
                # 有些复合emoji可能使用不同的文件命名约定
                alt_codepoint = format(ord(emoji_char[0]), 'x')
                
                for cdn_url in cdn_urls:
                    alt_url = f"{cdn_url}{alt_codepoint}.png"
                    try:
                        alt_response = requests.get(alt_url, timeout=5)
                        if alt_response.status_code == 200:
                            img = Image.open(io.BytesIO(alt_response.content))
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')
                            img = img.resize((size, size))
                            emoji_image_cache[cache_key] = img.copy()
                            working_cdn_url = cdn_url
                            print(f"成功获取替代Twemoji: {emoji_char} (URL: {alt_url})")
                            return img
                    except Exception:
                        continue
            
            print(f"所有CDN获取emoji失败: {emoji_char}")
            return None
    except Exception as e:
        print(f"下载Twemoji出错: {e}")
        return None

def get_local_emoji_image(emoji_char: str, size: int = 30) -> Optional[Image.Image]:
    """从本地缓存获取emoji图片，如果没有则从CDN下载"""
    try:
        # 获取emoji的Unicode码点
        codepoint = get_emoji_codepoint(emoji_char)
        
        # 本地emoji图片路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        emoji_dir = os.path.join(current_dir, "emoji_images")
        
        # 如果目录不存在，创建它
        if not os.path.exists(emoji_dir):
            os.makedirs(emoji_dir)
            
        emoji_path = os.path.join(emoji_dir, f"{codepoint}.png")
        
        # 如果本地存在图片，直接返回
        if os.path.exists(emoji_path):
            try:
                img = Image.open(emoji_path)
                # 确保转换为RGBA模式 - 修复透明度问题
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img = img.resize((size, size))
                return img
            except Exception as e:
                print(f"读取本地emoji图片失败: {e}，尝试重新下载")
                # 如果本地图片损坏，尝试重新下载
                os.remove(emoji_path)
            
        # 如果本地没有，尝试下载并保存
        img = get_twemoji_image(emoji_char, size)
        if img:
            # 确保图像是RGBA模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            try:
                img.save(emoji_path)
            except Exception as e:
                print(f"保存emoji图片到本地失败: {e}")
            return img
            
        return None
    except Exception as e:
        print(f"获取本地emoji图片失败: {e}")
        return None

# 尝试创建带有文本的emoji图片（作为最后的备选方案）
def create_text_emoji(emoji_char: str, size: int = 30) -> Optional[Image.Image]:
    """创建文本版emoji图片（当无法从网络获取时）"""
    try:
        # 创建透明背景图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 使用默认字体
        font_size = size - 10  # 稍微小一点避免被裁剪
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, "msyh.ttc")
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            # 如果无法加载字体，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文本位置使其居中
        bbox = draw.textbbox((0, 0), emoji_char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # 绘制emoji文本
        draw.text((x, y), emoji_char, font=font, fill=(0, 0, 0, 255))
        
        return img
    except Exception as e:
        print(f"创建文本emoji失败: {e}")
        return None

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
    is_horizontal_rule: bool = False  # 是否为水平分割线
    is_task_list: bool = False  # 是否为任务列表
    task_checked: bool = False  # 任务是否已完成
    is_ordered_list: bool = False  # 是否为有序列表


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
        
        # 打印字体文件路径用于调试
        print(f"正在加载emoji字体: {self.font_paths.get('emoji', '未指定')}")
        if 'emoji' in self.font_paths:
            print(f"字体文件存在: {os.path.exists(self.font_paths['emoji'])}")

    def _initialize_fonts(self):
        """初始化基础字体"""
        sizes = [30, 35, 40]  # 基础字号
        for size in sizes:
            self.fonts[f'regular_{size}'] = ImageFont.truetype(self.font_paths['regular'], size)
            self.fonts[f'bold_{size}'] = ImageFont.truetype(self.font_paths['bold'], size)
        # emoji字体 - 现在使用Noto Sans字体
        try:
            self.fonts['emoji_30'] = ImageFont.truetype(self.font_paths['emoji'], 30)
            print("Emoji字体加载成功")
        except Exception as e:
            print(f"Emoji字体加载失败: {e}")
            # 尝试使用常规字体作为备用
            self.fonts['emoji_30'] = self.fonts['regular_30']
            print("使用常规字体作为emoji备用")

    def get_font(self, style: TextStyle) -> ImageFont.FreeTypeFont:
        """获取对应样式的字体"""
        if style.font_name == 'emoji':
            return self.fonts['emoji_30']

        base_name = 'bold' if style.font_name == 'bold' or style.is_title or style.is_category else 'regular'
        font_key = f'{base_name}_{style.font_size}'

        if font_key not in self.fonts:
            # 动态创建新字号的字体
            self.fonts[font_key] = ImageFont.truetype(
                self.font_paths['bold' if base_name == 'bold' else 'regular'],
                style.font_size
            )

        return self.fonts[font_key]


def get_gradient_styles() -> List[Dict[str, tuple]]:
    """
    获取精心设计的背景渐变样式
    """
    return [
        # 现代简约系列 - 增强对比度
        {
            "start_color": (235, 245, 255),  # 浅蓝白
            "end_color": (210, 225, 245)  # 淡蓝灰
        },
        {
            "start_color": (235, 232, 250),  # 淡紫白
            "end_color": (210, 205, 235)  # 柔和紫灰
        },
        
        # 清新活力系列 - 更明显的渐变
        {
            "start_color": (180, 220, 255),  # 明亮蓝
            "end_color": (230, 240, 255)  # 淡蓝白
        },
        {
            "start_color": (220, 240, 255),  # 清新天蓝
            "end_color": (255, 230, 220)  # 温暖橘粉
        },
        
        # 精致渐变系列 - 提高色彩饱和度
        {
            "start_color": (255, 230, 230),  # 柔和粉红
            "end_color": (230, 230, 255)  # 淡雅紫蓝
        },
        {
            "start_color": (230, 255, 240),  # 清新薄荷
            "end_color": (240, 230, 255)  # 淡紫丁香
        },
        
        # 自然色彩系列 - 更加鲜明
        {
            "start_color": (220, 245, 220),  # 清新草绿
            "end_color": (250, 245, 220)  # 温暖米色
        },
        {
            "start_color": (230, 255, 230),  # 明亮嫩绿
            "end_color": (230, 230, 255)  # 淡雅蓝紫
        },
        
        # 高级质感系列 - 增强反差
        {
            "start_color": (235, 225, 245),  # 高级紫灰
            "end_color": (245, 235, 225)  # 温暖米色
        },
        {
            "start_color": (225, 235, 250),  # 高级蓝灰
            "end_color": (250, 235, 240)  # 淡粉灰
        },
        
        # 专业商务系列 - 更有力度
        {
            "start_color": (210, 230, 255),  # 商务蓝
            "end_color": (250, 250, 255)  # 纯净白蓝
        },
        {
            "start_color": (225, 225, 235),  # 高级灰
            "end_color": (245, 245, 255)  # 淡雅蓝白
        },
        
        # 轻松愉悦系列 - 视觉冲击更强
        {
            "start_color": (255, 235, 205),  # 明亮米色
            "end_color": (205, 235, 255)  # 清爽蓝色
        },
        {
            "start_color": (225, 255, 240),  # 薄荷绿
            "end_color": (255, 225, 215)  # 暖橘粉
        },
        
        # 科技感系列 - 更加鲜明
        {
            "start_color": (200, 225, 255),  # 科技蓝
            "end_color": (225, 200, 255)  # 科技紫
        },
        {
            "start_color": (200, 245, 235),  # 高级青绿
            "end_color": (235, 235, 255)  # 淡雅紫白
        }
    ]


def create_gradient_background(width: int, height: int) -> Image.Image:
    """创建渐变背景 - 从左上到右下的对角线渐变，增强效果"""
    gradient_styles = get_gradient_styles()
    style = random.choice(gradient_styles)
    start_color = style["start_color"]
    end_color = style["end_color"]

    # 创建基础图像
    base = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(base)

    # 计算渐变 - 使用指数曲线增强渐变效果
    for y in range(height):
        for x in range(width):
            # 计算当前位置到左上角的相对距离 (对角线渐变)
            # 使用非线性渐变使效果更加明显
            raw_position = (x + y) / (width + height)
            
            # 使用幂函数调整渐变曲线，增强对比
            # pow(raw_position, 0.85) 使渐变在整体上略微倾向于起始色
            position = pow(raw_position, 0.85)  

            # 为每个颜色通道计算渐变值，并增加轻微的通道差异以提高视觉效果
            r = int(start_color[0] * (1 - position) + end_color[0] * position)
            g = int(start_color[1] * (1 - position * 1.05) + end_color[1] * position * 1.05)  # 轻微调整绿色通道
            b = int(start_color[2] * (1 - position * 0.95) + end_color[2] * position * 0.95)  # 轻微调整蓝色通道
            
            # 确保值在合法范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            # 绘制像素
            draw.point((x, y), fill=(r, g, b))

    return base


def get_theme_colors() -> Tuple[tuple, str, bool]:
    """获取主题颜色配置"""
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute

    if (current_hour == 8 and current_minute >= 30) or (9 <= current_hour < 19):
        use_dark = random.random() < 0.15  # 略微增加深色主题出现概率
    else:
        use_dark = True

    if use_dark:
        # 深色毛玻璃效果: 使用更舒适且对比度更高的深色背景 + 明亮文字
        return ((35, 38, 50, 190), "#FFFFFF", True)  # 深蓝灰色 + 纯白文字，增加透明度
    else:
        # 浅色毛玻璃效果: 纯净白色背景 + 深色文字
        return ((250, 250, 252, 190), "#2A2A35", False)  # 纯净白 + 深沉灰蓝，增加透明度


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
    """添加标题图片"""
    try:
        with Image.open(title_image_path) as title_img:
            # 如果图片不是RGBA模式，转换为RGBA
            if title_img.mode != 'RGBA':
                title_img = title_img.convert('RGBA')

            # 设置图片宽度等于文字区域宽度
            target_width = rect_width - 40  # 左右各留20像素边距

            # 计算等比例缩放后的高度
            aspect_ratio = title_img.height / title_img.width
            target_height = int(target_width * aspect_ratio)

            # 调整图片大小
            resized_img = title_img.resize((int(target_width), target_height), Image.Resampling.LANCZOS)

            # 添加圆角
            rounded_img = round_corner_image(resized_img, radius=20)  # 可以调整圆角半径

            # 计算居中位置（水平方向）
            x = rect_x + 20  # 左边距20像素
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

    def reset(self):
        self.segments = []
        self.current_section = None  # 当前处理的段落类型
        self.in_code_block = False   # 是否在代码块内
        self.in_quote_block = False  # 是否在引用块内
        self.quote_indent = 0        # 引用块缩进级别

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
                        code_content.append(lines[i])
                        i += 1
                    
                    if i < len(lines):  # 找到了结束标记
                        code_text = '\n'.join(code_content)
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
                        # 没找到结束标记，作为普通文本处理
                        style = TextStyle(font_name='regular', indent=0)
                        segments.append(TextSegment(text=line, style=style))
                else:
                    # 结束代码块
                    self.in_code_block = False
                i += 1
                continue
                
            # 处理引用块
            if line.startswith('> '):
                quote_level = 0
                while line.startswith('> '):
                    quote_level += 1
                    line = line[2:]
                
                self.in_quote_block = True
                self.quote_indent = quote_level * 20
                
                # 处理引用块内部的文本
                quote_style = TextStyle(
                    font_name='regular',
                    indent=40 + self.quote_indent,
                    line_spacing=15,
                    is_quote=True  # 标记为引用样式
                )
                
                # 应用引用内部的Markdown格式
                processed_line = self.process_inline_formats(line.strip())
                segments.append(TextSegment(
                    text=processed_line,
                    style=quote_style,
                    original_text=lines[i]
                ))
            else:
                # 重置引用块状态
                if self.in_quote_block:
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
                    if i < len(lines) - 1:
                        has_next_content = False
                        for next_line in lines[i + 1:]:
                            if next_line.strip():
                                has_next_content = True
                                break
                        if has_next_content:
                            style = line_segments[-1].style
                            segments.append(TextSegment(text='', style=TextStyle(line_spacing=style.line_spacing)))
            
            i += 1

        # 最后添加签名，不添加任何额外空行
        if segments:
            try:
                from config import config
                signature_text = config.SIGNATURE_TEXT
            except (ImportError, AttributeError):
                signature_text = "—By 飞天"
                
            signature = TextSegment(
                text=signature_text,
                style=TextStyle(
                    font_name='regular', 
                    indent=0, 
                    line_spacing=0,
                    alignment='right'  # 添加右对齐属性
                )
            )
            segments.append(signature)

        return segments

    def is_category_title(self, text: str) -> bool:
        """判断是否为分类标题"""
        return text.strip() in ['国内要闻', '国际动态']

    def process_inline_formats(self, text: str) -> str:
        """处理行内Markdown格式"""
        # 完全替换所有Markdown格式标记，不保留原始标记
        
        # 处理标题格式 *一、标题*
        header_match = self.header_pattern.match(text)
        if header_match:
            return header_match.group(2)  # 只保留标题内容
            
        # 处理列表项标记 * 列表项
        list_match = self.list_star_pattern.match(text)
        if list_match:
            return "• " + list_match.group(1)  # 将星号替换为实际的圆点符号
        
        # 处理链接 [text](url)
        text = self.link_pattern.sub(r'\1', text)
        
        # 处理加粗 **text**
        text = self.bold_pattern.sub(r'\1', text)
        
        # 处理斜体 *text* 或 _text_
        text = self.italic_pattern.sub(lambda m: m.group(1) or m.group(2), text)
        
        # 处理行内代码 `code`
        text = self.code_pattern.sub(r'\1', text)
        
        # 处理删除线 ~~text~~
        text = self.strikethrough_pattern.sub(r'\1', text)
        
        return text

    def process_title_marks(self, text: str) -> str:
        """处理标题标记"""
        # 应用所有行内格式处理
        return self.process_inline_formats(text)

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

        # 处理水平分割线: --- 或 ***
        if re.match(r'^(\-{3,}|\*{3,})$', text.strip()):
            style = TextStyle(
                line_spacing=30,  # 分割线前后增加间距
                is_horizontal_rule=True
            )
            return [TextSegment(text='', style=style)]

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
                    indent=0
                )
            else:
                style = TextStyle(
                    font_name='bold',
                    font_size=35,
                    is_title=True,
                    line_spacing=20,
                    indent=0
                )
            return [TextSegment(text=title_text, style=style)]

        # 处理一级标题
        if text.startswith('# '):
            style = TextStyle(
                font_name='bold',
                font_size=40,
                is_title=True,
                indent=0
            )
            return [TextSegment(text=self.process_inline_formats(text[2:].strip()), style=style)]

        # 处理二级标题
        if text.startswith('## '):
            style = TextStyle(
                font_name='bold',
                font_size=35,
                is_title=True,
                line_spacing=25,
                indent=0
            )
            self.current_section = self.process_inline_formats(text[3:].strip())
            return [TextSegment(text=self.current_section, style=style)]

        # 处理三级标题
        if text.startswith('### '):
            style = TextStyle(
                font_name='bold',
                font_size=32,
                is_title=True,
                line_spacing=20,
                indent=0
            )
            return [TextSegment(text=self.process_inline_formats(text[4:].strip()), style=style)]

        # 处理分类标题
        if self.is_category_title(text):
            style = TextStyle(
                font_name='bold',
                font_size=35,
                is_category=True,
                line_spacing=25,
                indent=0
            )
            return [TextSegment(text=text.strip(), style=style)]

        # 处理emoji标题格式
        if text.strip() and emoji.is_emoji(text[0]):
            # 移除文本中的加粗标记 **
            content = text.strip()
            content = self.process_inline_formats(content)

            style = TextStyle(
                font_name='bold',
                font_size=40,  # 使用H1的字体大小
                is_title=True,
                line_spacing=25,
                indent=0
            )
            return [TextSegment(text=content, style=style)]

        # 处理任务列表项
        task_match = re.match(r'^(\-|\*|\+)\s+\[([ xX])\]\s+(.+)$', text)
        if task_match:
            marker = task_match.group(1)
            is_checked = task_match.group(2).lower() == 'x'
            task_content = task_match.group(3).strip()
            task_content = self.process_inline_formats(task_content)
            
            style = TextStyle(
                font_name='regular',
                indent=40,
                line_spacing=15,
                is_task_list=True,
                task_checked=is_checked
            )
            # 将完整任务项文本传递给渲染器
            return [TextSegment(text=task_content, style=style)]

        # 增强处理无序列表项
        list_match = re.match(r'^(\*|\-|\+)\s+(.+)$', text)
        if list_match:
            marker = "•"  # 使用实际的圆点符号
            list_content = list_match.group(2).strip()
            list_content = self.process_inline_formats(list_content)
            
            style = TextStyle(
                font_name='regular',
                indent=40,
                line_spacing=15,
                is_list_item=True
            )
            return [TextSegment(text=f"{marker} {list_content}", style=style)]

        # 处理有序列表项 - 增强识别和渲染
        ordered_list_match = re.match(r'^(\d+)\.[ \t]+(.+)$', text)
        if ordered_list_match:
            number = ordered_list_match.group(1)
            content = ordered_list_match.group(2).strip()
            content = self.process_inline_formats(content)
            
            style = TextStyle(
                font_name='regular',
                indent=40,
                line_spacing=15,
                is_ordered_list=True
            )
            # 保留数字前缀，确保正确渲染
            return [TextSegment(text=f"{number}. {content}", style=style)]

        # 处理带序号的新闻条目
        number, content = self.split_number_and_content(text)
        if number:
            content = self.process_title_marks(content)
            title, body = self.split_title_and_content(content)
            segments = []

            title_style = TextStyle(
                font_name='bold',
                indent=0,
                is_title=True,
                line_spacing=15 if body else 20
            )
            segments.append(TextSegment(
                text=f"{number}. {title}",
                style=title_style
            ))

            if body:
                content_style = TextStyle(
                    font_name='regular',
                    indent=40,
                    line_spacing=20
                )
                segments.append(TextSegment(
                    text=body,
                    style=content_style
                ))
            return segments

        # 处理破折号开头的内容
        if text.strip().startswith('-'):
            style = TextStyle(
                font_name='regular',
                indent=40,
                line_spacing=15
            )
            return [TextSegment(text=self.process_inline_formats(text.strip()), style=style)]

        # 处理普通文本，应用行内格式
        style = TextStyle(
            font_name='regular',
            indent=40 if self.current_section else 0,
            line_spacing=15
        )

        return [TextSegment(text=self.process_inline_formats(text.strip()), style=style)]


class TextRenderer:
    """文本渲染器"""

    def __init__(self, font_manager: FontManager, max_width: int):
        self.font_manager = font_manager
        self.max_width = max_width
        self.temp_image = Image.new('RGBA', (2000, 100))
        self.temp_draw = ImageDraw.Draw(self.temp_image)

    def draw_horizontal_rule(self, draw: ImageDraw.ImageDraw, rect_x: int, current_y: int, rect_width: int, is_dark_theme: bool = False) -> int:
        """绘制水平分割线，返回增加的高度"""
        hr_y = current_y + 10  # 距顶部10像素
        hr_width = rect_width - 80  # 左右各留40像素边距
        hr_color = (180, 180, 180, 150) if not is_dark_theme else (100, 100, 100, 150)  # 半透明灰色
        
        # 绘制分割线
        draw.line(
            [(rect_x + 40, hr_y), (rect_x + hr_width + 40, hr_y)],
            fill=hr_color,
            width=2
        )
        
        return 20  # 返回分割线占用的高度

    def draw_task_list_item(self, draw: ImageDraw.ImageDraw, background: Image.Image, pos: Tuple[int, int], 
                           text: str, font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont,
                           fill: str, style: TextStyle) -> int:
        """绘制任务列表项，返回绘制宽度"""
        x, y = pos
        
        # 绘制复选框
        box_size = min(20, font.size - 4)  # 复选框大小，略小于字体大小
        box_y = y + (font.size - box_size) // 2
        
        # 绘制方框
        box_color = (100, 100, 100, 200) if style.is_dark_theme else (80, 80, 80, 200)
        draw.rectangle(
            [(x, box_y), (x + box_size, box_y + box_size)],
            outline=box_color,
            width=2
        )
        
        # 如果已勾选，绘制勾号
        if style.task_checked:
            # 绘制勾号
            check_color = (50, 200, 100, 220)  # 绿色勾号
            # 绘制勾号的三个点
            p1 = (x + box_size * 0.2, box_y + box_size * 0.5)
            p2 = (x + box_size * 0.4, box_y + box_size * 0.7)
            p3 = (x + box_size * 0.8, box_y + box_size * 0.3)
            draw.line([p1, p2, p3], fill=check_color, width=2)
        
        # 绘制任务文本，位置在复选框右侧
        text_x = x + box_size + 10  # 文本距离复选框10像素
        return self.draw_text_with_emoji(draw, (text_x, y), text, font, emoji_font, fill, style) + box_size + 10

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
        
        # 为代码块和引用块添加背景
        if style and (style.is_code or style.is_quote):
            # 先测量整行文本宽度
            text_width, text_height = self.measure_text(text, font, emoji_font)
            
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
                draw.rectangle(
                    [(x-15, y-5), (x-10, y + text_height + 5)],
                    fill=quote_color
                )
                # 引用块背景
                quote_bg_color = (70, 70, 70, 40) if style.is_dark_theme else (240, 240, 255, 70)
                draw.rounded_rectangle(
                    [(x-10, y-5), (x + text_width + 10, y + text_height + 5)], 
                    radius=5, 
                    fill=quote_bg_color
                )

        # 获取背景图像对象
        background = None
        for obj in [o for o in gc.get_objects() if isinstance(o, Image.Image)]:
            if obj.mode in ('RGBA', 'RGB') and obj.width > 100:
                background = obj
                break

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
            draw.text((x, y), marker, font=marker_font, fill=fill)
            marker_width = bbox[2] - bbox[0]
            
            # 绘制内容，缩进10像素
            for char in content:
                if emoji.is_emoji(char):
                    # 尝试使用Twemoji图片
                    if background:
                        emoji_img = get_local_emoji_image(char, size=style.font_size)
                        if emoji_img:
                            # 确保图像是RGBA模式
                            if emoji_img.mode != 'RGBA':
                                emoji_img = emoji_img.convert('RGBA')
                                
                            emoji_y = y + (style.font_size - emoji_img.height) // 2
                            
                            # 安全粘贴emoji图片
                            try:
                                background.paste(emoji_img, (x, emoji_y), emoji_img)
                            except ValueError as e:
                                print(f"粘贴emoji图片失败: {e}, 尝试不使用透明度掩码")
                                background.paste(emoji_img, (x, emoji_y))  # 不使用透明度掩码
                            
                            char_width = emoji_img.width
                        else:
                            # 如果图片获取失败，使用普通文本
                            bbox = draw.textbbox((x + marker_width + 10, y), char, font=emoji_font)
                            draw.text((x + marker_width + 10, y), char, font=emoji_font, fill=fill)
                            char_width = bbox[2] - bbox[0]
                    else:
                        # 如果没有背景，使用普通文本
                        bbox = draw.textbbox((x + marker_width + 10, y), char, font=emoji_font)
                        draw.text((x + marker_width + 10, y), char, font=emoji_font, fill=fill)
                        char_width = bbox[2] - bbox[0]
                else:
                    # 使用常规字体
                    bbox = draw.textbbox((x + marker_width + 10, y), char, font=font)
                    draw.text((x + marker_width + 10, y), char, font=font, fill=fill)
                    char_width = bbox[2] - bbox[0]
                
                x += char_width
                total_width += char_width
                
            # 添加列表标记和缩进的宽度
            total_width += marker_width + 10
            return total_width
        
        # 常规文本绘制
        for char in text:
            if emoji.is_emoji(char):
                # 尝试使用Twemoji图片
                if background:
                    emoji_img = get_local_emoji_image(char, size=font.size)
                    
                    # 如果无法获取图片，尝试创建文本版emoji
                    if emoji_img is None:
                        emoji_img = create_text_emoji(char, size=font.size)
                            
                    if emoji_img:
                        # 确保图像是RGBA模式
                        if emoji_img.mode != 'RGBA':
                            emoji_img = emoji_img.convert('RGBA')
                        
                        emoji_y = y + (font.size - emoji_img.height) // 2
                        
                        # 安全粘贴emoji图片
                        try:
                            background.paste(emoji_img, (x, emoji_y), emoji_img)
                        except ValueError as e:
                            print(f"粘贴emoji图片失败: {e}, 尝试不使用透明度掩码")
                            background.paste(emoji_img, (x, emoji_y))  # 不使用透明度掩码
                        
                        char_width = emoji_img.width
                    else:
                        # 如果获取图片失败，使用普通文本
                        bbox = draw.textbbox((x, y), char, font=emoji_font)
                        draw.text((x, y), char, font=emoji_font, fill=fill)
                        char_width = bbox[2] - bbox[0]
                else:
                    # 如果没有背景，使用普通文本
                    bbox = draw.textbbox((x, y), char, font=emoji_font)
                    draw.text((x, y), char, font=emoji_font, fill=fill)
                    char_width = bbox[2] - bbox[0]
            else:
                # 使用常规字体
                bbox = draw.textbbox((x, y), char, font=font)
                draw.text((x, y), char, font=font, fill=fill)
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
        if not segment.text.strip():
            return [ProcessedLine(text='', style=segment.style, height=0, line_count=1)]
            
        # 代码块特殊处理：保留原始换行
        if hasattr(segment.style, 'is_code') and segment.style.is_code:
            lines = segment.text.split('\n')
            processed_lines = []
            
            font = self.font_manager.get_font(segment.style)
            emoji_font = self.font_manager.fonts['emoji_30']
            
            for line in lines:
                _, height = self.measure_text(line, font, emoji_font)
                processed_lines.append(ProcessedLine(
                    text=line,
                    style=segment.style,
                    height=height,
                    line_count=1
                ))
            
            return processed_lines

        font = self.font_manager.get_font(segment.style)
        emoji_font = self.font_manager.fonts['emoji_30']
        words = []
        current_word = ''
        processed_lines = []

        # 分词处理
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
    """
    预处理输入文本，提取logo URL和内容文本
    
    返回:
        Tuple[Optional[str], str]: (logo URL或None, 内容文本)
    """
    # 尝试解析为JSON
    try:
        # 检查是否为JSON格式
        if input_text.strip().startswith('{') and input_text.strip().endswith('}'):
            data = json.loads(input_text)
            
            # 提取logo和内容
            logo_url = data.get('logo')
            content_text = data.get('content', '')
            
            # 替换HTML实体
            content_text = html.unescape(content_text)
            
            return logo_url, content_text
    except:
        # 如果不是有效的JSON或解析出错，返回原始文本
        pass
    
    return None, input_text


def generate_image(text: str, output_path: str, title_image: Optional[str] = None):
    """生成图片主函数 - 修复彩色emoji渲染"""
    try:
        # 预处理输入文本 - 处理logo和内容
        logo_url, text = preprocess_text(text)
        
        # 如果传入的title_image为None但从文本中解析出logo_url，则使用logo_url
        if title_image is None and logo_url:
            title_image = logo_url
        
        width = 720
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 打印当前目录用于调试
        print(f"当前目录: {current_dir}")
        print(f"当前目录文件列表: {[f for f in os.listdir(current_dir) if f.endswith(('.ttf', '.ttc'))]}")
        
        # 仍然使用现有的字体路径
        font_paths = {
            'regular': os.path.join(current_dir, "msyh.ttc"),
            'bold': os.path.join(current_dir, "msyhbd.ttc"),
            'emoji': os.path.join(current_dir, "msyh.ttc")  # 使用默认字体作为emoji字体
        }

        # 验证字体文件
        for font_type, path in font_paths.items():
            if not os.path.exists(path):
                print(f"字体文件不存在: {path}")
                raise FileNotFoundError(f"Font file not found: {path}")
                
        # 检查Pillow版本
        try:
            from PIL import __version__ as pillow_version
            print(f"Pillow版本: {pillow_version}")
        except Exception as e:
            print(f"检查Pillow版本失败: {e}")

        # 获取主题颜色 - 在解析文本前获取，用于传递给TextStyle
        background_color, text_color, is_dark_theme = get_theme_colors()
        
        # 初始化组件
        font_manager = FontManager(font_paths)
        rect_width = width - 80
        max_content_width = rect_width - 80
        parser = MarkdownParser()
        renderer = TextRenderer(font_manager, max_content_width)

        # 处理logo/title图片
        if title_image:
            try:
                # 检查是否为URL
                if isinstance(title_image, str) and title_image.startswith(('http://', 'https://')):
                    # 下载图片
                    title_img = download_image_with_timeout(title_image)
                    if title_img is None:
                        print(f"无法下载logo图片: {title_image}")
                        # 添加一个空行作为分隔
                        text = "\n\n" + text
                    else:
                        # 如果成功下载，使用临时文件
                        temp_logo_path = os.path.join(current_dir, "temp_logo.png")
                        title_img.save(temp_logo_path)
                        title_image = temp_logo_path
                        # 添加一个空行作为分隔
                        text = "\n\n" + text
                # 本地文件路径处理保持不变
            except Exception as e:
                print(f"处理logo图片时出错: {e}")
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

        # 逐字符绘制文本
        for i, line in enumerate(processed_lines):
            if not line.text.strip():
                if i < len(processed_lines) - 1 and any(l.text.strip() for l in processed_lines[i + 1:]):
                    current_y += line.style.line_spacing
                continue

            # 计算文本起始位置
            base_x = rect_x + 40
            
            # 处理水平分割线
            if hasattr(line.style, 'is_horizontal_rule') and line.style.is_horizontal_rule:
                # 绘制水平分割线
                current_y += renderer.draw_horizontal_rule(draw, rect_x, current_y, rect_width, is_dark_theme)
                continue
            
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
            
            # 为代码块和引用块添加背景
            if (hasattr(line.style, 'is_code') and line.style.is_code) or \
               (hasattr(line.style, 'is_quote') and line.style.is_quote):
                # 代码块和引用块背景在draw_text_with_emoji中处理
                renderer.draw_text_with_emoji(
                    draw, (x, current_y), line.text, 
                    font, emoji_font, text_color, line.style
                )
            elif hasattr(line.style, 'is_list_item') and line.style.is_list_item:
                # 列表项特殊处理
                renderer.draw_text_with_emoji(
                    draw, (x, current_y), line.text, 
                    font, emoji_font, text_color, line.style
                )
            elif hasattr(line.style, 'is_task_list') and line.style.is_task_list:
                # 任务列表特殊处理
                renderer.draw_task_list_item(
                    draw, background, (x, current_y), line.text,
                    font, emoji_font, text_color, line.style
                )
            elif hasattr(line.style, 'is_ordered_list') and line.style.is_ordered_list:
                # 有序列表特殊处理
                # 从文本中提取序号和内容
                parts = line.text.split('. ', 1)
                number = parts[0]
                content = parts[1] if len(parts) > 1 else ""
                
                # 绘制序号，用加粗字体
                number_font = font_manager.get_font(TextStyle(font_name='bold', font_size=font.size))
                number_text = f"{number}. "
                bbox = draw.textbbox((x, current_y), number_text, font=number_font)
                draw.text((x, current_y), number_text, font=number_font, fill=text_color)
                number_width = bbox[2] - bbox[0]
                
                # 绘制内容
                content_x = x + number_width + 5  # 内容距离序号5像素
                renderer.draw_text_with_emoji(
                    draw, (content_x, current_y), content,
                    font, emoji_font, text_color, line.style
                )
            else:
                # 常规文本逐字符渲染
                current_x = x
                for char in line.text:
                    if emoji.is_emoji(char):
                        # 使用Twemoji图片渲染emoji
                        emoji_size = line.style.font_size
                        emoji_img = get_local_emoji_image(char, size=emoji_size)
                        
                        # 如果无法获取图片，尝试创建文本版emoji
                        if emoji_img is None:
                            emoji_img = create_text_emoji(char, size=emoji_size)
                            
                        if emoji_img:
                            # 确保图像是RGBA模式
                            if emoji_img.mode != 'RGBA':
                                emoji_img = emoji_img.convert('RGBA')
                                
                            # 计算垂直居中位置
                            emoji_y = current_y + (emoji_size - emoji_img.height) // 2
                            
                            # 安全粘贴emoji图片
                            try:
                                background.paste(emoji_img, (current_x, emoji_y), emoji_img)
                            except ValueError as e:
                                print(f"粘贴emoji图片失败: {e}, 尝试不使用透明度掩码")
                                background.paste(emoji_img, (current_x, emoji_y))  # 不使用透明度掩码
                            
                            # 更新位置
                            current_x += emoji_img.width
                        else:
                            # 如果获取图片失败，使用普通文本
                            emoji_font = font_manager.fonts['emoji_30']
                            bbox = draw.textbbox((current_x, current_y), char, font=emoji_font)
                            draw.text((current_x, current_y), char, font=emoji_font, fill=text_color)
                            current_x += bbox[2] - bbox[0]
                    else:
                        # 普通文字渲染
                        font = font_manager.get_font(line.style)
                        bbox = draw.textbbox((current_x, current_y), char, font=font)
                        draw.text((current_x, current_y), char, font=font, fill=text_color)
                        current_x += bbox[2] - bbox[0]

            if i < len(processed_lines) - 1:
                current_y += line.height + line.style.line_spacing
            else:
                current_y += line.height

        # 直接保存为PNG，保持RGBA模式
        try:
            # 测试RGBA模式保存
            background.save(output_path, "PNG", optimize=False, compress_level=0)
            print(f"已保存图片(RGBA): {output_path}")
        except Exception as e:
            print(f"RGBA保存失败: {e}")
            try:
                # 备用方案：转换为RGB模式再保存
                background = background.convert('RGB')
                background.save(output_path, "PNG", optimize=False, compress_level=0)
                print(f"已保存图片(RGB): {output_path}")
            except Exception as e2:
                print(f"RGB保存也失败: {e2}")
                raise

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
                    return Image.open(BytesIO(response.content))  # 使用正确导入的BytesIO
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
