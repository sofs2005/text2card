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


def add_title_image(background: Image.Image, title_image_path: str, rect_x: int, rect_y: int, rect_width: int) -> int:
    """添加标题图片"""
    try:
        # 判断是否为URL
        if title_image_path.startswith(('http://', 'https://')):
            # 从URL下载图像
            title_img = download_image_with_timeout(title_image_path)
            if title_img is None:
                print(f"无法加载标题图像: {title_image_path}")
                return rect_y + 30
        else:
            # 从本地文件加载
            title_img = Image.open(title_image_path)
        
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

    def reset(self):
        self.segments = []
        self.current_section = None  # 当前处理的段落类型

    def parse(self, text: str) -> List[TextSegment]:
        """解析整个文本"""
        self.reset()
        segments = []
        lines = text.splitlines()

        for i, line in enumerate(lines):
            line = line.strip()
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
                continue

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

        # 最后添加签名，不添加任何额外空行
        if segments:
            signature = TextSegment(
                text="                                         —By 嫣然",
                style=TextStyle(font_name='regular', indent=0, line_spacing=0)  # 设置 line_spacing=0
            )
            segments.append(signature)

        return segments

    def is_category_title(self, text: str) -> bool:
        """判断是否为分类标题"""
        return text.strip() in ['国内要闻', '国际动态']

    def process_title_marks(self, text: str) -> str:
        """处理标题标记"""
        # 移除 ** 标记
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        # 统一中文冒号
        text = text.replace(':', '：')
        return text

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

        # 处理一级标题
        if text.startswith('# '):
            style = TextStyle(
                font_name='bold',
                font_size=40,
                is_title=True,
                indent=0
            )
            return [TextSegment(text=text[2:].strip(), style=style)]

        # 处理二级标题
        if text.startswith('## '):
            style = TextStyle(
                font_name='bold',
                font_size=35,
                is_title=True,
                line_spacing=25,
                indent=0
            )
            self.current_section = text[3:].strip()
            return [TextSegment(text=self.current_section, style=style)]

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
            if '**' in content:
                content = content.replace('**', '')

            style = TextStyle(
                font_name='bold',
                font_size=40,  # 使用H1的字体大小
                is_title=True,
                line_spacing=25,
                indent=0
            )
            return [TextSegment(text=content, style=style)]

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
            return [TextSegment(text=text.strip(), style=style)]

        # 处理普通文本
        style = TextStyle(
            font_name='regular',
            indent=40 if self.current_section else 0,
            line_spacing=15
        )

        return [TextSegment(text=text.strip(), style=style)]


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
                             fill: str = "white") -> int:
        """绘制包含emoji的文本，返回绘制宽度"""
        x, y = pos
        total_width = 0

        for char in text:
            if emoji.is_emoji(char):
                # 使用emoji字体
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


def generate_image(text: str, output_path: str, title_image: Optional[str] = None):
    """生成图片主函数 - 修复彩色emoji渲染"""
    try:
        width = 720
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = {
            'regular': os.path.join(current_dir, "msyh.ttc"),
            'bold': os.path.join(current_dir, "msyhbd.ttc"),
            'emoji': os.path.join(current_dir, "TwitterColorEmoji.ttf")  # 或其他彩色emoji字体
        }

        # 验证字体文件
        for font_type, path in font_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Font file not found: {path}")

        # 初始化组件
        font_manager = FontManager(font_paths)
        rect_width = width - 80
        max_content_width = rect_width - 80
        parser = MarkdownParser()
        renderer = TextRenderer(font_manager, max_content_width)

        # 解析文本
        segments = parser.parse(text)
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
                # 判断是否为URL
                if title_image.startswith(('http://', 'https://')):
                    # 从URL下载图像
                    img = download_image_with_timeout(title_image)
                    if img is None:
                        print(f"无法加载标题图像预览: {title_image}")
                    else:
                        aspect_ratio = img.height / img.width
                        title_height = int((rect_width - 40) * aspect_ratio) + 40
                else:
                    # 从本地文件加载
                    with Image.open(title_image) as img:
                        aspect_ratio = img.height / img.width
                        title_height = int((rect_width - 40) * aspect_ratio) + 40
            except Exception as e:
                print(f"Title image processing error: {e}")

        content_height = renderer.calculate_height(processed_lines)
        rect_height = content_height + title_height
        rect_x = (width - rect_width) // 2
        rect_y = 40
        total_height = rect_height + 80

        # 创建RGBA背景
        background = create_gradient_background(width, total_height)
        draw = ImageDraw.Draw(background)

        # 获取主题颜色
        background_color, text_color, is_dark_theme = get_theme_colors()
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

            x = rect_x + 40 + line.style.indent
            current_x = x

            # 逐字符渲染
            for char in line.text:
                if emoji.is_emoji(char):
                    # emoji字体渲染
                    emoji_font = font_manager.fonts['emoji_30']
                    bbox = draw.textbbox((current_x, current_y), char, font=emoji_font)
                    # 使用RGBA模式绘制emoji
                    draw.text((current_x, current_y), char, font=emoji_font, embedded_color=True)
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
        background = background.convert('RGB')
        background.save(output_path, "PNG", optimize=False, compress_level=0)

    except Exception as e:
        print(f"Error generating image: {e}")
        raise
