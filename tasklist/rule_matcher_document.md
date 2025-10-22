# Unity Rule Matcher 系统设计文档

## 1. 系统概述
Rule Matcher是Unity日志分析系统的规则匹配引擎，负责执行error_rules定义的规则，识别和分析日志中的错误模式。它提供高效的正则表达式匹配、智能的权重计算和复杂的冲突处理机制。

## 2. 系统架构

### 2.1 目录结构
```
analyzer/
└── rule_matcher/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── matcher_engine.py       # 核心匹配引擎
    │   ├── weight_calculator.py    # 权重计算器
    │   └── conflict_resolver.py    # 冲突处理器
    ├── engines/
    │   ├── __init__.py
    │   ├── regex_engine.py        # 正则表达式引擎
    │   ├── multi_line_engine.py   # 多行匹配引擎
    │   └── correlation_engine.py   # 关联匹配引擎
    ├── processors/
    │   ├── __init__.py
    │   ├── context_processor.py    # 上下文处理器
    │   ├── segment_processor.py    # 片段处理器
    │   └── result_processor.py     # 结果处理器
    └── utils/
        ├── __init__.py
        ├── regex_optimizer.py      # 正则优化工具
        ├── pattern_compiler.py     # 模式编译器
        └── cache_manager.py        # 缓存管理器
```

## 3. 核心组件

### 3.1 匹配引擎（MatcherEngine）
```python
class MatcherEngine:
    """核心匹配引擎"""
    
    def __init__(self, rule_manager):
        self.rule_manager = rule_manager
        self.regex_engine = RegexEngine()
        self.multi_line_engine = MultiLineEngine()
        self.correlation_engine = CorrelationEngine()
        self.pattern_compiler = PatternCompiler()
        
    async def match(self, log_content: LogContent) -> List[MatchResult]:
        """执行规则匹配"""
        results = []
        
        # 1. 编译和优化模式
        compiled_patterns = self.pattern_compiler.compile_rules(
            self.rule_manager.get_active_rules())
            
        # 2. 执行不同类型的匹配
        single_line_matches = await self.regex_engine.match(
            log_content, compiled_patterns.single_line_patterns)
            
        multi_line_matches = await self.multi_line_engine.match(
            log_content, compiled_patterns.multi_line_patterns)
            
        correlation_matches = await self.correlation_engine.match(
            log_content, compiled_patterns.correlation_patterns)
            
        # 3. 合并结果
        results.extend(single_line_matches)
        results.extend(multi_line_matches)
        results.extend(correlation_matches)
        
        # 4. 处理冲突
        resolved_results = self.conflict_resolver.resolve(results)
        
        return resolved_results
```

### 3.2 正则表达式引擎（RegexEngine）
```python
class RegexEngine:
    """正则表达式匹配引擎"""
    
    def __init__(self):
        self.optimizer = RegexOptimizer()
        self.cache = PatternCache()
        
    async def match(self, content: str, patterns: List[CompiledPattern]) -> List[Match]:
        """执行正则匹配"""
        matches = []
        
        # 1. 应用预过滤
        if not self._pre_filter(content):
            return matches
            
        # 2. 并行匹配
        async with ProcessPoolExecutor() as executor:
            tasks = [
                self._match_pattern(content, pattern)
                for pattern in patterns
            ]
            matches = await asyncio.gather(*tasks)
            
        return self._post_process(matches)
```

### 3.3 权重计算器（WeightCalculator）
```python
class WeightCalculator:
    """规则权重计算器"""
    
    def calculate_weight(self, match: Match, context: MatchContext) -> float:
        """计算匹配结果的权重"""
        base_weight = match.rule.weight
        
        # 1. 上下文相关性
        context_score = self._calculate_context_relevance(match, context)
        
        # 2. 模式完整性
        pattern_score = self._calculate_pattern_completeness(match)
        
        # 3. 历史准确性
        history_score = self._calculate_historical_accuracy(match.rule)
        
        # 4. 组合计算
        final_weight = self._combine_scores(
            base_weight,
            context_score,
            pattern_score,
            history_score
        )
        
        return final_weight
```

### 3.4 冲突处理器（ConflictResolver）
```python
class ConflictResolver:
    """规则冲突处理器"""
    
    def resolve_conflicts(self, matches: List[Match]) -> List[Match]:
        """处理匹配结果中的冲突"""
        
        # 1. 分组冲突
        grouped_conflicts = self._group_conflicts(matches)
        
        # 2. 应用解决策略
        for group in grouped_conflicts:
            if self._is_mergeable(group):
                resolved = self._merge_matches(group)
            else:
                resolved = self._select_best_match(group)
            
            resolved_matches.extend(resolved)
        
        return resolved_matches
```

## 4. 关键功能实现

### 4.1 多行匹配处理
```python
class MultiLineProcessor:
    """多行匹配处理器"""
    
    def process(self, lines: List[str], rule: MultiLineRule) -> Optional[Match]:
        """处理多行匹配"""
        
        # 1. 初始化匹配状态
        state = MatchState()
        
        # 2. 逐行扫描
        for i, line in enumerate(lines):
            # 检查是否匹配规则的任何部分
            for segment in rule.segments:
                if self._matches_segment(line, segment):
                    state.add_match(segment, i, line)
                    
            # 检查是否完成所有必需匹配
            if state.is_complete():
                # 验证匹配之间的距离约束
                if self._validate_distances(state, rule):
                    return self._create_match(state, rule)
                    
            # 检查是否超过最大扫描范围
            if i - state.first_match_line > rule.max_scan_lines:
                state.reset()
                
        return None
```

### 4.2 关联分析处理
```python
class CorrelationProcessor:
    """关联分析处理器"""
    
    def process(self, segments: List[LogSegment], rule: CorrelationRule) -> List[Match]:
        """处理段落关联"""
        
        # 1. 构建关联图
        graph = self._build_correlation_graph(segments)
        
        # 2. 查找关联链
        chains = []
        for segment in segments:
            if self._is_primary(segment, rule):
                chain = self._find_correlation_chain(segment, graph, rule)
                if chain:
                    chains.append(chain)
                    
        # 3. 验证关联条件
        valid_chains = [
            chain for chain in chains
            if self._validate_correlation(chain, rule)
        ]
        
        return self._convert_to_matches(valid_chains, rule)
```

### 4.3 权重计算示例
```python
def calculate_pattern_weight(match: Match, context: Context) -> float:
    """计算模式权重"""
    base_weight = match.rule.base_weight
    factors = [
        # 1. 匹配完整性（所有必需部分都匹配）
        MatchCompleteness(match).score() * 0.3,
        
        # 2. 上下文相关性（与周围内容的关联度）
        ContextRelevance(match, context).score() * 0.2,
        
        # 3. 特异性分数（模式的独特程度）
        PatternSpecificity(match.rule).score() * 0.2,
        
        # 4. 历史准确率（基于反馈的准确性）
        HistoricalAccuracy(match.rule).score() * 0.2,
        
        # 5. 规则优先级（预定义的优先级）
        RulePriority(match.rule).score() * 0.1
    ]
    
    return base_weight * reduce(lambda x, y: x * y, factors)
```

## 5. 优化机制

### 5.1 性能优化
1. 正则表达式优化
   - 预编译模式
   - 模式简化
   - 快速预过滤

2. 并行处理
   - 多进程匹配
   - 分片处理
   - 任务调度

3. 缓存策略
   - 模式缓存
   - 结果缓存
   - 统计缓存

### 5.2 内存优化
1. 流式处理
   - 增量扫描
   - 内存限制
   - 垃圾回收

2. 数据结构优化
   - 紧凑表示
   - 引用计数
   - 池化复用

## 6. 扩展能力

### 6.1 自定义匹配器
```python
class CustomMatcher(BaseMatcher):
    """自定义匹配器接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    async def match(self, content: str) -> List[Match]:
        """实现自定义匹配逻辑"""
        pass
        
    def calculate_weight(self, match: Match) -> float:
        """实现自定义权重计算"""
        pass
```

### 6.2 规则转换器
```python
class RuleConverter:
    """规则格式转换器"""
    
    def convert(self, external_rule: Any) -> Rule:
        """转换外部规则格式"""
        pass
        
    def export(self, rule: Rule, format: str) -> Any:
        """导出为外部格式"""
        pass
```

## 7. 监控指标

### 7.1 性能指标
- 匹配时间统计
- 内存使用监控
- 缓存命中率

### 7.2 质量指标
- 规则匹配率
- 冲突发生率
- 权重分布统计

## 8. 错误处理

### 8.1 异常类型
- 模式编译错误
- 匹配超时异常
- 资源超限异常

### 8.2 恢复策略
1. 自动重试
2. 降级处理
3. 部分结果保存

## 9. 测试策略

### 9.1 单元测试
- 模式匹配测试
- 权重计算测试
- 冲突处理测试

### 9.2 性能测试
- 大规模规则测试
- 并发处理测试
- 内存压力测试

## 10. 使用示例

### 10.1 基本使用
```python
# 创建匹配引擎
matcher = RuleMatcher(rules)

# 执行匹配
results = await matcher.match(log_content)

# 处理结果
for match in results:
    print(f"Rule: {match.rule.id}")
    print(f"Content: {match.content}")
    print(f"Weight: {match.weight}")
```

### 10.2 自定义处理
```python
# 注册自定义匹配器
matcher.register_matcher("custom", CustomMatcher(config))

# 添加结果处理器
matcher.add_processor(CustomProcessor())

# 设置冲突处理策略
matcher.set_conflict_strategy(CustomStrategy())
```

## 11. 配置参数

### 11.1 匹配配置
```json
{
    "matcher": {
        "timeout": 30,
        "max_matches": 1000,
        "parallel_threads": 4
    },
    "regex": {
        "timeout": 5,
        "max_recursion": 100
    },
    "multi_line": {
        "max_lines": 100,
        "context_size": 5
    }
}
```

### 11.2 优化配置
```json
{
    "optimization": {
        "cache_size": "100MB",
        "pattern_optimization": true,
        "parallel_matching": true
    },
    "resources": {
        "max_memory": "1GB",
        "max_cpu_percent": 70
    }
}
```