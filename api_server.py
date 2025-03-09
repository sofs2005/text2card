import os
import time
import uuid
import re
import json
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends, Header
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import secrets
import socket
from enhanced_renderer import render_markdown_to_image

# 获取服务器IP地址
def get_server_ip():
    """获取服务器IP地址"""
    try:
        # 获取本机的主机名
        host_name = socket.gethostname()
        # 获取本机IP
        host_ip = socket.gethostbyname(host_name)
        return host_ip
    except:
        return "127.0.0.1"  # 如果无法获取，返回默认值

# 配置
class Config:
    # 读取HOST环境变量，如果没有设置，使用服务器IP
    default_host = f"http://{get_server_ip()}:3000"
    HOST = os.environ.get('HOST', default_host)
    PORT = int(os.environ.get('PORT', 3000))
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(16))
    API_KEYS = json.loads(os.environ.get('API_KEYS', '["sk-test"]'))
    TOKEN_EXPIRY = int(os.environ.get('TOKEN_EXPIRY', 3600))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'picture')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))
    SIGNATURE_TEXT = os.environ.get('SIGNATURE_TEXT', '—By 飞天')

# 创建目录
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
# 创建临时目录
os.makedirs("temp_images", exist_ok=True)

app = FastAPI(
    title="Text2Card API服务",
    description="OpenAI兼容的Markdown卡片渲染API",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义OpenAI兼容的请求模型
class ChatMessage(BaseModel):
    role: str
    content: str
    title_image: Optional[str] = None
    name: Optional[str] = None

class ResponseFormat(BaseModel):
    type: str = "text"

class ChatRequest(BaseModel):
    model: str = "Text2Card"
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    response_format: Optional[ResponseFormat] = None

# 定义OpenAI兼容的响应模型
class ChatResponseMessage(BaseModel):
    role: str
    content: str

class ChatResponseChoice(BaseModel):
    index: int
    message: ChatResponseMessage
    finish_reason: str

class ChatResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatResponseChoice]
    usage: ChatResponseUsage

# 定义错误响应类
class ErrorResponse(BaseModel):
    error: Dict[str, Any]

# 定义简单的Markdown请求模型（用于/render端点）
class MarkdownRequest(BaseModel):
    markdown_text: str
    width: Optional[int] = 720
    height: Optional[int] = None
    filename: Optional[str] = None

# 错误处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 格式化为OpenAI兼容的错误响应
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": str(exc),
                "type": "invalid_request_error",
                "param": None,
                "code": "validation_error"
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 格式化为OpenAI兼容的错误响应
    error_type = "invalid_request_error"
    if exc.status_code == 401:
        error_type = "authentication_error"
    elif exc.status_code == 429:
        error_type = "rate_limit_error"
    elif exc.status_code >= 500:
        error_type = "server_error"
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": error_type,
                "param": None,
                "code": None
            }
        }
    )

# 辅助函数
def validate_api_key(api_key: str) -> bool:
    """验证API密钥"""
    print(f"尝试验证API密钥: {api_key}")
    print(f"配置的API密钥列表: {Config.API_KEYS}")
    
    # 如果API密钥列表为空，或包含空字符串，允许任何密钥
    if not Config.API_KEYS or "" in Config.API_KEYS or "sk-test" in Config.API_KEYS:
        print("API密钥列表为空或包含测试密钥，允许任何密钥")
        return True
    
    # 验证密钥是否在允许列表中
    result = api_key in Config.API_KEYS
    print(f"密钥验证结果: {result}")
    return result

def extract_image_url(text: str) -> Optional[str]:
    """从文本中提取图片URL"""
    url_pattern = r'(https?://\S+\.(jpg|jpeg|png|gif))'
    match = re.search(url_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None

def generate_token() -> tuple:
    """生成访问令牌"""
    token = secrets.token_urlsafe(16)
    expiry = int(time.time()) + Config.TOKEN_EXPIRY
    return token, expiry

def get_image_url(image_path: str, token: str, expiry: int) -> str:
    """生成图片访问URL"""
    filename = os.path.basename(image_path)
    url = f"{Config.HOST}/v1/images/{filename}?token={token}&expiry={expiry}"
    print(f"生成的图片URL: {url}")
    print(f"使用的HOST配置: {Config.HOST}")
    return url

def cleanup_old_images(max_age_seconds: int = 3600):
    """清理超过指定时间的临时图片"""
    current_time = time.time()
    for folder in [Config.UPLOAD_FOLDER, "temp_images"]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # 如果文件修改时间超过max_age_seconds，则删除
                if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > max_age_seconds:
                    os.remove(file_path)

async def check_auth_header(authorization: Optional[str] = Header(None)) -> str:
    """验证Authorization头并返回API密钥"""
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Missing Authorization header"
        )
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=401, 
            detail="Authorization header must start with 'Bearer'"
        )
    
    api_key = authorization[7:]
    
    # 如果是测试环境，直接允许通过
    if api_key == "sk-test":
        print("使用测试密钥，自动通过验证")
        return api_key
    
    if not validate_api_key(api_key):
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key"
        )
    
    return api_key

# OpenAI兼容的API路由
@app.post("/v1/chat/completions", response_model=Union[ChatResponse, ErrorResponse])
async def chat_completions(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    api_key: str = Depends(check_auth_header)
):
    """OpenAI兼容的聊天完成接口"""
    print("\n===== 新的API请求 =====")
    
    # 获取最后一条用户消息
    user_message = None
    for msg in reversed(request.messages):
        if msg.role == 'user':
            user_message = msg
            break
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # 提取文本内容
    content = user_message.content
    if not content:
        raise HTTPException(status_code=400, detail="Empty message content")
    
    # 提取标题图片URL
    title_image = user_message.title_image
    if not title_image:
        # 尝试从内容中提取图片URL
        url_match = extract_image_url(content)
        if url_match:
            title_image = url_match
            # 从内容中移除URL
            content = content.replace(url_match, '').strip()
    
    # 生成唯一文件名
    timestamp = time.strftime('%Y%m%d%H%M%S')
    random_id = uuid.uuid4().hex[:6]
    filename = f"{timestamp}_{random_id}.png"
    output_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    # 生成图片
    try:
        render_markdown_to_image(content, output_path, width=720)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
    
    # 生成访问令牌
    token, expiry = generate_token()
    image_url = get_image_url(output_path, token, expiry)
    
    # 添加清理任务
    background_tasks.add_task(cleanup_old_images)
    
    # 检查是否为流式响应
    if request.stream:
        def generate_stream():
            stream_id = f'text2card-{random_id}'
            created_time = int(time.time())
            
            # 第一个块：返回角色
            chunk1 = {
                'id': stream_id,
                'object': 'chat.completion.chunk',
                'created': created_time,
                'model': request.model,
                'choices': [{
                    'index': 0,
                    'delta': {'role': 'assistant'},
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(chunk1)}\n\n"
            
            # 确定响应内容（普通文本或JSON）
            content = f"![图片卡片]({image_url})"
            if (hasattr(request, 'response_format') and request.response_format and 
                hasattr(request.response_format, 'type') and request.response_format.type == 'json_object'):
                # JSON对象响应格式
                content_obj = {
                    'url': image_url,
                    'expires_at': expiry
                }
                content = json.dumps(content_obj)
            
            # 流式内容处理：将内容分成更小的块以模拟真实流式效果
            if len(content) > 30:
                # 分割长内容以模拟流式传输
                chunk_size = min(20, max(5, len(content) // 5))  # 动态chunk大小
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                
                # 发送内容块
                for text_chunk in chunks:
                    chunk = {
                        'id': stream_id,
                        'object': 'chat.completion.chunk',
                        'created': created_time,
                        'model': request.model,
                        'choices': [{
                            'index': 0,
                            'delta': {'content': text_chunk},
                            'finish_reason': None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    # 添加一点延迟以模拟真实流式传输
                    time.sleep(0.05)
            else:
                # 短内容直接发送
                chunk2 = {
                    'id': stream_id,
                    'object': 'chat.completion.chunk',
                    'created': created_time,
                    'model': request.model,
                    'choices': [{
                        'index': 0,
                        'delta': {'content': content},
                        'finish_reason': None
                    }]
                }
                yield f"data: {json.dumps(chunk2)}\n\n"
            
            # 最终块：表示完成
            chunk_final = {
                'id': stream_id,
                'object': 'chat.completion.chunk',
                'created': created_time,
                'model': request.model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(chunk_final)}\n\n"
            
            # 标准结束标记
            yield "data: [DONE]\n\n"
        
        # 设置正确的响应头
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }
        
        return StreamingResponse(
            generate_stream(), 
            media_type="text/event-stream",
            headers=headers
        )
    else:
        # 非流式响应
        message_content = f"![图片卡片]({image_url})"
        
        # 检查是否需要特定的响应格式
        if (hasattr(request, 'response_format') and request.response_format and 
            hasattr(request.response_format, 'type') and request.response_format.type == 'json_object'):
            # 以JSON对象格式返回
            message_content = json.dumps({
                'url': image_url,
                'expires_at': expiry
            })
        
        response = {
            'id': f'text2card-{random_id}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': request.model,
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': message_content
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(content),
                'completion_tokens': len(message_content),
                'total_tokens': len(content) + len(message_content)
            }
        }
        
        return response

@app.get("/v1/images/{filename}")
async def get_image(filename: str, token: str, expiry: str):
    """获取生成的图片"""
    if not token or not expiry:
        raise HTTPException(status_code=401, detail="Missing token or expiry")
    
    try:
        expiry_int = int(expiry)
        if expiry_int < int(time.time()):
            raise HTTPException(status_code=401, detail="Token expired")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expiry format")
    
    image_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path, media_type="image/png")

# 保留原有的/render端点，提供直接渲染Markdown的功能
@app.post("/render")
async def render_markdown(request: MarkdownRequest, background_tasks: BackgroundTasks):
    """
    将Markdown文本直接渲染为图片
    
    - **markdown_text**: Markdown格式的文本
    - **width**: 图片宽度(像素)
    - **height**: 图片高度(像素)，为None则自动计算
    - **filename**: 自定义文件名，不含扩展名
    
    返回渲染后的图片文件
    """
    try:
        # 生成唯一文件名或使用用户提供的文件名
        filename = request.filename or f"markdown_{uuid.uuid4().hex}"
        output_path = os.path.join("temp_images", f"{filename}.png")
        
        # 渲染Markdown到图片
        render_markdown_to_image(
            request.markdown_text, 
            output_path, 
            width=request.width, 
            height=request.height
        )
        
        # 添加清理任务
        background_tasks.add_task(cleanup_old_images)
        
        # 返回文件
        return FileResponse(
            output_path, 
            media_type="image/png", 
            filename=f"{filename}.png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")

# 兼容OpenAI的其他端点
@app.get("/v1/models")
async def list_models(api_key: str = Depends(check_auth_header)):
    """列出支持的模型 - OpenAI兼容接口"""
    return {
        "object": "list",
        "data": [
            {
                "id": "Text2Card",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "Text2Card",
                "permission": [],
                "root": "Text2Card",
                "parent": None
            }
        ]
    }

@app.get("/")
async def root():
    """API服务根路径，返回使用说明"""
    return {
        "message": "Text2Card API服务",
        "openai_compatible": "发送POST请求到/v1/chat/completions，遵循OpenAI Chat API格式",
        "direct_render": "发送POST请求到/render端点，包含markdown_text字段",
        "example": "curl -X POST -H 'Content-Type: application/json' -d '{\"markdown_text\":\"# 标题\\n内容\"}' http://localhost:3000/render --output image.png"
    }

# 启动服务
if __name__ == "__main__":
    import uvicorn
    
    print("\n===== 服务器配置信息 =====")
    print(f"HOST: {Config.HOST}")
    print(f"PORT: {Config.PORT}")
    print(f"API_KEYS: {Config.API_KEYS}")
    print(f"UPLOAD_FOLDER: {Config.UPLOAD_FOLDER}")
    print(f"SERVER IP: {get_server_ip()}")
    print("=========================\n")
    
    uvicorn.run("api_server:app", host="0.0.0.0", port=Config.PORT, reload=True) 