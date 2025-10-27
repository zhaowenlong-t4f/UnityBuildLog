# UnityBuildLog Reader模块用户手册

## 1. 模块结构与文件布局

Reader模块专为高效读取和预处理Unity构建日志设计，目录结构如下：
```
src/log_parser/reader/
├── base.py                # 抽象接口与核心数据结构
├── exceptions.py          # 异常体系
├── file_handlers/         # 文件处理器（文本/GZIP/工厂）
├── iterators/             # 分片/行/预读取迭代器
├── cache/                 # 缓存管理与策略
├── monitoring/            # 性能与内存监控
├── parallel/              # 并行处理相关
├── __init__.py            # 导出主要接口
```

## 2. 功能总览

- **多格式文件处理**：自动识别文本、GZIP等格式，支持扩展。
- **分片与行迭代**：ChunkIterator高效分片，LineIterator逐行读取，PrefetchIterator异步预读取。
- **缓存优化**：CacheManager统一管理缓存，支持LRU/TTL策略。
- **性能监控**：StatsCollector收集IO/缓存/操作延迟，MemoryMonitor监控内存趋势。
- **并行处理**：ParallelReader结合线程池、负载均衡、任务管理，实现多线程分片读取。
- **异常处理**：ErrorHandler支持重试、延迟、恢复回调。
- **灵活配置**：支持JSON配置，参数可自定义。

## 3. 主要接口与用法

### 3.1 文件处理器
- `TextFileHandler`：普通文本文件读取，支持编码/缓冲区设置。
- `GzipFileHandler`：GZIP压缩文件自动解压读取。
- `FileHandlerFactory`：根据扩展名自动选择处理器，支持自定义注册。

### 3.2 迭代器
- `ChunkIterator`：按分片高效读取，自动处理分片边界。
- `LineIterator`：逐行读取，支持大行拆分与缓冲。
- `PreFetchIterator`：为任意迭代器添加异步预读取能力。

### 3.3 缓存系统
- `CacheManager`：统一缓存管理，支持最大容量设置与统计。
- `LRUCache`/`TTLCache`：最近最少使用/定时过期策略。

### 3.4 性能与监控
- `StatsCollector`：收集IO、缓存、操作延迟等统计。
- `MemoryMonitor`：监控内存使用率、趋势、自动GC与泄漏检测。
- `ThreadMonitor`：线程级性能统计（并行场景）。

### 3.5 并行处理
- `ParallelReader`：多线程分片读取，自动负载均衡与错误恢复。
- `ThreadPool`/`TaskManager`/`LoadBalancer`/`ErrorHandler`：并行任务分发、线程管理、负载调整、错误处理。

### 3.6 异常体系
- `LogReaderError`：所有reader异常基类。
- `FileFormatError`/`ReadError`/`ConfigError`：文件格式、读取、配置相关异常。

## 4. 使用示例

### 4.1 读取文本日志文件
```python
from src.log_parser.reader.file_handlers import FileHandlerFactory
factory = FileHandlerFactory()
handler = factory.get_handler(Path('build_log.txt'))
handler.open()
for line in handler.read():
    print(line)
handler.close()
```

### 4.2 分片迭代大文件
```python
from src.log_parser.reader.iterators import ChunkIterator
handler = factory.get_handler(Path('large_log.txt'))
chunk_iter = ChunkIterator(handler, chunk_size=8*1024*1024)
for chunk in chunk_iter:
    process(chunk)
```

### 4.3 并行读取
```python
from src.log_parser.reader.parallel import ParallelReader
context = ReaderContext(Path('big_log.txt'))
handler = factory.get_handler(context.file_path)
reader = ParallelReader(context, handler, max_workers=4)
reader.initialize()
results = reader.read_chunks()
reader.close()
```

### 4.4 缓存与性能监控
```python
from src.log_parser.reader.cache import CacheManager, LRUCache
cache = CacheManager(LRUCache(), max_size=100*1024*1024)
cache.put('log1', 'data...')
print(cache.get_stats())

from src.log_parser.reader.monitoring import StatsCollector
stats = StatsCollector()
stats.collect_io_stats(1024, 0.01)
print(stats.get_statistics())
```

## 5. 配置说明

配置文件示例（`config/log_parser/log_parser_config.json`）：
```json
{
  "reader": {
    "chunk_size": 8388608,
    "encoding": "utf-8",
    "supported_extensions": [".txt", ".log", ".gz"],
    "buffer_size": 4096,
    "max_line_length": 1048576,
    "compression": {
      "enable_gzip": true,
      "gzip_buffer_size": 65536
    },
    "performance": {
      "enable_caching": true,
      "cache_size": 104857600,
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

## 6. 异常处理机制

- 所有异常均继承自`LogReaderError`，可统一捕获。
- 支持自动重试（最大次数/延迟可配置），可跳过损坏行。
- 错误上下文详细记录，便于定位和恢复。

## 7. 性能优化建议

- 合理设置分片大小与缓冲区，提升大文件处理效率。
- 启用并行处理与缓存，显著提升多核和重复访问场景性能。
- 监控内存与IO，及时调整参数，避免资源瓶颈。

## 8. 扩展性说明

- 新增文件格式：继承`BaseFileHandler`并注册到`FileHandlerFactory`。
- 新增缓存策略：实现`CacheStrategy`接口并用于`CacheManager`。
- 新增监控指标：扩展`StatsCollector`或自定义回调。

---
如需更详细API文档与开发示例，请参考源码注释与各子模块实现。
