"""Unity 构建日志读取器

此模块负责处理 Unity 构建日志的读取操作，支持大文件分片读取、
文件编码自动检测和日志文件格式验证等功能。
"""

import os
import json
import chardet
from typing import Generator, Optional, List, Dict
from pathlib import Path

class LogReader:
    """Unity 日志读取器
    
    支持大文件分片读取、自动编码检测和基本的日志格式验证。
    
    Attributes:
        filepath (str): 日志文件路径
        encoding (str): 文件编码
        chunk_size (int): 文件读取的块大小，默认 1MB
    """
    
    def __init__(self, filepath: str, config_path: Optional[str] = None, encoding: Optional[str] = None, chunk_size: Optional[int] = None):
        """初始化日志读取器
        
        Args:
            filepath (str): 日志文件路径
            config_path (str, optional): 配置文件路径，如果不指定则使用默认配置
            encoding (str, optional): 文件编码，默认自动检测
            chunk_size (int, optional): 分片读取的块大小，默认使用配置值
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: chunk_size 小于等于 0 时抛出
        """
        self.filepath = filepath
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在：{filepath}")

        # 加载配置
        self.config = self._load_config(config_path)
        
        # 设置块大小
        self.chunk_size = (chunk_size if chunk_size is not None 
                          else self.config['file_reading']['default_chunk_size'])
        if self.chunk_size <= 0:
            raise ValueError("块大小必须大于0")
        
        # 检查编码
        if encoding and encoding not in self.config['file_reading']['supported_encodings']:
            raise ValueError(f"不支持的编码格式：{encoding}")
        self.encoding = encoding or self.detect_encoding(filepath)
        
        self._validated = False
        
    def read_lines(self) -> Generator[str, None, None]:
        """按行读取日志文件，使用生成器避免内存溢出。
        
        如果文件格式未经验证，会先进行验证。
        
        Yields:
            str: 每一行的内容（不含换行符）
            
        Raises:
            ValueError: 日志格式无效时抛出
            IOError: 文件读取错误时抛出
        """
        if not self._validated:
            self.validate_log_format()
            
        try:
            with open(self.filepath, 'r', encoding=self.encoding, errors='ignore') as f:
                for line in f:
                    yield line.rstrip('\n')
        except IOError as e:
            raise IOError(f"读取文件失败：{e}")

    def read_chunks(self, chunk_size: Optional[int] = None) -> Generator[str, None, None]:
        """按字节分块读取日志文件，适合极大文件。
        
        Args:
            chunk_size (int, optional): 分片大小（字节），如果不指定则使用实例的 chunk_size
        
        Yields:
            str: 文件内容片段
            
        Raises:
            IOError: 文件读取错误时抛出
            UnicodeDecodeError: 编码解码错误时抛出
        """
        if not self._validated:
            self.validate_log_format()
            
        chunk_size = chunk_size or self.chunk_size
        
        try:
            with open(self.filepath, 'r', encoding=self.encoding, errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except IOError as e:
            raise IOError(f"读取文件失败：{e}")

    def filter_lines(self, keyword: Optional[str] = None) -> Generator[str, None, None]:
        """只返回包含关键字的行。
        
        Args:
            keyword (str, optional): 过滤关键字，如果为 None 则返回所有行
            
        Yields:
            str: 符合条件的行
        """
        for line in self.read_lines():
            if keyword is None or keyword in line:
                yield line

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """加载配置文件
        
        Args:
            config_path (str, optional): 配置文件路径
            
        Returns:
            Dict: 配置信息
            
        Raises:
            FileNotFoundError: 配置文件不存在时抛出
        """
        default_config_path = Path(__file__).parent.parent.parent / 'config' / 'log_parser_config.json'
        config_file = Path(config_path) if config_path else default_config_path
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在：{config_file}")
            
        try:
            with open(config_file, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception as e:
            print(f"[LogReader] Warning: 加载配置文件失败 ({e})，使用默认配置")
            return {
                "log_validation": {
                    "markers": ["[Unity]"],
                    "min_matches": 1,
                    "scan_size_kb": 4
                },
                "file_reading": {
                    "default_chunk_size": 8192,
                    "default_encoding": "utf-8",
                    "supported_encodings": ["utf-8", "gbk", "utf-16"],
                    "encoding_confidence_threshold": 0.7
                }
            }
            
    def validate_log_format(self) -> bool:
        """验证是否为 Unity 日志格式
        
        读取文件开头部分验证是否包含 Unity 日志的特征标记。
        
        Returns:
            bool: 如果是有效的 Unity 日志返回 True
            
        Raises:
            ValueError: 如果不是有效的 Unity 日志格式
        """
        validation_config = self.config['log_validation']
        unity_markers = validation_config['markers']
        min_matches = validation_config['min_matches']
        scan_size = validation_config['scan_size_kb'] * 1024
        
        try:
            with open(self.filepath, 'r', encoding=self.encoding, errors='ignore') as f:
                # 读取文件内容
                content = f.read(scan_size)
                matches = sum(1 for marker in unity_markers if marker in content)
                if matches >= min_matches:
                    self._validated = True
                    return True
                raise ValueError(f"无效的 Unity 日志格式：{self.filepath}（找到 {matches} 个标记，需要至少 {min_matches} 个）")
        except IOError as e:
            raise IOError(f"读取文件失败：{e}")

    def detect_encoding(self, filepath: str) -> str:
        """检测文件编码
        
        使用 chardet 库进行编码检测，如果检测失败则回退到基本编码尝试。
        
        Args:
            filepath (str): 文件路径
            
        Returns:
            str: 检测到的编码名称
        """
        reading_config = self.config['file_reading']
        confidence_threshold = reading_config['encoding_confidence_threshold']
        supported_encodings = reading_config['supported_encodings']
        default_encoding = reading_config['default_encoding']
        
        try:
            # 首先使用 chardet 检测
            with open(filepath, 'rb') as f:
                raw = f.read(4096)  # 读取前 4KB 进行检测
                result = chardet.detect(raw)
                detected_encoding = result['encoding'].lower()
                
                # 检查是否为支持的编码
                if result['confidence'] > confidence_threshold:
                    for supported_enc in supported_encodings:
                        if detected_encoding in supported_enc.lower():
                            return supported_enc
                            
            # chardet 检测失败或编码不支持，尝试所有支持的编码
            for enc in supported_encodings:
                try:
                    raw.decode(enc.lower())
                    return enc
                except UnicodeDecodeError:
                    continue
                    
        except Exception as e:
            print(f"[LogReader] Warning: 编码检测失败 ({e})，使用默认编码 {default_encoding}")
        
        return default_encoding