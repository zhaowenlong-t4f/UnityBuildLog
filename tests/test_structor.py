from src.log_parser.structor import LogEntry, to_structured_entries

def test_log_entry_to_dict():
    entry = LogEntry(
        entry_type='CS0246',
        level='Error',
        message='类型或命名空间不存在',
        location='Assets/xxx.cs(10,5)',
        stacktrace='at SomeClass.Method()',
        time='2025-10-14 10:00:00',
        extra={'code': 'CS0246'}
    )
    d = entry.to_dict()
    assert d['entry_type'] == 'CS0246'
    assert d['level'] == 'Error'
    assert d['location'] == 'Assets/xxx.cs(10,5)'
    assert d['stacktrace'] == 'at SomeClass.Method()'
    assert d['extra']['code'] == 'CS0246'


def test_log_entry_to_json():
    entry = LogEntry('TestType', 'Warning', 'msg', time='2025-10-14')
    j = entry.to_json()
    assert 'TestType' in j and 'Warning' in j


def test_to_structured_entries():
    raw = [
        {
            'type': 'CS0246',
            'level': 'Error',
            'message': '类型或命名空间不存在',
            'location': 'Assets/xxx.cs(10,5)',
            'stacktrace': None,
            'time': '2025-10-14 10:00:00',
            'extra': {'code': 'CS0246'}
        },
        {
            'type': 'TextureNotReadable',
            'level': 'Error',
            'message': '资源不可读',
            'location': "Assets/xxx.png",
            'stacktrace': None,
            'time': None,
            'extra': None
        }
    ]
    entries = to_structured_entries(raw)
    assert len(entries) == 2
    assert entries[0].entry_type == 'CS0246'
    assert entries[1].location == 'Assets/xxx.png'
