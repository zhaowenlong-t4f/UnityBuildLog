"""
提取器配置管理器。
"""

class ExtractorConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.load_config()

    def load_config(self):
        import json
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def get_config(self):
        return self.config
