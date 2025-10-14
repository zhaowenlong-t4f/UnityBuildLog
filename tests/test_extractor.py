"""Unity构建日志提取器测试"""

from pathlib import Path
from src.log_parser.extractor import LineProcessor

def get_test_data_path():
    """获取测试数据目录"""
    return Path(__file__).parent.parent / "samples"

def test_process_build_log():
    """测试处理Unity构建日志文件"""
    # 准备路径
    test_data_path = get_test_data_path()
    input_file = test_data_path / "build_logs/build_log_1.txt"
    output_file = test_data_path / "results/processed_log_1.txt"

    # 确保测试数据目录存在
    test_data_path.mkdir(exist_ok=True)
    
    # 创建LineProcessor实例
    config_path = Path("config/line_processor.json")
    processor = LineProcessor(config_path)
    
    # 处理日志文件
    processed_lines = []
    line_number = 1
    
    for line in input_file.read_text(encoding='utf-8').splitlines():
        result = processor.process_line(line, line_number)
        if result is not None:
            processed_lines.append(result.cleaned_content)
        line_number += 1
    
    # 写入处理后的结果
    output_file.write_text('\n'.join(processed_lines), encoding='utf-8')
    
    # 基本验证
    assert output_file.exists(), "输出文件应该被创建"
    assert output_file.stat().st_size > 0, "输出文件不应该为空"
