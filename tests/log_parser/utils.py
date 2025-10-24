"""测试包的公共工具和基础设施。"""

import os
import tempfile
import threading
from pathlib import Path
from typing import Iterator, Optional, Dict, Any

class TestTimeout:
    """测试超时装饰器。
    
    用法:
        @TestTimeout(5)
        def test_something(self):
            # 测试代码
    """
    
    def __init__(self, seconds: int):
        """初始化超时装饰器。
        
        Args:
            seconds: 超时时间（秒）
        """
        self.seconds = seconds
        
    def __call__(self, func):
        def wrapped(instance):
            timeout_flag = {'timeout': False}
            
            def target():
                try:
                    func(instance)
                except Exception as e:
                    instance.test_exception = e
                    
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(self.seconds)
            
            if thread.is_alive():
                timeout_flag['timeout'] = True
                raise TimeoutError(f"测试超时（{self.seconds}秒）")
                
            if hasattr(instance, 'test_exception'):
                raise instance.test_exception
                
        return wrapped

class TestFileManager:
    """测试文件管理器，用于创建和管理测试用的临时文件。"""
    
    def __init__(self) -> None:
        self._temp_dir: Optional[str] = None
        self._files: list[str] = []
        
    def __enter__(self) -> 'TestFileManager':
        self._temp_dir = tempfile.mkdtemp(prefix='log_parser_test_')
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
        
    def create_file(self, content: bytes, suffix: str = '.txt') -> Path:
        """创建临时测试文件。

        Args:
            content: 文件内容
            suffix: 文件扩展名

        Returns:
            临时文件路径
        """
        if not self._temp_dir:
            raise RuntimeError("TestFileManager未初始化")
            
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            dir=self._temp_dir,
            delete=False
        ) as f:
            f.write(content)
            self._files.append(f.name)
            return Path(f.name)
            
    def cleanup(self) -> None:
        """清理所有临时文件。"""
        for file in self._files:
            try:
                os.unlink(file)
            except OSError:
                pass
                
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                os.rmdir(self._temp_dir)
            except OSError:
                pass
            
        self._temp_dir = None
        self._files.clear()