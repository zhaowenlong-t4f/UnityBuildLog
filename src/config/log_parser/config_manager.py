"""配置管理器实现。"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .defaults import DEFAULT_CONFIG
from .config_validator import ConfigValidator

class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器。"""
    
    def __init__(self, callback: Callable[[], None]) -> None:
        """初始化处理器。
        
        Args:
            callback: 配置变更时的回调函数
        """
        self.callback = callback
        
    def on_modified(self, event: FileModifiedEvent) -> None:
        """文件修改事件处理。"""
        if not event.is_directory:
            self.callback()

class ConfigManager:
    """配置管理器，负责加载、验证和管理配置。
    
    支持：
    1. 配置文件加载和保存
    2. 配置验证
    3. 热重载
    4. 默认值管理
    """
    
    def __init__(self, config_path: str | Path, enable_watch: bool = True) -> None:
        """初始化配置管理器。
        
        Args:
            config_path: 配置文件路径
            enable_watch: 是否启用文件监控功能，测试时可设为False
        """
        print(f"\n=== 初始化配置管理器 ===")
        print(f"配置文件路径: {config_path}")
        print(f"是否启用监控: {enable_watch}")
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._observer = None
        self._handler = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._enable_watch = enable_watch
        
        # 加载初始配置
        print("加载初始配置...")
        self.load_config()
        print("初始化完成")
    def load_config(self) -> None:
        """加载配置文件。
        
        如果配置文件不存在，将创建默认配置文件。
        """
        print(f"加载配置文件: {self.config_path}")
        with self._lock:
            print("已获取锁...")
            if not self.config_path.exists():
                print("配置文件不存在，创建默认配置...")
                # 创建默认配置文件
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
                print("默认配置已保存")
            else:
                print("读取现有配置文件...")
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                    print("配置文件已读取")
                    
                    print("验证配置（宽松模式）...")
                    # 验证配置，使用非严格模式
                    errors = ConfigValidator.validate_config(loaded_config, strict=False)
                    if errors:
                        raise ValueError(f"配置验证失败：\n" + "\n".join(errors))
                    print("配置验证通过")
                    
                    print("合并默认配置...")
                    # 合并默认配置
                    self.config = self._merge_with_defaults(loaded_config)
                    print("配置合并完成")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    raise ValueError(f"配置文件格式错误：{e}")
                except Exception as e:
                    print(f"加载失败: {e}")
                    raise ValueError(f"加载配置文件失败：{e}")
            print("配置加载完成")
    
    def save_config(self) -> None:
        """保存配置到文件。"""
        print("=== 开始保存配置 ===")
        try:
            # 确保目录存在
            print(f"检查目录: {self.config_path.parent}")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            print("写入配置文件...")
            # 保存配置
            config_data = json.dumps(self.config, indent=4, ensure_ascii=False)
            print(f"配置内容预览: {config_data[:100]}...")
            
            # 原子写入：首先写入临时文件，然后重命名
            temp_path = self.config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(config_data)
                f.flush()
                os.fsync(f.fileno())  # 确保写入磁盘
                
            print("临时文件写入完成，进行重命名...")
            if os.name == 'nt' and self.config_path.exists():
                # Windows需要先删除目标文件
                os.remove(self.config_path)
            os.rename(temp_path, self.config_path)
            print("配置文件保存完成")
            
        except Exception as e:
            print(f"保存失败: {e}")
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise ValueError(f"保存配置文件失败：{e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置。
        
        Returns:
            当前配置的副本
        """
        with self._lock:
            return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置。
        
        Args:
            new_config: 新的配置字典
            
        Raises:
            ValueError: 配置验证失败时
        """
        print("\n=== 开始更新配置 ===")
        # 先在锁外部验证配置
        print("验证新配置...")
        errors = ConfigValidator.validate_config(new_config)
        if errors:
            raise ValueError(f"配置验证失败：\n" + "\n".join(errors))
        
        # 准备新配置
        print("合并新配置...")
        merged_config = self._merge_with_defaults(new_config)
        
        print("获取锁...")
        with self._lock:
            print("已获取锁，更新配置...")
            # 更新配置
            self.config = merged_config
            
            try:
                print("保存配置到文件...")
                # 保存到文件
                self.save_config()
                print("配置已保存")
            except Exception as e:
                print(f"保存失败: {e}")
                # 如果保存失败，恢复原始配置
                self.config = self.get_config()
                raise
            
        print("释放锁")
        # 锁外部执行回调
        print("执行回调...")
        self._notify_callbacks()
        print("配置更新完成")
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """将配置与默认配置合并。
        
        Args:
            config: 要合并的配置
            
        Returns:
            合并后的配置
        """
        print("\n=== 开始合并配置 ===")
        import copy
        print("正在复制默认配置...")
        result = copy.deepcopy(DEFAULT_CONFIG)  # 使用深拷贝
        
        def merge_dict(base: Dict[str, Any], update: Dict[str, Any], path: str = "") -> Dict[str, Any]:
            print(f"正在合并路径: {path}")
            for key, value in update.items():
                current_path = f"{path}.{key}" if path else key
                print(f"处理键: {current_path}")
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    print(f"发现嵌套字典: {current_path}")
                    # 递归合并字典，但要创建新的字典对象
                    base[key] = merge_dict(copy.deepcopy(base[key]), value, current_path)
                else:
                    print(f"更新值: {current_path}")
                    # 对于非字典值，直接进行深拷贝
                    base[key] = copy.deepcopy(value)
            return base  # 返回合并后的字典
        
        print("开始合并配置...")
        merge_dict(result, config)
        print("配置合并完成")
        return result
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册配置变更回调函数。
        
        Args:
            callback: 配置变更时调用的函数，接收新配置作为参数
        """
        self._callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        """通知所有回调函数配置已更新。"""
        config = self.get_config()
        for callback in self._callbacks:
            try:
                callback(config)
            except Exception as e:
                print(f"配置回调执行失败：{e}")
    
    def start_watch(self) -> None:
        """开始监控配置文件变更。"""
        if not self._enable_watch or self._observer is not None:
            return
            
        self._handler = ConfigChangeHandler(self._on_config_changed)
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self.config_path.parent),
            recursive=False
        )
        self._observer.start()
    
    def stop_watch(self) -> None:
        """停止监控配置文件变更。"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._handler = None
    
    def _on_config_changed(self) -> None:
        """配置文件变更处理。"""
        try:
            self.load_config()
            self._notify_callbacks()
        except Exception as e:
            print(f"重新加载配置失败：{e}")
    
    def __enter__(self) -> 'ConfigManager':
        """上下文管理器入口。"""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。"""
        self.stop_watch()