#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""测试LogExtractor的功能，用于大文件日志处理"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.log_parser.reader import LogReader
from src.log_parser.extractor import LogExtractor

def main():
    # 设置路径
    project_root = Path(__file__).parent.parent
    sample_log = project_root / 'samples' / 'build_logs' / 'build_log_1.txt'
    config_dir = project_root / 'config'
    result_dir = project_root / 'samples' / 'results'
    
    # 确保结果目录存在
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取日志文件
    reader = LogReader(
        filepath=str(sample_log),
        config_path=str(config_dir / 'log_parser_config.json')
    )
    
    # 读取所有行并合并
    log_content = '\n'.join(reader.read_lines())
    
    # 处理日志
    extractor = LogExtractor(config_dir=config_dir)
    processed_segments = extractor.process_logs(log_content)
    
    # 输出处理结果
    output_file = result_dir / 'processed_log_1.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for segment in processed_segments:
            # 写入段落元数据
            f.write(f"=== 段落 (行 {segment['metadata']['start_line']} - {segment['metadata']['end_line']}) ===\n")
            # 写入清理后的内容
            for line in segment['lines']:
                if line:  # 只写入非空行
                    f.write(f"{line}\n")
            f.write('\n')  # 段落之间加空行

if __name__ == '__main__':
    main()