"""Unity 日志读取器（LogReader）的单元测试

此测试模块全面测试 LogReader 类的所有功能，包括：
1. 基本文件操作（读取、验证）
2. 编码处理（自动检测、多编码支持）
3. 内容读取方式（按行、按块、过滤）
4. 错误处理（文件不存在、格式无效、编码错误）
5. 性能相关（大文件处理）
"""

import os
import json
import pytest
from src.log_parser.reader import LogReader

# 获取默认配置文件路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'log_parser_config.json')

def load_test_config():
    """加载测试配置"""
    with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

# 测试用的Unity日志样本
SAMPLE_UNITY_LOG = """[Unity] Starting Build
[UNITYVERSION]: 2020.3.25f1
Running as SYSTEM
[Unity] Project: TestProject
UnityEditor starting compiler...
[Unity] Error: Failed to build Player
[Unity] Error Details:
[Unity]   Assets/Scripts/Game.cs(10,5): error CS0246: The type or namespace name 'UnityEngine' could not be found
"""

SAMPLE_UNITY_LOG_WITH_STACK = """[Unity] Error
Running as SYSTEM
[Unity] Stack trace:
UnityEditor.BuildPlayer.BuildPlayer (UnityEditor.BuildPlayerOptions options) [0x002da] in <d6cd0ef5f0ef4c238ebde15d775e78c2>:0 
UnityEditor.BuildPlayerWindow+BuildMethodHelper.BuildPlayer (UnityEditor.BuildPlayerOptions options) [0x00002] in <d6cd0ef5f0ef4c238ebde15d775e78c2>:0 
"""

class TestLogReaderBasics:
    """测试LogReader的基本功能"""
    
    def test_initialization(self, tmp_path):
        """测试初始化参数"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        config = load_test_config()
        
        # 测试默认参数（使用配置文件）
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        assert reader.chunk_size == config['file_reading']['default_chunk_size']
        assert reader.filepath == str(log_file)
        assert reader.encoding is not None
        
        # 测试自定义参数（覆盖配置文件）
        custom_chunk_size = 4096
        custom_encoding = 'utf-8'
        reader = LogReader(
            str(log_file), 
            config_path=DEFAULT_CONFIG_PATH,
            encoding=custom_encoding,
            chunk_size=custom_chunk_size
        )
        assert reader.chunk_size == custom_chunk_size
        assert reader.encoding == custom_encoding
        
    def test_config_loading(self, tmp_path):
        """测试配置文件加载"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        
        # 测试使用默认配置文件
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        config = load_test_config()
        assert reader.config == config
        
        # 测试配置文件不存在的情况
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            LogReader(str(log_file), config_path="nonexistent_config.json")

    def test_file_not_found(self):
        """测试文件不存在的错误处理"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            LogReader("nonexistent.log")
            
    def test_invalid_chunk_size(self, tmp_path):
        """测试无效的块大小参数"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        
        with pytest.raises(ValueError, match="块大小必须大于0"):
            LogReader(str(log_file), chunk_size=0)
        
        with pytest.raises(ValueError, match="块大小必须大于0"):
            LogReader(str(log_file), chunk_size=-1)

class TestLogReaderContent:
    """测试日志内容读取功能"""
    
    def test_read_lines(self, tmp_path):
        """测试按行读取"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        reader = LogReader(str(log_file))
        
        lines = list(reader.read_lines())
        assert len(lines) == 8  # 更新为新的行数
        assert lines[0] == "[Unity] Starting Build"
        assert "error CS0246" in lines[-1]
        assert all(not line.endswith('\n') for line in lines)  # 确保没有末尾换行符
        
    def test_read_chunks(self, tmp_path):
        """测试分块读取"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        reader = LogReader(str(log_file), chunk_size=50)
        
        # 测试内容完整性
        chunks = list(reader.read_chunks())
        assert ''.join(chunks) == SAMPLE_UNITY_LOG
        
        # 测试块大小控制
        for chunk in chunks[:-1]:  # 除了最后一块
            assert len(chunk) <= 50
            
    def test_filter_lines(self, tmp_path):
        """测试行过滤功能"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        reader = LogReader(str(log_file))
        
        # 测试错误过滤
        error_lines = list(reader.filter_lines("Error"))
        assert len(error_lines) == 2
        assert all("Error" in line for line in error_lines)
        
        # 测试无关键字的情况
        all_lines = list(reader.filter_lines())
        assert len(all_lines) == len(SAMPLE_UNITY_LOG.splitlines())
        
        # 测试不存在的关键字
        no_lines = list(reader.filter_lines("NonExistent"))
        assert len(no_lines) == 0

class TestLogReaderEncoding:
    """测试编码处理功能"""
    
    def test_detect_encoding_utf8(self, tmp_path):
        """测试UTF-8编码检测"""
        log_file = tmp_path / "test_utf8.log"
        log_file.write_text(SAMPLE_UNITY_LOG, encoding="utf-8")
        config = load_test_config()
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        enc = reader.detect_encoding(str(log_file))
        assert enc.lower() in config['file_reading']['supported_encodings']
        
    def test_detect_encoding_gbk(self, tmp_path):
        """测试GBK编码检测"""
        log_file = tmp_path / "test_gbk.log"
        content = "[Unity] 编译错误：资源重复\n[Unity] 位置：Assets/测试/场景.unity"
        log_file.write_text(content, encoding="gbk")
        config = load_test_config()
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        enc = reader.detect_encoding(str(log_file))
        assert enc.lower() in config['file_reading']['supported_encodings']
        
    def test_unsupported_encoding(self, tmp_path):
        """测试不支持的编码"""
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        config = load_test_config()
        invalid_encoding = "invalid-encoding"
        
        with pytest.raises(ValueError, match=f"不支持的编码格式"):
            LogReader(str(log_file), 
                     config_path=DEFAULT_CONFIG_PATH, 
                     encoding=invalid_encoding)
        
    def test_detect_encoding_empty_file(self, tmp_path):
        """测试空文件的编码检测"""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")
        config = load_test_config()
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        enc = reader.detect_encoding(str(log_file))
        assert enc.lower() == config['file_reading']['default_encoding']  # 使用配置的默认编码

class TestLogValidation:
    """测试日志格式验证功能"""
    
    def test_valid_unity_log(self, tmp_path):
        """测试有效的Unity日志"""
        log_file = tmp_path / "valid.log"
        log_file.write_text(SAMPLE_UNITY_LOG)
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        assert reader.validate_log_format() == True
        
    def test_invalid_log(self, tmp_path):
        """测试无效的日志格式"""
        log_file = tmp_path / "invalid.log"
        log_file.write_text("This is not a Unity log file.")
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        with pytest.raises(ValueError, match="无效的 Unity 日志格式"):
            reader.validate_log_format()
            
    def test_empty_log(self, tmp_path):
        """测试空日志文件"""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        with pytest.raises(ValueError, match="无效的 Unity 日志格式"):
            reader.validate_log_format()
            
    def test_validation_marker_match(self, tmp_path):
        """测试验证标记匹配"""
        config = load_test_config()
        markers = config['log_validation']['markers']
        log_content = "\n".join(f"[Unity] Some content with {marker}" for marker in markers)
        
        log_file = tmp_path / "markers.log"
        log_file.write_text(log_content)
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        assert reader.validate_log_format() == True
        
    def test_minimum_marker_matches(self, tmp_path):
        """测试最小标记匹配数"""
        config = load_test_config()
        min_matches = config['log_validation']['min_matches']
        markers = config['log_validation']['markers'][:min_matches-1]  # 使用比最小要求少一个的标记
        log_content = "\n".join(f"[Unity] Content with {marker}" for marker in markers)
        
        log_file = tmp_path / "min_matches.log"
        log_file.write_text(log_content)
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        with pytest.raises(ValueError, match="无效的 Unity 日志格式"):
            reader.validate_log_format()

class TestPerformance:
    """测试性能相关功能"""
    
    def test_large_file_handling(self, tmp_path):
        """测试大文件处理"""
        log_file = tmp_path / "large.log"
        config = load_test_config()
        
        # 创建一个包含标记和超过默认块大小的文件
        markers = config['log_validation']['markers']
        header = "".join(f"{marker}\n" for marker in markers)
        large_content = header + ("[Unity] Some content\n" * 100000)
        log_file.write_text(large_content, encoding="utf-8")
        
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        
        # 测试按行读取
        expected_line_count = len(markers) + 100000  # 标记行数 + 内容行数
        line_count = sum(1 for _ in reader.read_lines())
        assert line_count == expected_line_count
        
        # 测试分块读取
        chunk_content = ''.join(reader.read_chunks())
        assert len(chunk_content.splitlines()) == expected_line_count
        
    def test_memory_efficiency(self, tmp_path):
        """测试内存使用效率（验证是否真正实现了生成器模式）"""
        log_file = tmp_path / "large.log"
        config = load_test_config()
        
        # 创建一个包含标记和非常大的文件
        markers = config['log_validation']['markers']
        header = "".join(f"{marker}\n" for marker in markers)
        large_content = header + ("[Unity] Some content\n" * 1000000)  # 创建一个非常大的文件
        log_file.write_text(large_content, encoding="utf-8")
        
        reader = LogReader(str(log_file), config_path=DEFAULT_CONFIG_PATH)
        lines_iter = reader.read_lines()
        
        # 验证是否返回生成器
        assert hasattr(lines_iter, '__iter__')
        assert hasattr(lines_iter, '__next__')
        
        # 读取前10行就停止，验证是否支持提前退出
        for i, line in enumerate(lines_iter):
            if i >= 10:
                break
        assert i == 10  # 确认只读取了10行就退出了