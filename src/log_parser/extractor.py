
# 日志清洗：去除空行、分隔符、特殊字符

def clean_lines(lines, filter_prefixes=None, remove_empty=None):
	"""
	日志清洗，过滤指定前缀和空行，规则可配置。
	"""
	from config import app_config
	if filter_prefixes is None:
		filter_prefixes = app_config.CLEAN_FILTER_PREFIXES
	if remove_empty is None:
		remove_empty = app_config.CLEAN_REMOVE_EMPTY
	result = []
	for line in lines:
		line_strip = line.strip()
		if remove_empty and not line_strip:
			continue
		if any(line_strip.startswith(prefix) for prefix in filter_prefixes):
			continue
		result.append(line_strip)
	return result

# 日志分段：按关键字分割为片段

from config import app_config


def segment_by_keyword(lines, keywords=None):
	"""
	按配置关键字分段，默认从app_config读取SEGMENT_KEYWORDS，忽略大小写。
	"""
	if keywords is None:
		keywords = app_config.SEGMENT_KEYWORDS
	keywords_lower = [kw.lower() for kw in keywords]
	segments = []
	current = []
	for line in lines:
		line_lower = line.lower()
		if any(kw in line_lower for kw in keywords_lower):
			if current:
				segments.append(current)
			current = [line]
		else:
			current.append(line)
	if current:
		segments.append(current)
	return segments

# 日志去噪：去除重复片段
def denoise_segments(segments):
	unique = []
	seen = set()
	for seg in segments:
		key = ''.join(seg)
		if key not in seen:
			unique.append(seg)
			seen.add(key)
	return unique

# 环境信息提取
def extract_env_info(lines):
	"""
	从日志行中提取环境相关信息，如Unity版本、平台、打包时间等。
	"""
	env = {
		'unity_version': None,
		'platform': None,
		'build_time': None
	}
	for line in lines:
		if 'Unity Version:' in line:
			env['unity_version'] = line.split(':', 1)[-1].strip()
		elif 'Platform:' in line:
			env['platform'] = line.split(':', 1)[-1].strip()
		elif 'Build Time:' in line:
			env['build_time'] = line.split(':', 1)[-1].strip()
	return env

# 可扩展：增加更多通用预处理函数，如extract_stacktrace, extract_resource_paths等
