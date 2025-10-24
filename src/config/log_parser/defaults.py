"""默认配置值定义。"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "reader": {
        "chunk_size": 8388608,          # 分片大小（8MB）
        "encoding": "utf-8",            # 文件编码
        "supported_extensions": [".txt", ".log", ".gz"],
        "buffer_size": 4096,            # 缓冲区大小（4KB）
        "max_line_length": 1048576,     # 最大行长度（1MB）
        "compression": {
            "enable_gzip": True,
            "gzip_buffer_size": 65536    # GZIP缓冲区（64KB）
        },
        "performance": {
            "enable_caching": True,
            "cache_size": 104857600,     # 缓存限制（100MB）
            "enable_parallel": False,
            "max_workers": 4
        },
        "error_handling": {
            "max_retries": 3,
            "retry_delay": 1.0,
            "skip_corrupted_lines": True
        },
        "monitoring": {
            "enable_stats": True,
            "stats_interval": 5.0,
            "memory_threshold": 0.8
        }
    }
}