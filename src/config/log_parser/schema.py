"""
配置schema定义。
"""

SCHEMA = {
    "reader": {
        "chunk_size": {"type": "int", "min": 1},
        "encoding": {"type": "str"},
        "supported_extensions": {"type": "list", "item_type": "str"},
        "buffer_size": {"type": "int", "min": 1},
        "max_line_length": {"type": "int", "min": 1},
        "compression": {
            "enable_gzip": {"type": "bool"},
            "gzip_buffer_size": {"type": "int", "min": 1}
        },
        "performance": {
            "enable_caching": {"type": "bool"},
            "cache_size": {"type": "int", "min": 1},
            "enable_parallel": {"type": "bool"},
            "max_workers": {"type": "int", "min": 1}
        },
        "error_handling": {
            "max_retries": {"type": "int", "min": 0},
            "retry_delay": {"type": "float", "min": 0},
            "skip_corrupted_lines": {"type": "bool"}
        },
        "monitoring": {
            "enable_stats": {"type": "bool"},
            "stats_interval": {"type": "float", "min": 0.1},
            "memory_threshold": {"type": "float", "min": 0, "max": 1}
        }
    }
}
