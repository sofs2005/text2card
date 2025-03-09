#!/bin/bash
echo "正在启动Text2Card服务..."

# 检查是否已安装依赖
if ! pip show flask &>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动服务器
python api_server.py

echo "服务已关闭。" 