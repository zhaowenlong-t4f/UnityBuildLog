"""文件处理器工厂实现。"""

import mimetypes
from pathlib import Path
from typing import Type, Dict, Optional

from .base import BaseFileHandler
from .text_handler import TextFileHandler
from .gzip_handler import GzipFileHandler
from ..exceptions import FileFormatError

class FileHandlerFactory:
    """文件处理器工厂。
    
    根据文件类型创建相应的文件处理器。支持：
    1. 文件类型自动检测
    2. 处理器注册机制
    3. 自定义处理器扩展
    """
    
    def __init__(self) -> None:
        """初始化工厂。"""
        self._handlers: Dict[str, Type[BaseFileHandler]] = {}
        self._file_types: Dict[str, str] = {}
        
        # 注册默认处理器
        self.register_handler("text", TextFileHandler, [".txt", ".log"])
        self.register_handler("gzip", GzipFileHandler, [".gz"])
        
    def register_handler(
        self,
        handler_type: str,
        handler_class: Type[BaseFileHandler],
        file_extensions: list[str]
    ) -> None:
        """注册新的文件处理器。

        Args:
            handler_type: 处理器类型标识
            handler_class: 处理器类
            file_extensions: 支持的文件扩展名列表

        Raises:
            ValueError: 参数无效
        """
        if not handler_type or not issubclass(handler_class, BaseFileHandler):
            raise ValueError("无效的处理器类型或类")
            
        self._handlers[handler_type] = handler_class
        for ext in file_extensions:
            if not ext.startswith('.'):
                ext = f".{ext}"
            self._file_types[ext.lower()] = handler_type
            
    def get_handler(
        self,
        file_path: Path,
        **kwargs
    ) -> BaseFileHandler:
        """获取适合的文件处理器。

        Args:
            file_path: 文件路径
            **kwargs: 传递给处理器的额外参数

        Returns:
            文件处理器实例

        Raises:
            FileFormatError: 不支持的文件类型
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
            
        # 获取文件类型
        ext = file_path.suffix.lower()
        handler_type = self._file_types.get(ext)
        
        if not handler_type:
            # 尝试通过MIME类型识别
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type == 'text/plain':
                handler_type = 'text'
            elif mime_type == 'application/gzip':
                handler_type = 'gzip'
            else:
                raise FileFormatError(f"不支持的文件类型：{ext}")
                
        handler_class = self._handlers[handler_type]
        return handler_class(file_path, **kwargs)
        
    @property
    def supported_extensions(self) -> list[str]:
        """获取支持的文件扩展名列表。

        Returns:
            支持的文件扩展名列表
        """
        return list(self._file_types.keys())
        
    @property
    def supported_handlers(self) -> list[str]:
        """获取支持的处理器类型列表。

        Returns:
            支持的处理器类型列表
        """
        return list(self._handlers.keys())