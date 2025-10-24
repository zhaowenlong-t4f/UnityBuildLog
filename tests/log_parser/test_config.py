"""配置系统测试。"""

import unittest
import json
import tempfile
import os
import time
from pathlib import Path
from typing import Dict, Any

from .utils import TestTimeout

from src.config.log_parser.config_validator import ConfigValidator
from src.config.log_parser.config_manager import ConfigManager
from src.config.log_parser.defaults import DEFAULT_CONFIG

class TestConfigValidator(unittest.TestCase):
    """配置验证器测试。"""
    
    def setUp(self):
        """测试准备。"""
        import copy
        self.valid_config = copy.deepcopy(DEFAULT_CONFIG)
        
    def test_valid_config(self):
        """测试有效配置。"""
        # 检查配置是否为预期结构
        self.assertIn("reader", self.valid_config)
        self.assertIsInstance(self.valid_config["reader"], dict)
        self.assertIn("chunk_size", self.valid_config["reader"])
        
        # 验证配置
        errors = ConfigValidator.validate_config(self.valid_config)
        if errors:  # 如果有错误，打印详细信息以帮助调试
            print("\nValidation errors found:")
            for error in errors:
                print(f"- {error}")
            print("\nCurrent config:")
            import json
            print(json.dumps(self.valid_config, indent=2))
            
        self.assertEqual(len(errors), 0)
        
    def test_missing_reader_section(self):
        """测试缺少reader部分。"""
        invalid_config = {}
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("reader" in error for error in errors))
        
    def test_invalid_chunk_size(self):
        """测试无效的chunk_size。"""
        # 测试负数
        import copy
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["reader"]["chunk_size"] = -1
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertTrue(any("chunk_size" in error for error in errors))
        
        # 测试非整数
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["reader"]["chunk_size"] = "invalid"
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertTrue(any("chunk_size" in error for error in errors))
        
    def test_invalid_encoding(self):
        """测试无效的encoding。"""
        import copy
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["reader"]["encoding"] = 123
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertTrue(any("encoding" in error for error in errors))
        
    def test_invalid_extensions(self):
        """测试无效的文件扩展名。"""
        import copy
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["reader"]["supported_extensions"] = ["txt"]  # 缺少点号
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertTrue(any("扩展名" in error for error in errors))

class TestConfigManager(unittest.TestCase):
    """配置管理器测试。"""
    
    def setUp(self):
        """测试准备。"""
        print("\nSetting up TestConfigManager")  # 调试信息
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        print(f"Created temp config path: {self.config_path}")  # 调试信息
        
    def tearDown(self):
        """测试清理。"""
        try:
            if self.config_path.exists():
                self.config_path.unlink()
            os.rmdir(self.temp_dir)
        except:
            pass
            

    @TestTimeout(5)
    def test_load_existing_config(self):
        """测试加载现有配置。"""
        print("\n=== 开始配置加载测试 ===")
        # 创建自定义配置文件
        import copy
        custom_config = copy.deepcopy(DEFAULT_CONFIG)
        custom_config["reader"]["encoding"] = "gbk"
        
        print("创建测试配置文件...")
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)
        
        print("加载配置文件...")    
        manager = ConfigManager(self.config_path, enable_watch=False)
        loaded_config = manager.get_config()
        
        self.assertEqual(loaded_config["reader"]["encoding"], "gbk")
        
    @TestTimeout(10)
    def test_update_config(self):
        """测试更新配置。"""
        print("\n=== 开始配置更新测试 ===")
        
        # 创建初始配置文件
        print("创建初始配置文件...")
        initial_config = {
            "reader": {
                "chunk_size": 4096,
                "encoding": "utf-8"
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_config, f, indent=4)
            
        time.sleep(0.1)  # 确保文件写入完成
        
        print("创建配置管理器...")
        manager = ConfigManager(str(self.config_path), enable_watch=False)
        
        print("准备更新配置...")
        new_config = {
            "reader": {
                "chunk_size": 8192  # 更新块大小
            }
        }
        
        print("执行配置更新...")
        manager.update_config(new_config)
        
        time.sleep(0.1)  # 确保文件写入完成
        
        print("验证配置更新...")
        # 重新加载确认更新
        reloaded_manager = ConfigManager(str(self.config_path), enable_watch=False)
        config = reloaded_manager.get_config()
        self.assertEqual(config["reader"]["chunk_size"], 8192)
        print("测试完成")
        
    @TestTimeout(10)
    def test_merge_with_defaults(self):
        """测试配置合并功能。"""
        print("\n=== 开始配置合并测试 ===")
        
        # 使用最简单的配置进行测试
        test_config = {
            "reader": {
                "chunk_size": 4096,  # 简单的配置值
                "encoding": "utf-8"
            }
        }
        
        # 将测试配置写入文件
        print("创建测试配置文件...")
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=4)
            
        print(f"使用配置文件路径: {self.config_path}")
        time.sleep(0.1)  # 确保文件写入完成
        
        print("创建配置管理器...")
        manager = ConfigManager(str(self.config_path), enable_watch=False)
        
        # 创建简单的更新配置
        print("准备合并配置...")
        update_config = {
            "reader": {
                "encoding": "gbk",  # 只更新编码
            }
        }
        
        print("执行配置合并...")
        merged_config = manager._merge_with_defaults(update_config)
        
        # 验证合并结果
        print("验证合并结果...")
        self.assertEqual(merged_config["reader"]["encoding"], "gbk")  # 新值
        self.assertEqual(merged_config["reader"]["chunk_size"], DEFAULT_CONFIG["reader"]["chunk_size"])  # 默认值
        print("测试完成")
        
    def test_invalid_json(self):
        """测试无效JSON处理。"""
        # 创建无效的JSON配置文件
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("invalid json content")
            
        with self.assertRaises(ValueError) as cm:
            ConfigManager(self.config_path)
            
        self.assertTrue("格式错误" in str(cm.exception))
            
if __name__ == '__main__':
    unittest.main()