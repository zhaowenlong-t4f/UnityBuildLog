# 日志清洗规则配置
CLEAN_FILTER_PREFIXES = [
	'====',
    '---',
	# 可添加更多需过滤的前缀，如 '---', '[INFO]'
]
CLEAN_REMOVE_EMPTY = True
# 日志分段关键字配置，可根据实际需求调整
SEGMENT_KEYWORDS = [
	"Error",
	"Warning",
	"Stacktrace",
    "Failed",
    "Exception"
]
# 错误规则文件路径列表，可按需扩展
ERROR_RULE_PATHS = [
	'./config/error_rules.json',
	# 可添加更多规则文件路径，如 './config/external_rules.json'
]
