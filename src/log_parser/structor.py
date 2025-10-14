import json

class LogEntry:
	def __init__(self, entry_type, level, message, location=None, stacktrace=None, time=None, extra=None):
		self.entry_type = entry_type      # 错误类型/资源类型等
		self.level = level                # Error/Warning/Fatal Error
		self.message = message            # 详细信息
		self.location = location          # 发生位置（如文件、行号、资源路径）
		self.stacktrace = stacktrace      # 堆栈信息
		self.time = time                  # 时间戳
		self.extra = extra or {}          # 其他扩展字段

	def to_dict(self):
		return {
			'entry_type': self.entry_type,
			'level': self.level,
			'message': self.message,
			'location': self.location,
			'stacktrace': self.stacktrace,
			'time': self.time,
			'extra': self.extra
		}

	def to_json(self):
		return json.dumps(self.to_dict(), ensure_ascii=False)

def to_structured_entries(raw_items):
	"""
	将原始提取结果（如analyzer层输出的字典或片段）转为LogEntry对象列表。
	"""
	entries = []
	for item in raw_items:
		entry = LogEntry(
			entry_type=item.get('type'),
			level=item.get('level'),
			message=item.get('message'),
			location=item.get('location'),
			stacktrace=item.get('stacktrace'),
			time=item.get('time'),
			extra=item.get('extra')
		)
		entries.append(entry)
	return entries
