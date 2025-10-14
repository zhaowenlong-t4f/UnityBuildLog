import pytest
from src.log_parser import extractor

def test_clean_lines_basic():
    lines = [
        '',
        '==== separator',
        'Error: something',
        '   Info: ok   ',
        '====',
        'Warning: test',
        '   '
    ]
    result = extractor.clean_lines(lines)
    assert result == ['Error: something', 'Info: ok', 'Warning: test']

def test_clean_lines_custom_prefix():
    lines = ['--- skip', 'Error: a', 'Warning: b']
    result = extractor.clean_lines(lines, filter_prefixes=['---'])
    assert result == ['Error: a', 'Warning: b']

def test_segment_by_keyword_default():
    lines = [
        'Error: something',
        'Stacktrace: ...',
        'Info: ok',
        'Warning: test',
        'Other line'
    ]
    segments = extractor.segment_by_keyword(lines)
    assert len(segments) == 3
    assert segments[0][0].startswith('Error')
    assert segments[1][0].startswith('Stacktrace') or segments[1][0].startswith('Warning')

def test_segment_by_keyword_case_insensitive():
    lines = ['error: a', 'WARNING: b', 'StackTrace: c']
    segments = extractor.segment_by_keyword(lines)
    assert len(segments) == 3

def test_denoise_segments():
    segments = [
        ['Error: a', 'Stacktrace: ...'],
        ['Error: a', 'Stacktrace: ...'],
        ['Warning: b']
    ]
    unique = extractor.denoise_segments(segments)
    assert len(unique) == 2

def test_extract_env_info():
    lines = [
        'Unity Version: 2021.3.0f1',
        'Platform: Windows',
        'Build Time: 2025-10-14 10:00:00',
        'Other line'
    ]
    env = extractor.extract_env_info(lines)
    assert env['unity_version'] == '2021.3.0f1'
    assert env['platform'] == 'Windows'
    assert env['build_time'] == '2025-10-14 10:00:00'
