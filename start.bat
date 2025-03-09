@echo off
echo 正在启动Text2Card服务...

:: 检查是否已安装依赖
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

:: 启动服务器
python api_server.py

echo 服务已关闭。 