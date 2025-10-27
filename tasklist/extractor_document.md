# Unity 日志提取器设计文档

## 1. 系统概述
日志提取器（LogExtractor）是Unity日志分析系统的核心组件，负责从原始日志中提取、分析和组织有意义的信息片段。它通过多层次分析和智能处理，实现高质量的日志信息提取和组织。

## 2. 文件结构设计
```
src/log_parser/extractor/
├── __init__.py                 # 导出主要的类和接口
├── base.py                     # 基础接口和抽象类定义
├── extractors/                 # 不同类型的提取器实现
│   ├── __init__.py
│   ├── error_extractor.py      # 错误信息提取器
│   ├── stack_extractor.py      # 堆栈信息提取器
│   ├── env_extractor.py        # 环境信息提取器
│   └── factory.py              # 提取器工厂
├── patterns/                   # 提取模式定义
│   ├── __init__.py
│   ├── regex_patterns.py       # 正则表达式模式
│   ├── pattern_manager.py      # 模式管理器
│   └── pattern_optimizer.py    # 模式优化器
├── analyzers/                  # 分析器实现
│   ├── __init__.py
│   ├── context_analyzer.py     # 上下文分析器
│   ├── semantic_analyzer.py    # 语义分析器
│   └── causality_analyzer.py   # 因果关系分析器
├── aggregators/                # 聚合器实现
│   ├── __init__.py
│   ├── segment_aggregator.py   # 片段聚合器
│   └── duplicate_detector.py   # 重复检测器
└── utils/                      # 工具类
    ├── __init__.py
    ├── normalizer.py          # 日志规范化工具
    ├── importance_calc.py     # 重要性计算器
    └── validators.py          # 数据验证工具

src/config/extractor/              # 提取器配置
├── __init__.py
├── config_manager.py          # 配置管理器
├── extractor_config.json      # 主配置文件
├── patterns/                  # 模式配置
│   ├── error_patterns.json    # 错误模式
│   ├── warning_patterns.json  # 警告模式
│   └── stack_patterns.json    # 堆栈模式
└── rules/                     # 规则配置
    ├── importance_rules.json  # 重要性规则
    └── merge_rules.json       # 合并规则
```

## 3. 核心组件说明

### 3.1 基础接口层
- `BaseExtractor`: 提取器基类
- `ExtractorContext`: 提取上下文
- `ExtractResult`: 提取结果

### 3.2 规范化处理
```python
class LogNormalizer:
    """日志规范化处理器"""
    def normalize_line(self, line: str) -> NormalizedLine:
        """规范化单行日志"""
        
    def normalize_chunk(self, chunk: LogChunk) -> List[NormalizedLine]:
        """规范化日志块"""
```

### 3.3 模式识别系统
```python
class LogPatterns:
    """日志模式定义"""
    ERROR_PATTERNS: Dict[str, Pattern]    # 错误模式
    WARNING_PATTERNS: Dict[str, Pattern]  # 警告模式
    STACK_PATTERNS: Dict[str, Pattern]    # 堆栈模式
    ENV_PATTERNS: Dict[str, Pattern]      # 环境信息模式
```

### 3.4 分析器实现
```python
class ContextAnalyzer:
    """上下文分析器"""
    def analyze_line(self, line: NormalizedLine) -> Optional[LogSegment]
    
class SemanticAnalyzer:
    """语义分析器"""
    def analyze_segment(self, segment: LogSegment) -> SegmentAnalysis
    
class CausalityAnalyzer:
    """因果关系分析器"""
    def analyze(self, segment: LogSegment) -> List[CausalRelation]
```

### 3.5 聚合系统
```python
class LogAggregator:
    """日志聚合器"""
    def add_segment(self, segment: LogSegment) -> None
    def get_organized_segments(self) -> List[LogSegment]
```

## 4. 配置项说明

```json
{
    "extractor": {
        "normalizer": {
            "timestamp_format": "%H:%M:%S",
            "max_line_length": 1048576,
            "strip_ansi": true
        },
        "context": {
            "window_size": 5,
            "min_context_lines": 2,
            "max_context_lines": 10
        },
        "patterns": {
            "cache_size": 1000,
            "optimization_level": 2
        },
        "analysis": {
            "semantic_depth": "deep",
            "causality_analysis": true,
            "max_relation_distance": 10
        },
        "aggregation": {
            "similarity_threshold": 0.85,
            "max_merge_distance": 20,
            "min_importance_score": 0.3
        }
    }
}
```

## 5. 处理流程

### 5.1 预处理阶段
1. 日志规范化
   - 清理无效字符
   - 提取时间戳
   - 标准化格式

2. 初步分段
   - 识别边界
   - 标记类型
   - 提取元数据

### 5.2 分析阶段
1. 上下文分析
   - 维护上下文窗口
   - 识别相关行
   - 计算上下文重要性

2. 语义分析
   - 提取关键概念
   - 识别错误类型
   - 分析严重程度

3. 因果分析
   - 识别依赖关系
   - 构建错误链
   - 推导根本原因

### 5.3 聚合阶段
1. 重复检测
   - 计算相似度
   - 识别重复内容
   - 合并相似片段

2. 结果组织
   - 按重要性排序
   - 关联相关片段
   - 生成层次结构

## 6. 优化机制

### 6.1 性能优化
- 模式缓存
- 并行处理
- 增量分析

### 6.2 内存优化
- 流式处理
- 数据压缩
- 缓存清理

### 6.3 准确性优化
- 模式优化
- 上下文扩展
- 误报过滤

## 7. 扩展能力

### 7.1 模式扩展
- 自定义错误模式
- 新类型识别
- 规则更新机制

### 7.2 分析器扩展
- 自定义分析器
- 新特征提取
- 结果处理器

### 7.3 输出扩展
- 自定义格式
- 结果过滤
- 统计聚合

## 8. 使用示例

```python
# 创建提取器实例
extractor = LogExtractor(config)

# 处理日志文件
async def process_log_file(file_path: str):
    reader = LogReader(file_path)
    result = await extractor.process_log(reader)
    
    # 获取提取结果
    for segment in result.segments:
        print(f"Type: {segment.type}")
        print(f"Importance: {segment.importance}")
        print(f"Content: {segment.content}")
        print(f"Analysis: {segment.analysis}")
```

## 9. 错误处理

### 9.1 异常类型
- `ExtractorError`: 基础异常类
- `PatternError`: 模式匹配错误
- `AnalysisError`: 分析处理错误
- `AggregationError`: 聚合处理错误

### 9.2 错误恢复
- 重试机制
- 降级处理
- 部分结果保存

## 10. 监控指标

### 10.1 性能指标
- 处理速度
- 内存使用
- 缓存命中率

### 10.2 质量指标
- 提取准确率
- 覆盖率
- 重复率

### 10.3 系统指标
- 错误率
- 超时率
- 资源使用率