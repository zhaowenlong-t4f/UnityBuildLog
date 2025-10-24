"""Pytest configuration file."""

import os
import sys

# 添加源代码目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))