"""
基础接口和抽象类定义
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


# 异常体系
class ExtractorError(Exception):
    """提取器基础异常类"""
    pass

class PatternError(ExtractorError):
    """模式匹配错误"""
    pass

class AnalysisError(ExtractorError):
    """分析处理错误"""
    pass

class AggregationError(ExtractorError):
    """聚合处理错误"""
    pass


class BaseExtractor(ABC):
    """
    提取器基类
    所有具体提取器需继承并实现 extract 方法。
    """
    @abstractmethod
    def extract(self, data: Any, context: Optional['ExtractorContext'] = None) -> 'ExtractResult':
        """
        抽象提取方法
        :param data: 输入数据（如日志文本、分片等）
        :param context: 提取上下文
        :return: 提取结果对象
        """
        pass


class ExtractorContext:
    """
    提取上下文
    包含配置、状态、缓存等信息，供提取器使用。
    """
    def __init__(self, config: dict, state: Optional[dict] = None):
        self.config = config
        self.state = state or {}
        # 可扩展更多上下文属性，如缓存、统计等


class ExtractResult:
    """
    提取结果
    存储所有提取出的片段及相关元数据。
    """
    def __init__(self, segments: Optional[List[Any]] = None, meta: Optional[dict] = None):
        self.segments = segments or []
        self.meta = meta or {}
