"""配置验证器实现。"""

import json
from typing import Dict, Any, List, Union
from pathlib import Path

class ConfigValidator:
    """配置验证器，用于验证配置的正确性。"""

    @staticmethod
    def validate_config(config: Dict[str, Any], strict: bool = False) -> List[str]:
        """验证配置是否有效。

        Args:
            config: 要验证的配置字典
            strict: 是否进行严格验证（验证所有必需字段）

        Returns:
            错误消息列表，如果为空则表示验证通过
        """
        errors: List[str] = []
        print(f"开始配置验证，{'严格模式' if strict else '宽松模式'}")
        
        if not isinstance(config, dict):
            errors.append("配置必须是一个字典")
            return errors

        # 验证reader部分
        if "reader" not in config:
            errors.append("缺少'reader'配置段")
            return errors

        reader_config = config["reader"]
        print(f"验证reader部分: {reader_config}")

        if strict:
            # 严格模式：验证所有必需字段
            ConfigValidator._validate_basic_params(reader_config, errors)
            ConfigValidator._validate_compression_config(reader_config, errors)
            ConfigValidator._validate_performance_config(reader_config, errors)
            ConfigValidator._validate_error_handling_config(reader_config, errors)
            ConfigValidator._validate_monitoring_config(reader_config, errors)
        else:
            # 宽松模式：仅验证提供的字段，但对于提供的字段要进行必要的验证
            for field, config_value in reader_config.items():
                if field == "chunk_size":
                    ConfigValidator._validate_field(
                        reader_config, field, int, lambda x: x > 0,
                        "必须是大于0的整数", errors
                    )
                elif field == "buffer_size":
                    ConfigValidator._validate_field(
                        reader_config, field, int, lambda x: x > 0,
                        "必须是大于0的整数", errors
                    )
                elif field == "encoding":
                    ConfigValidator._validate_field(
                        reader_config, field, str, lambda x: True,
                        "必须是字符串", errors
                    )
                elif field == "supported_extensions":
                    if not isinstance(config_value, list):
                        errors.append("supported_extensions必须是列表")
                    else:
                        for ext in config_value:
                            if not isinstance(ext, str) or not ext.startswith("."):
                                errors.append(f"无效的扩展名格式: {ext}")
                elif field == "max_line_length":
                    ConfigValidator._validate_field(
                        reader_config, field, int, lambda x: x > 0,
                        "必须是大于0的整数", errors
                    )
                elif field == "performance":
                    if not isinstance(config_value, dict):
                        errors.append("performance配置必须是字典")
                    else:
                        for perf_field, perf_value in config_value.items():
                            if perf_field == "cache_size":
                                ConfigValidator._validate_field(
                                    config_value, perf_field, int, lambda x: x > 0,
                                    "必须是大于0的整数", errors
                                )
                            elif perf_field == "enable_caching":
                                ConfigValidator._validate_field(
                                    config_value, perf_field, bool, lambda x: True,
                                    "必须是布尔值", errors
                                )

        print(f"验证完成，发现 {len(errors)} 个错误")
        return errors
        
    @staticmethod
    def _validate_field(
        config: Dict[str, Any],
        field: str,
        expected_type: type,
        validator: callable,
        error_message: str,
        errors: List[str]
    ) -> None:
        """验证单个字段。

        Args:
            config: 配置字典
            field: 字段名
            expected_type: 期望的类型
            validator: 验证函数
            error_message: 错误消息
            errors: 错误列表
        """
        value = config.get(field)
        if not isinstance(value, expected_type):
            errors.append(f"{field}必须是{expected_type.__name__}")
        elif not validator(value):
            errors.append(f"{field}{error_message}")
            

    @staticmethod
    def _validate_basic_params(config: Dict[str, Any], errors: List[str]) -> None:
        """验证基本参数配置。"""
        # chunk_size验证
        if not isinstance(config.get("chunk_size", 0), int):
            errors.append("chunk_size必须是整数")
        elif config.get("chunk_size", 0) <= 0:
            errors.append("chunk_size必须大于0")

        # encoding验证
        if not isinstance(config.get("encoding", ""), str):
            errors.append("encoding必须是字符串")

        # supported_extensions验证
        extensions = config.get("supported_extensions", [])
        if not isinstance(extensions, list):
            errors.append("supported_extensions必须是列表")
        else:
            for ext in extensions:
                if not isinstance(ext, str) or not ext.startswith("."):
                    errors.append(f"无效的扩展名格式: {ext}")

        # buffer_size验证
        if not isinstance(config.get("buffer_size", 0), int):
            errors.append("buffer_size必须是整数")
        elif config.get("buffer_size", 0) <= 0:
            errors.append("buffer_size必须大于0")
            
        # max_line_length验证
        if not isinstance(config.get("max_line_length", 0), int):
            errors.append("max_line_length必须是整数")
        elif config.get("max_line_length", 0) <= 0:
            errors.append("max_line_length必须大于0")

    @staticmethod
    def _validate_compression_config(config: Dict[str, Any], errors: List[str]) -> None:
        """验证压缩相关配置。"""
        compression = config.get("compression", {})
        if not isinstance(compression, dict):
            errors.append("compression配置必须是字典")
            return

        if not isinstance(compression.get("enable_gzip", True), bool):
            errors.append("enable_gzip必须是布尔值")

        if not isinstance(compression.get("gzip_buffer_size", 0), int):
            errors.append("gzip_buffer_size必须是整数")
        elif compression.get("gzip_buffer_size", 0) <= 0:
            errors.append("gzip_buffer_size必须大于0")

    @staticmethod
    def _validate_performance_config(config: Dict[str, Any], errors: List[str]) -> None:
        """验证性能相关配置。"""
        perf = config.get("performance", {})
        if not isinstance(perf, dict):
            errors.append("performance配置必须是字典")
            return

        if not isinstance(perf.get("enable_caching", True), bool):
            errors.append("enable_caching必须是布尔值")

        if not isinstance(perf.get("cache_size", 0), int):
            errors.append("cache_size必须是整数")
        elif perf.get("cache_size", 0) <= 0:
            errors.append("cache_size必须大于0")

        if not isinstance(perf.get("enable_parallel", False), bool):
            errors.append("enable_parallel必须是布尔值")

        if not isinstance(perf.get("max_workers", 0), int):
            errors.append("max_workers必须是整数")
        elif perf.get("max_workers", 0) <= 0:
            errors.append("max_workers必须大于0")

    @staticmethod
    def _validate_error_handling_config(config: Dict[str, Any], errors: List[str]) -> None:
        """验证错误处理相关配置。"""
        error_handling = config.get("error_handling", {})
        if not isinstance(error_handling, dict):
            errors.append("error_handling配置必须是字典")
            return

        if not isinstance(error_handling.get("max_retries", 0), int):
            errors.append("max_retries必须是整数")
        elif error_handling.get("max_retries", 0) < 0:
            errors.append("max_retries不能为负数")

        if not isinstance(error_handling.get("retry_delay", 0), (int, float)):
            errors.append("retry_delay必须是数字")
        elif error_handling.get("retry_delay", 0) < 0:
            errors.append("retry_delay不能为负数")

        if not isinstance(error_handling.get("skip_corrupted_lines", True), bool):
            errors.append("skip_corrupted_lines必须是布尔值")

    @staticmethod
    def _validate_monitoring_config(config: Dict[str, Any], errors: List[str]) -> None:
        """验证监控相关配置。"""
        monitoring = config.get("monitoring", {})
        if not isinstance(monitoring, dict):
            errors.append("monitoring配置必须是字典")
            return

        if not isinstance(monitoring.get("enable_stats", True), bool):
            errors.append("enable_stats必须是布尔值")

        if not isinstance(monitoring.get("stats_interval", 0), (int, float)):
            errors.append("stats_interval必须是数字")
        elif monitoring.get("stats_interval", 0) <= 0:
            errors.append("stats_interval必须大于0")

        if not isinstance(monitoring.get("memory_threshold", 0), float):
            errors.append("memory_threshold必须是浮点数")
        elif not 0 < monitoring.get("memory_threshold", 0) <= 1:
            errors.append("memory_threshold必须在0到1之间")