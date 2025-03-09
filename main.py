import os
import argparse
from pil_renderer import generate_image

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='将文本转换为卡片图片')
    parser.add_argument('--text', type=str, help='要转换的文本内容')
    parser.add_argument('--file', type=str, help='要转换的文本文件路径')
    parser.add_argument('--output', type=str, default='output.png', help='输出图片路径')
    
    args = parser.parse_args()
    
    # 获取文本内容
    text = ""
    if args.text:
        text = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return
    else:
        print("请提供文本内容 (--text) 或文本文件路径 (--file)")
        return
    
    # 确保输出目录存在
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成图片
    try:
        generate_image(text, args.output)
        print(f"已成功生成图片: {args.output}")
    except Exception as e:
        print(f"生成图片时出错: {e}")

if __name__ == "__main__":
    main() 