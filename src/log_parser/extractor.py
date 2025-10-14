#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unity构建日志提取器

该模块负责对Unity构建日志进行预处理、分段和规范化，为后续的规则匹配做准备。
主要包含三个核心组件：
1. LineProcessor: 处理单行日志的清洗和格式化
2. LogSegmenter: 根据规则将日志分割成有意义的段落
3. LogNormalizer: 统一不同格式日志的表示形式
"""

from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
import re
import json
from pathlib import Path

def load_json_config(config_path: Path) -> Dict:
    """加载JSON配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict: 配置信息
    """
    with config_path.open('r', encoding='utf-8-sig') as f:
        return json.load(f)

@dataclass
class LogLine:
    """表示处理后的单行日志"""
    raw_content: str           # 原始内容
    cleaned_content: str       # 清洗后的内容
    line_number: int          # 行号

class LineProcessor:
    """日志行处理器
    
    负责清理和格式化单行日志，提取时间戳、日志级别等信息。
    """
    def __init__(self, config_path: Optional[Path] = None):
        """初始化行处理器
        
        Args:
            config_path: 配置文件路径，包含清理规则和正则表达式
        """
        self.config = load_json_config(config_path) if config_path else {}
    
    def should_ignore(self, line: str) -> bool:
        """检查是否应该忽略该行
        
        Args:
            line: 日志行
            
        Returns:
            bool: 如果应该忽略则返回True
        """
        ignore_patterns = self.config.get('ignore_patterns', [])
        return any(
            re.match(pattern, line)
            for pattern in ignore_patterns
        )
    
    def clean_line(self, line: str) -> str:
        """应用清理规则
        
        Args:
            line: 原始日志行
            
        Returns:
            str: 清理后的日志行
        """
        cleaned = line
        cleaned = re.sub("\\s+", " ", cleaned)
        for rule in self.config.get('clean_rules', []):
            cleaned = re.sub(rule, "", cleaned)
        return cleaned
    
    def process_line(self, line: str, line_number: int) -> Optional[LogLine]:
        """处理单行日志
        
        Args:
            line: 原始日志行
            line_number: 行号
            
        Returns:
            Optional[LogLine]: 处理后的日志行对象，如果行应被忽略则返回None
        """
        if self.should_ignore(line):
            return None
            
        cleaned_content = self.clean_line(line)
        if not cleaned_content:  # 如果清理后为空，也忽略该行
            return None
            
        return LogLine(
            raw_content=line,
            cleaned_content=cleaned_content,
            line_number=line_number
        )

class LogSegmenter:
    """日志分段器
    
    根据规则将连续的日志行分割成有意义的段落。
    """
    def __init__(self, config_path: Optional[Path] = None):
        """初始化分段器
        
        Args:
            config_path: 配置文件路径，包含分段规则
        """
        self.config = load_json_config(config_path) if config_path else {}
    
    def segment_logs(self, log_lines: List[LogLine]) -> List[List[LogLine]]:
        """将日志行分割成段落
        
        Args:
            log_lines: 处理后的日志行列表
            
        Returns:
            List[List[LogLine]]: 分段后的日志段落列表
        """
        # TODO: 实现具体的分段逻辑
        return [log_lines]  # 暂时返回单个段落

class LogNormalizer:
    """日志规范化器
    
    统一不同格式日志的表示形式，便于后续规则匹配。
    """
    def __init__(self, config_path: Optional[Path] = None):
        """初始化规范化器
        
        Args:
            config_path: 配置文件路径，包含规范化规则
        """
        self.config = load_json_config(config_path) if config_path else {}
    
    def normalize_segment(self, segment: List[LogLine]) -> Dict:
        """规范化日志段落
        
        Args:
            segment: 日志段落（LogLine对象列表）
            
        Returns:
            Dict: 规范化后的日志段落，包含结构化信息
        """
        # TODO: 实现具体的规范化逻辑
        return {
            'lines': [line.cleaned_content for line in segment],
            'metadata': {
                'start_line': segment[0].line_number if segment else None,
                'end_line': segment[-1].line_number if segment else None
            }
        }

class LogExtractor:
    """日志提取器
    
    整合LineProcessor、LogSegmenter和LogNormalizer，
    提供完整的日志处理流程。
    """
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化日志提取器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir) if config_dir else None
        self.line_processor = LineProcessor(
            self.config_dir / 'line_processor.json' if self.config_dir else None
        )
        self.segmenter = LogSegmenter(
            self.config_dir / 'log_segmenter.json' if self.config_dir else None
        )
        self.normalizer = LogNormalizer(
            self.config_dir / 'log_normalizer.json' if self.config_dir else None
        )
    
    def process_logs(self, log_content: str) -> List[Dict]:
        """处理日志内容
        
        完整的处理流程：行处理 -> 分段 -> 规范化
        
        Args:
            log_content: 原始日志内容
            
        Returns:
            List[Dict]: 处理后的规范化日志段落列表
        """
        # 1. 处理每一行，过滤掉None结果
        lines = log_content.splitlines()
        processed_lines = [
            result for result in (
                self.line_processor.process_line(line, i+1)
                for i, line in enumerate(lines)
            ) if result is not None
        ]
        
        # 2. 分段
        segments = self.segmenter.segment_logs(processed_lines)
        
        # 3. 规范化每个段落
        normalized_segments = [
            self.normalizer.normalize_segment(segment)
            for segment in segments
        ]
        
        return normalized_segments
