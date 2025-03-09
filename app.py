"""
Text2Card API Server
提供符合 OpenAI API 格式的文字转图片卡片服务

主要功能：
1. 文字转卡片图片生成
2. 安全的URL token认证
3. 图片存储和服务
4. 环境配置管理

API 端点：
- POST /v1/chat/completions: 生成图片卡片
- GET /v1/images/<filename>: 获取生成的图片

使用方法：
    curl -X POST http://localhost:3000/v1/chat/completions \
        -H "Authorization: Bearer your-api-key" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "Text2Card",
            "messages": [{"role": "user", "content": "要转换的文本内容"}]
        }'
"""

from flask import Flask, request, jsonify, send_file, make_response, Response
from flask_cors import CORS
from functools import wraps
import os
from datetime import datetime
import uuid
import time
import logging
from typing import Optional, Dict, Any, Tuple
import re
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from werkzeug.middleware.proxy_fix import ProxyFix
import gc
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
import argparse
import importlib
import threading

# 导入配置
from config import config

# 初始化日志
config.setup_logging()
logger = logging.getLogger(__name__)

# 初始化调度器
scheduler = BackgroundScheduler()

def generate_unique_filename() -> str:
    """
    生成唯一的文件名
    使用时间戳和UUID组合确保唯一性

    Returns:
        str: 格式为 'YYYYMMDDHHMMSS_UUID.png' 的文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex
    return f"{timestamp}_{unique_id}.png"

def create_error_response(message: str, error_type: str, status_code: int) -> Tuple[Dict[str, Any], int]:
    """
    创建标准化的错误响应

    Args:
        message: 错误消息
        error_type: 错误类型
        status_code: HTTP状态码

    Returns:
        tuple: (错误响应字典, 状态码)
    """
    return {
        'error': {
            'message': message,
            'type': error_type
        }
    }, status_code

def require_api_key(f):
    """
    API密钥验证装饰器
    验证请求头中的Authorization字段

    Args:
        f: 被装饰的函数
    Returns:
        函数: 包装后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid API key format")
            return make_response(
                jsonify(create_error_response(
                    '缺少或无效的 API key',
                    'authentication_error',
                    401
                ))
            )

        api_key = auth_header.split(' ')[1]

        if api_key not in config.API_KEYS:
            logger.warning(f"Invalid API key attempted: {api_key[:6]}...")
            return make_response(
                jsonify(create_error_response(
                    '无效的 API key',
                    'authentication_error',
                    401
                ))
            )

        return f(*args, **kwargs)
    return decorated

def validate_chat_request(data: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], int]]:
    """
    验证聊天请求数据

    Args:
        data: 请求数据字典

    Returns:
        Optional[tuple]: 如果验证失败返回错误响应，否则返回None
    """
    if not data:
        return create_error_response('缺少请求数据', 'invalid_request_error', 400)

    if 'model' not in data or data['model'] != 'Text2Card':
        return create_error_response(
            '无效的模型指定。请使用 model: Text2Card',
            'invalid_request_error',
            400
        )

    if 'messages' not in data or not data['messages']:
        return create_error_response('需要提供消息数组', 'invalid_request_error', 400)

    return None

def cleanup_old_images():
    """
    清理过期的图片文件
    """
    try:
        current_time = time.time()
        cleanup_count = 0
        for filename in os.listdir(config.UPLOAD_FOLDER):
            try:
                file_path = os.path.join(config.UPLOAD_FOLDER, filename)
                # 如果文件超过24小时未被访问
                if os.path.exists(file_path) and \
                   current_time - os.path.getmtime(file_path) > 86400:
                    os.remove(file_path)
                    cleanup_count += 1
                    if cleanup_count % 100 == 0:  # 每清理100个文件记录一次日志
                        logger.info(f"Cleaned up {cleanup_count} old images")
            except Exception as e:
                logger.error(f"Error cleaning up image {filename}: {str(e)}")
                continue
        if cleanup_count > 0:
            logger.info(f"Cleanup completed: removed {cleanup_count} old images")
        gc.collect()  # 手动触发垃圾回收
    except Exception as e:
        logger.error(f"Error in cleanup_old_images: {str(e)}")

# 配置定时任务
scheduler.add_job(func=cleanup_old_images, trigger="interval", hours=1)
scheduler.start()

# 确保在应用退出时关闭调度器
atexit.register(lambda: scheduler.shutdown())

# 初始化Flask应用
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # 修复代理问题
CORS(app)  # 启用跨域支持
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# 添加请求限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.after_request
def after_request(response):
    """请求完成后的清理工作"""
    gc.collect()  # 手动触发垃圾回收
    return response

@app.route('/v1/chat/completions', methods=['POST'])
@require_api_key
@limiter.limit("10 per minute")  # 添加速率限制
def chat_completions():
    """
    OpenAI兼容的聊天补全API端点
    接收文本内容并生成对应的图片卡片

    Expected Request:
    {
        "model": "Text2Card",
        "messages": [
            {"role": "user", "content": "要转换的文本内容"}
        ]
    }

    Returns:
        JSON响应: 包含生成的图片URL或错误信息
    """
    try:
        # 限制请求体大小
        if request.content_length and request.content_length > config.MAX_CONTENT_LENGTH:
            return jsonify(create_error_response(
                '请求数据过大',
                'payload_too_large',
                413
            ))
            
        data = request.json
        
        # 验证请求数据
        validation_error = validate_chat_request(data)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]

        # 提取最后一条用户消息
        last_message = None
        title_image = None
        for msg in reversed(data['messages']):
            if msg.get('role') == 'user':
                last_message = msg.get('content')
                title_image = msg.get('title_image')  # 提取title_image参数
                break

        if not last_message:
            return jsonify(create_error_response(
                '未找到有效的用户消息',
                'invalid_request_error',
                400
            ))
        
        # 检查是否使用了分隔符"|LOGO|"来分割logo和正文
        logo_separator = "|LOGO|"
        if logo_separator in last_message and not title_image:
            parts = last_message.split(logo_separator, 1)
            if len(parts) == 2:
                logo_url = parts[0].strip()
                remaining_text = parts[1].strip()
                
                # 如果剩余内容为空，使用默认文本
                if not remaining_text:
                    remaining_text = "图片卡片"
                    
                # 更新参数
                title_image = logo_url
                last_message = remaining_text
        
        # 如果没有使用分隔符，则检查文本内容开头是否为图片URL（向后兼容）
        elif not title_image:
            url_pattern = r'^(https?://\S+\.(jpg|jpeg|png|gif|webp))(.*)$'
            match = re.match(url_pattern, last_message, re.IGNORECASE | re.DOTALL)
            
            if match:
                # 如果消息内容以图片URL开头且没有设置title_image，则将其作为logo
                logo_url = match.group(1)
                remaining_text = match.group(3).strip()
                
                # 如果剩余内容为空，使用默认文本
                if not remaining_text:
                    remaining_text = "图片卡片"
                    
                # 更新参数
                title_image = logo_url
                last_message = remaining_text
        
        # 处理转义字符
        # 1. 处理文本中的转义序列
        last_message = last_message.replace('\\n', '\n')
        last_message = last_message.replace('\\t', '\t')
        last_message = last_message.replace('\\r', '\r')
        
        # 2. 处理特殊的文本标记
        last_message = last_message.replace('!~!', '\n')
        
        # 生成图片
        output_filename = generate_unique_filename()
        output_path = os.path.join(config.UPLOAD_FOLDER, output_filename)

        # 调用图片生成函数
        from image_generator import generate_image
        generate_image(last_message, output_path, title_image)  # 传入title_image参数

        # 验证图片生成是否成功
        if not os.path.exists(output_path):
            logger.error(f"Failed to generate image: {output_path}")
            return jsonify(create_error_response(
                '图片生成失败',
                'server_error',
                500
            ))

        # 生成带token的图片URL
        token, expiry = config.generate_image_token(output_filename)
        image_url = f"{config.base_url}/v1/images/{output_filename}?token={token}&expiry={expiry}"

        # 将URL转换为Markdown格式
        markdown_image_url = f"![图片卡片]({image_url})"

        # 检查客户端对响应格式的需求 - 标准OpenAI参数
        response_format = data.get('response_format', {}).get('type', 'text')
        
        # 选择响应内容 - 根据标准OpenAI格式
        # 在流式模式中，由于大多数客户端已经处理流式内容，我们保持简单文本返回
        # 但我们会支持response_format参数
        if response_format == 'json_object':
            # 如果客户端要求JSON响应，我们返回一个包含URL的JSON结构
            content = json.dumps({"url": image_url, "markdown": markdown_image_url})
        else:
            # 默认使用Markdown格式，这在大多数支持OpenAI的客户端中都能正常工作
            content = markdown_image_url

        # 记录详细的日志
        logger.info(f"Successfully generated image: {output_filename}")
        logger.info(f"Image URL: {image_url}")
        logger.info(f"Response format: {response_format}")
        logger.info(f"Content being returned: {content}")

        # 检查是否请求了流式响应 - 标准OpenAI参数
        stream = data.get('stream', False)
        logger.info(f"Stream mode requested: {stream}")

        if stream:
            def generate():
                try:
                    # 首先发送角色
                    chunk = {
                        "id": f"text2card-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "Text2Card",
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant"
                            },
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                    # 然后发送内容
                    chunk = {
                        "id": f"text2card-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "Text2Card",
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": content
                            },
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                    # 然后发送一个完成标记
                    chunk = {
                        "id": f"text2card-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "Text2Card",
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                    # 最后发送 [DONE] 标记
                    yield "data: [DONE]\n\n"
                except GeneratorExit:
                    # 处理客户端断开连接
                    logger.info("Client disconnected from stream")
                finally:
                    # 清理资源
                    gc.collect()
            
            return Response(
                generate(),
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
                }
            )
        else:
            # 构造OpenAI格式的响应 - 完整标准格式
            response = {
                'id': f'text2card-{int(time.time())}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'Text2Card',
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': content
                    },
                    'finish_reason': 'stop'
                }],
                'usage': {
                    'prompt_tokens': len(last_message),
                    'completion_tokens': len(str(content)),
                    'total_tokens': len(last_message) + len(str(content))
                }
            }

            logger.info(f"Full response: {json.dumps(response, ensure_ascii=False)}")

            # 直接使用Flask的Response构造响应
            return Response(
                json.dumps(response, ensure_ascii=False),
                status=200,
                headers={
                    "Content-Type": "application/json; charset=utf-8"
                }
            )

    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}", exc_info=True)
        return jsonify(create_error_response(
            f'服务器错误: {str(e)}',
            'server_error',
            500
        ))

@app.route('/v1/images/<filename>')
def serve_image(filename):
    """
    提供图片服务的端点，使用URL token验证

    Args:
        filename (str): 请求的图片文件名

    URL Parameters:
        token (str): 访问令牌
        expiry (str): 过期时间戳

    Returns:
        file: 图片文件或错误响应
    """
    try:
        # 获取URL参数
        token = request.args.get('token')
        expiry = request.args.get('expiry')

        # 验证参数
        if not token or not expiry:
            logger.warning(f"Missing token or expiry for image: {filename}")
            return jsonify(create_error_response(
                '缺少访问令牌',
                'authentication_error',
                401
            ))

        # 验证token
        if not config.verify_image_token(filename, token, expiry):
            logger.warning(f"Invalid or expired token for image: {filename}")
            return jsonify(create_error_response(
                '无效或过期的访问令牌',
                'authentication_error',
                401
            ))

        # 提供图片
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            logger.error(f"Image file not found: {file_path}")
            return jsonify(create_error_response(
                '图片文件不存在',
                'not_found_error',
                404
            ))

        return send_file(file_path, mimetype='image/png')

    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return jsonify(create_error_response(
            '图片未找到或访问出错',
            'not_found_error',
            404
        ))

@app.errorhandler(413)
def request_entity_too_large(error):
    """处理请求体过大的错误"""
    return jsonify(create_error_response(
        '请求数据过大',
        'payload_too_large',
        413
    ))

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify(create_error_response(
        '请求的资源不存在',
        'not_found_error',
        404
    ))

@app.errorhandler(500)
def internal_server_error(error):
    """处理500错误"""
    return jsonify(create_error_response(
        '服务器内部错误',
        'server_error',
        500
    ))

def watch_files_for_changes(watched_files=None, check_interval=1, exclude_patterns=None):
    """
    监控Python文件变化并在变化时重新加载应用
    
    Args:
        watched_files: 要监控的文件列表，如果为None则监控所有py文件
        check_interval: 检查间隔时间（秒）
        exclude_patterns: 要排除的文件匹配模式列表
    """
    if watched_files is None:
        # 默认监控当前目录下所有.py文件
        watched_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', '.git', '.venv', 'venv']
    
    # 记录文件最后修改时间
    file_mtimes = {}
    for file_path in watched_files:
        try:
            file_mtimes[file_path] = os.path.getmtime(file_path)
        except OSError:
            file_mtimes[file_path] = 0
    
    logging.info(f"文件监控已启动，监控文件: {', '.join(watched_files)}")
    
    def check_files():
        while True:
            # 检查文件是否有变化
            for file_path in watched_files:
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime > file_mtimes[file_path]:
                        logging.info(f"检测到文件变化: {file_path}")
                        file_mtimes[file_path] = mtime
                        
                        # 重新加载已导入的模块
                        module_name = os.path.splitext(file_path)[0]
                        if module_name in sys.modules:
                            try:
                                importlib.reload(sys.modules[module_name])
                                logging.info(f"已重新加载模块: {module_name}")
                            except Exception as e:
                                logging.error(f"重新加载模块时出错: {e}")
                        
                        # 告知用户需要重启服务以应用所有更改
                        logging.warning("某些更改可能需要手动重启服务才能完全生效")
                except OSError:
                    continue
            
            time.sleep(check_interval)
    
    # 在后台线程中运行文件监控
    monitor_thread = threading.Thread(target=check_files, daemon=True)
    monitor_thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Text2Card API 服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听主机 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=3000, help='监听端口 (默认: 3000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--watch', action='store_true', help='监控文件变化并自动重载')
    args = parser.parse_args()
    
    # 配置日志
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)
    
    # 启动文件监控（如果启用）
    if args.watch:
        py_files = [f for f in os.listdir('.') if f.endswith('.py')]
        watch_files_for_changes(py_files)
    
    # 启动前清理旧文件
    cleanup_old_images()

    # 输出启动信息
    logger.info(f"Starting Text2Card API server")
    logger.info(f"Server URL: {config.base_url}")
    logger.info(f"Upload folder: {config.UPLOAD_FOLDER}")
    logger.info(f"Maximum content length: {config.MAX_CONTENT_LENGTH} bytes")

    # 启动服务器
    app.run(host=args.host, port=args.port)