# Unity 日志结构化器设计文档

## 1. 系统概述
日志结构化器（LogStructor）是Unity日志分析系统的组织层组件，负责将提取器得到的非结构化信息转换为标准的结构化数据，并提供灵活的存储、去重和组织功能。它通过多层次的数据处理和智能去重，实现高质量的日志整理和管理。

## 2. 文件结构设计
```
src/log_parser/structor/
├── __init__.py                 # 导出主要的类和接口
├── base.py                     # 基础接口和抽象类定义
├── models/                     # 数据模型定义
│   ├── __init__.py
│   ├── log_entry.py           # 日志条目模型
│   ├── log_features.py        # 日志特征模型
│   └── build_report.py        # 构建报告模型
├── processors/                 # 处理器实现
│   ├── __init__.py
│   ├── content_processor.py   # 内容处理器
│   └── metadata_processor.py  # 元数据处理器
├── storage/                   # 存储相关实现
│   ├── __init__.py
│   ├── storage_handler.py     # 存储处理器
│   └── compression.py         # 压缩处理器
├── deduplication/             # 去重相关实现
│   ├── __init__.py
│   ├── deduplicator.py       # 去重处理器
│   ├── strategies/           # 去重策略
│   │   ├── __init__.py
│   │   ├── exact_match.py    # 精确匹配
│   │   ├── similarity.py     # 相似度匹配
│   │   └── pattern_match.py  # 模式匹配
│   └── cache.py              # 特征缓存
└── formatters/               # 格式化器实现
    ├── __init__.py
    ├── json_formatter.py     # JSON格式化器
    └── yaml_formatter.py     # YAML格式化器

config/structor/              # 配置文件目录
├── __init__.py
├── structor_config.json     # 主配置文件
└── schemas/                 # JSON Schema定义
    ├── log_entry.json
    └── deduplication.json
```

## 3. 核心功能模块

### 3.1 内容处理系统
```python
class ContentProcessor:
    """内容处理器，负责处理多行日志及其上下文"""
    
    def process_log_content(self, content: LogContent) -> ProcessedContent:
        """处理日志内容，包括上下文处理和内容合并"""

    def _handle_context(self, content: str, context_lines: int) -> List[str]:
        """处理日志上下文"""

    def _merge_nearby_logs(self, content: str, threshold: int) -> str:
        """合并相近的日志内容"""
```

### 3.2 存储管理系统
```python
class LogStorageHandler:
    """日志存储处理器"""
    
    async def store_log_entry(self, log_entry: LogEntry) -> None:
        """存储单个日志条目"""
        
    def _process_content(self, log_entry: LogEntry) -> Dict[str, Any]:
        """处理日志内容，包括上下文处理和内容合并"""
        
    async def _write_to_disk(self, content: Dict[str, Any], 
                           metadata: Dict[str, Any]) -> None:
        """将内容写入磁盘"""
```

### 3.3 去重系统
```python
class LogDeduplicator:
    """日志去重处理器"""
    
    async def process(self, log_entry: LogEntry) -> Tuple[bool, Optional[str]]:
        """处理日志条目，返回(是否重复, 重复组ID)"""
        
    def _extract_features(self, log_entry: LogEntry) -> LogFeatures:
        """提取日志特征用于比较"""
```

## 4. 配置系统

### 4.1 存储配置
```json
{
    "structor": {
        "storage": {
            "enable_disk_output": true,
            "output_directory": "output",
            "file_pattern": "{timestamp}_{level}.json",
            "content_handling": {
                "context_lines": 5,
                "merge_threshold": 10,
                "split_large_content": true,
                "max_file_size": "10MB"
            },
            "compression": {
                "enable": false,
                "method": "gzip"
            }
        }
    }
}
```

### 4.2 去重配置
```json
{
    "structor": {
        "deduplication": {
            "enable": true,
            "strategies": {
                "exact_match": {
                    "enable": true,
                    "ignore_fields": ["timestamp", "line_number"]
                },
                "similarity_match": {
                    "enable": true,
                    "threshold": 0.85,
                    "compare_fields": [
                        "error_message",
                        "stack_trace",
                        "context"
                    ]
                },
                "pattern_match": {
                    "enable": true,
                    "patterns": {
                        "stack_trace": {
                            "ignore_line_numbers": true,
                            "ignore_file_paths": false
                        },
                        "error_message": {
                            "ignore_variables": true,
                            "variable_patterns": [
                                "\\d+",
                                "'[^']*'",
                                "\"[^\"]*\""
                            ]
                        }
                    }
                }
            },
            "grouping": {
                "enable": true,
                "max_group_size": 100,
                "group_by_fields": [
                    "error_type",
                    "component"
                ]
            }
        }
    }
}
```

## 5. 处理流程

### 5.1 基本流程
1. 接收提取器结果
2. 数据预处理和规范化
3. 去重检查
4. 内容处理（上下文和合并）
5. 存储处理
6. 返回结构化结果

### 5.2 去重流程
1. 特征提取
2. 多策略去重检查
3. 结果分组
4. 更新统计信息

### 5.3 存储流程
1. 内容处理和组织
2. 文件名生成
3. 压缩处理（如果启用）
4. 磁盘写入

## 6. 性能优化

### 6.1 内存优化
- 流式处理大文件
- 特征缓存管理
- 定期清理机制

### 6.2 速度优化
- 异步IO操作
- 并行处理支持
- 智能缓存策略

### 6.3 存储优化
- 相似内容合并
- 重复内容去除
- 可选压缩支持

## 7. 错误处理

### 7.1 异常类型
- `StructorError`: 基础异常类
- `StorageError`: 存储相关错误
- `DeduplicationError`: 去重相关错误
- `ProcessingError`: 处理相关错误

### 7.2 错误恢复
- 自动重试机制
- 降级处理策略
- 部分结果保存

## 8. 使用示例

```python
# 创建结构化器实例
structor = LogStructor(config)

# 处理提取器结果
async def process_log(extractor_result: ExtractorResult):
    # 处理并获取结构化结果
    result = await structor.process(extractor_result)
    
    # 检查是否是重复日志
    if result.is_duplicate:
        print(f"发现重复日志，组ID: {result.group_id}")
    else:
        print(f"新日志已处理并存储")
        
    # 获取结构化数据
    structured_data = result.structured_data
```

## 9. 监控指标

### 9.1 性能指标
- 处理速度
- 内存使用
- 存储效率
- 去重率

### 9.2 质量指标
- 去重准确率
- 合并效果
- 数据完整性
- 存储可靠性

## 10. 扩展能力

### 10.1 存储扩展
- 新的存储格式支持
- 自定义存储处理器
- 外部存储集成

### 10.2 去重扩展
- 新的去重策略
- 自定义特征提取
- 自定义分组规则

### 10.3 处理扩展
- 自定义内容处理器
- 新的格式化器
- 自定义验证规则