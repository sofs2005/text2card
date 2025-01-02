"""
Configuration Management Module
处理应用程序的配置管理，包括环境变量加载、验证和访问
"""

import os
import json
from typing import List, Optional
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import logging
from pathlib import Path

# 加载环境变量
load_dotenv()

class ConfigurationError(Exception):
    """配置错误异常类"""
    pass

class Config:
    """
    应用配置类
    处理配置加载、验证和访问的核心类
    """

    def __init__(self):
        """初始化配置，加载和验证所有必需的配置值"""
        # 环境配置
        self.ENV: str = self._get_env('ENV', 'development')
        self.DEVELOPMENT_HOST: str = self._get_env('DEVELOPMENT_HOST', 'http://127.0.0.1:3000')
        self.PRODUCTION_HOST: str = self._get_env('PRODUCTION_HOST')
        self.PORT: int = int(self._get_env('PORT', '3000'))

        # 安全配置
        self.SECRET_KEY: str = self._get_env('SECRET_KEY')
        self.API_KEYS: List[str] = self._parse_json_env('API_KEYS', '[]')
        self.TOKEN_EXPIRY: int = int(self._get_env('TOKEN_EXPIRY', '3600'))

        # 存储配置
        self.UPLOAD_FOLDER: str = self._get_env('UPLOAD_FOLDER', 'picture')
        self.MAX_CONTENT_LENGTH: int = int(self._get_env('MAX_CONTENT_LENGTH', '10485760'))

        # 日志配置
        self.LOG_LEVEL: str = self._get_env('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT: str = self._get_env('LOG_FORMAT',
                                           '%(asctime)s - %(levelname)s - %(message)s')

        # 验证配置
        self._validate_configuration()

        # 确保上传目录存在
        self._ensure_upload_folder()

    def _get_env(self, key: str, default: Optional[str] = None) -> str:
        """
        获取环境变量值

        Args:
            key: 环境变量名
            default: 默认值（可选）

        Returns:
            str: 环境变量值

        Raises:
            ConfigurationError: 如果必需的环境变量未设置且没有默认值
        """
        value = os.getenv(key, default)
        if value is None:
            raise ConfigurationError(f"必需的环境变量 {key} 未设置")
        return value

    def _parse_json_env(self, key: str, default: str = '[]') -> List[str]:
        """
        解析JSON格式的环境变量

        Args:
            key: 环境变量名
            default: 默认JSON字符串

        Returns:
            List[str]: 解析后的列表
        """
        try:
            return json.loads(self._get_env(key, default))
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"环境变量 {key} JSON解析错误: {str(e)}")

    def _validate_configuration(self):
        """
        验证配置的有效性

        Raises:
            ConfigurationError: 当配置无效时
        """
        if not self.SECRET_KEY:
            raise ConfigurationError("SECRET_KEY 不能为空")

        if self.ENV not in ['development', 'production']:
            raise ConfigurationError("ENV 必须是 'development' 或 'production'")

        if self.ENV == 'production' and not self.PRODUCTION_HOST:
            raise ConfigurationError("生产环境需要设置 PRODUCTION_HOST")

    def _ensure_upload_folder(self):
        """确保上传目录存在"""
        Path(self.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

    @property
    def base_url(self) -> str:
        """
        获取当前环境的基础URL

        Returns:
            str: 完整的基础URL
        """
        return self.DEVELOPMENT_HOST if self.ENV == 'development' else self.PRODUCTION_HOST

    def generate_image_token(self, filename: str) -> tuple:
        """
        为图片URL生成安全的访问token

        Args:
            filename: 图片文件名

        Returns:
            tuple: (token, expiry) token和过期时间戳
        """
        timestamp = int(datetime.now().timestamp())
        expiry = timestamp + self.TOKEN_EXPIRY
        message = f"{filename}{expiry}{self.SECRET_KEY}"
        token = hashlib.sha256(message.encode()).hexdigest()[:32]
        return token, expiry

    def verify_image_token(self, filename: str, token: str, expiry: str) -> bool:
        """
        验证图片访问token是否有效

        Args:
            filename: 图片文件名
            token: 访问token
            expiry: 过期时间戳

        Returns:
            bool: token是否有效
        """
        try:
            if int(datetime.now().timestamp()) > int(expiry):
                return False
            expected_token = hashlib.sha256(
                f"{filename}{expiry}{self.SECRET_KEY}".encode()
            ).hexdigest()[:32]
            return token == expected_token
        except ValueError:
            return False

    def setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format=self.LOG_FORMAT
        )

# 创建全局配置实例
config = Config()