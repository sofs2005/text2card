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

from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from functools import wraps
import os
from datetime import datetime
import uuid
import time
import logging
from typing import Optional, Dict, Any, Tuple

# 导入配置
from config import config

# 初始化日志
config.setup_logging()
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

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

@app.route('/v1/chat/completions', methods=['POST'])
@require_api_key
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
                title_image = msg.get('title_image')  # 这里已经在提取 title_image 参数
                break

        if not last_message:
            return jsonify(create_error_response(
                '未找到有效的用户消息',
                'invalid_request_error',
                400
            ))

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

        # 构造OpenAI格式的响应
        response = {
            'id': f'text2card-{int(time.time())}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': 'Text2Card',
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': image_url
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(last_message),
                'completion_tokens': 0,
                'total_tokens': len(last_message)
            }
        }

        logger.info(f"Successfully generated image: {output_filename}")
        return jsonify(response)

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

def cleanup_old_images():
    """
    清理过期的图片文件
    """
    try:
        current_time = time.time()
        for filename in os.listdir(config.UPLOAD_FOLDER):
            file_path = os.path.join(config.UPLOAD_FOLDER, filename)
            # 如果文件超过24小时未被访问
            if os.path.exists(file_path) and \
               current_time - os.path.getmtime(file_path) > 86400:
                os.remove(file_path)
                logger.info(f"Cleaned up old image: {filename}")
    except Exception as e:
        logger.error(f"Error cleaning up old images: {str(e)}")

if __name__ == "__main__":
    # 启动前清理旧文件
    cleanup_old_images()

    # 输出启动信息
    logger.info(f"Starting Text2Card API server")
    logger.info(f"Server URL: {config.base_url}")
    logger.info(f"Upload folder: {config.UPLOAD_FOLDER}")
    logger.info(f"Maximum content length: {config.MAX_CONTENT_LENGTH} bytes")

    # 启动服务器
    app.run(
        debug=False,
        port=config.PORT,
        host='0.0.0.0'  # 默认监听所有网络接口
    )