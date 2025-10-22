# Unity 日志读取器设计文档

## 1. 系统概述
日志读取器（LogReader）是 Unity 日志分析系统的基础组件，负责高效、可靠地读取和预处理构建日志文件。它支持大文件分片处理、多种文件格式，并提供性能监控和缓存优化功能。

## 2. 文件结构设计
```
src/log_parser/
├── reader/
│   ├── __init__.py                    # 导出主要的类和接口
│   ├── base.py                        # 基础接口和抽象类定义
│   ├── exceptions.py                  # 自定义异常类定义
│   ├── file_handlers/                 # 不同文件类型的处理器
│   │   ├── __init__.py
│   │   ├── base.py                    # 文件处理器基类
│   │   ├── text_handler.py            # 文本文件处理器
│   │   ├── gzip_handler.py            # GZIP文件处理器
│   │   └── factory.py                 # 文件处理器工厂
│   ├── iterators/                     # 迭代器相关实现
│   │   ├── __init__.py
│   │   ├── chunk_iterator.py          # 分片迭代器
│   │   └── line_iterator.py           # 行迭代器
│   ├── cache/                         # 缓存实现
│   │   ├── __init__.py
│   │   ├── cache_manager.py           # 缓存管理器
│   │   └── strategies.py              # 缓存策略实现
│   ├── monitoring/                    # 监控相关实现
│   │   ├── __init__.py
│   │   ├── stats_collector.py         # 统计信息收集器
│   │   └── memory_monitor.py          # 内存使用监控
│   └── log_reader.py                  # 主要的LogReader类实现

config/
├── log_parser/                        # 日志解析相关配置
│   ├── __init__.py
│   ├── config_manager.py              # 配置管理器实现
│   ├── config_validator.py            # 配置验证器
│   ├── defaults.py                    # 默认配置定义
│   └── schema.py                      # 配置schema定义
└── log_parser_config.json             # 配置文件

tests/log_parser/                      # 测试目录
├── __init__.py
├── test_log_reader.py                 # LogReader测试
└── [...其他测试文件]
```

## 3. 核心组件说明

### 3.1 基础接口层
- `LogFileHandler`: 文件处理器接口
- `LogIterator`: 日志迭代器接口
- 提供统一的抽象接口定义

### 3.2 文件处理器
- 支持多种文件格式（文本、GZIP）
- 工厂模式创建处理器
- 统一的文件操作接口

### 3.3 迭代器实现
- 分片迭代：高效处理大文件
- 行迭代：按行读取内容
- 支持惰性加载

### 3.4 缓存系统
- 缓存管理器
- 多种缓存策略（LRU、TTL）
- 内存使用优化

### 3.5 监控系统
- 性能统计收集
- 内存使用监控
- 运行状态跟踪

### 3.6 配置管理
- JSON格式配置文件
- 配置验证机制
- 默认值处理

## 4. 配置项说明

```json
{
    "reader": {
        "chunk_size": 8388608,          // 分片大小（8MB）
        "encoding": "utf-8",            // 文件编码
        "supported_extensions": [".txt", ".log", ".gz"],
        "buffer_size": 4096,            // 缓冲区大小（4KB）
        "max_line_length": 1048576,     // 最大行长度（1MB）
        "compression": {
            "enable_gzip": true,
            "gzip_buffer_size": 65536    // GZIP缓冲区（64KB）
        },
        "performance": {
            "enable_caching": true,
            "cache_size": 104857600,     // 缓存限制（100MB）
            "enable_parallel": false,
            "max_workers": 4
        },
        "error_handling": {
            "max_retries": 3,
            "retry_delay": 1.0,
            "skip_corrupted_lines": true
        },
        "monitoring": {
            "enable_stats": true,
            "stats_interval": 5.0,
            "memory_threshold": 0.8
        }
    }
}
```

## 5. 异常处理机制

### 5.1 异常类型
- `LogReaderError`: 基础异常类
- `FileFormatError`: 文件格式错误
- `ReadError`: 读取错误
- `ConfigError`: 配置错误

### 5.2 错误处理策略
- 重试机制
- 错误跳过
- 详细日志记录

## 6. 性能优化

### 6.1 读取优化
- 分片处理
- 缓存机制
- 并行处理支持

### 6.2 内存优化
- 惰性加载
- 内存使用监控
- 自动清理机制

## 7. 扩展性设计

### 7.1 处理器扩展
- 支持添加新的文件格式
- 自定义处理器实现

### 7.2 缓存策略扩展
- 自定义缓存策略
- 可配置缓存参数

### 7.3 监控指标扩展
- 自定义统计指标
- 监控回调机制