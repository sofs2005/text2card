from PIL import Image, ImageDraw, ImageFont
import os
import re
import emoji

# 辅助类和函数
class TextStyle:
    """文本样式定义"""
    def __init__(self, color='black', is_bold=False, is_italic=False):
        self.color = color
        self.is_bold = is_bold
        self.is_italic = is_italic

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
    # 尝试常见的中文字体路径
    potential_fonts = [
        # Windows 中文字体
        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf", # 黑体
        "C:/Windows/Fonts/simsun.ttc", # 宋体
        
        # 项目内的字体
        "./fonts/SourceHanSansCN-Regular.otf",
        "./fonts/NotoSansSC-Regular.otf",
    ]
    
    for font_path in potential_fonts:
        if os.path.exists(font_path):
            return font_path
    
    return None  # 如果找不到合适的字体，返回None

def load_fonts():
    """加载字体"""
    fonts = {}
    
    font_path = get_system_font()
    if font_path:
        # 使用找到的字体
        fonts['regular'] = ImageFont.truetype(font_path, size=30)
        fonts['bold'] = ImageFont.truetype(font_path, size=30)
        fonts['large'] = ImageFont.truetype(font_path, size=40)
        fonts['small'] = ImageFont.truetype(font_path, size=24)
    else:
        # 使用默认字体
        fonts['regular'] = ImageFont.load_default()
        fonts['bold'] = ImageFont.load_default()
        fonts['large'] = ImageFont.load_default()
        fonts['small'] = ImageFont.load_default()
    
    return fonts

def draw_text_with_color(draw, image, fonts, pos, text, color='black', is_bold=False, is_italic=False):
    """绘制带颜色的文本"""
    x, y = pos
    
    # 选择字体
    font = fonts['bold'] if is_bold else fonts['regular']
    
    # 绘制文本
    draw.text((x, y), text, fill=color, font=font)
    
    # 返回文本宽度
    return draw.textlength(text, font=font)

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
            break
    
    return segments

def split_text_to_paragraphs(text):
    """将文本分割为段落"""
    paragraphs = []
    
    # 按行分割
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 检查是否是标题
        if line.startswith('# '):
            paragraphs.append(('h1', line[2:]))
        elif line.startswith('## '):
            paragraphs.append(('h2', line[3:]))
        # 检查是否是表格开始
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and '-' in lines[i + 1]:
            # 收集表格行
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            i -= 1  # 回退一行，因为循环会再加1
            
            # 合并表格行
            paragraphs.append(('table', '\n'.join(table_lines)))
        # 普通段落
        else:
            paragraphs.append(('paragraph', line))
        
        i += 1
    
    return paragraphs

def generate_image(text, output_path):
    """生成图像"""
    width = 800
    height = 1000
    
    # 创建图像
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    fonts = load_fonts()
    
    # 分割文本为段落
    paragraphs = split_text_to_paragraphs(text)
    
    # 卡片边距
    margin = 40
    x = margin
    y = margin
    max_width = width - 2 * margin
    
    # 绘制段落
    for p_type, p_text in paragraphs:
        if p_type == 'h1':
            # 标题
            segments = parse_color_tags(p_text)
            
            for segment in segments:
                font = fonts['large']
                draw_text_with_color(
                    draw, image, fonts, (x, y), 
                    segment.text, 
                    segment.style.color, 
                    True
                )
            
            y += 50  # 标题后增加间距
        elif p_type == 'h2':
            # 二级标题
            segments = parse_color_tags(p_text)
            
            for segment in segments:
                font = fonts['bold']
                draw_text_with_color(
                    draw, image, fonts, (x, y), 
                    segment.text, 
                    segment.style.color, 
                    True
                )
            
            y += 40  # 标题后增加间距
        elif p_type == 'table':
            # 表格处理 - 简单版本
            rows = p_text.split('\n')
            row_height = 40
            for row in rows:
                cells = row.split('|')
                cell_x = x
                
                for cell in cells:
                    cell = cell.strip()
                    if cell:
                        # 解析单元格中的颜色标签
                        segments = parse_color_tags(cell)
                        
                        for segment in segments:
                            draw_text_with_color(
                                draw, image, fonts, (cell_x, y), 
                                segment.text, 
                                segment.style.color, 
                                segment.style.is_bold
                            )
                        
                        cell_x += 150  # 简单的固定列宽
                
                y += row_height
        else:
            # 普通段落
            segments = parse_color_tags(p_text)
            
            line_height = 40
            line_x = x
            
            for segment in segments:
                # 绘制文本
                draw_text_with_color(
                    draw, image, fonts, (line_x, y), 
                    segment.text, 
                    segment.style.color, 
                    segment.style.is_bold,
                    segment.style.is_italic
                )
                
                line_x += draw.textlength(segment.text, font=fonts['regular']) + 5
            
            y += line_height
    
    # 保存图像
    image.save(output_path)
    print(f"图片已保存到: {output_path}")
    return image

# 测试函数
def test_color_renderer():
    """测试颜色渲染器"""
    text = """# 颜色测试

<span style="color:red">红色文本</span> <span style="color:blue">蓝色文本</span>
<span style="color:green">绿色文本</span> <span style="color:purple">紫色文本</span>

表格测试:

| 项目 | 描述 | 价格 |
|------|------|------|
| 商品A | <span style="color:red">非常棒的商品</span> | ¥199 |
| 商品B | <span style="color:green">打折商品!</span> | ¥49 |

—By 飞天
"""
    
    output_path = "simple_renderer_test.png"
    generate_image(text, output_path)

if __name__ == "__main__":
    test_color_renderer() 