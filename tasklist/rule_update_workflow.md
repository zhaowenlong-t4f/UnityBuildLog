# Unity 错误规则更新工作流程

## 1. 规则更新总体流程

规则更新流程分为四个主要阶段：
1. 规则提取和分析
2. 规则构建
3. 规则验证
4. 规则部署

## 2. 详细流程说明

### 2.1 规则提取和分析阶段

#### 2.1.1 原始日志预处理
- 分割日志段落
- 检测错误级别
- 提取堆栈跟踪
- 提取上下文信息

```python
class LogPreprocessor:
    def process_raw_log(self, raw_log: str) -> Dict[str, Any]:
        """处理原始日志，提取关键信息"""
        return {
            'log_segments': self._split_log_segments(raw_log),
            'error_level': self._detect_error_level(raw_log),
            'stack_trace': self._extract_stack_trace(raw_log),
            'context_info': self._extract_context(raw_log)
        }
```

#### 2.1.2 特征分析
- 识别关键模式
- 查找固定部分
- 识别变量部分
- 分析上下文依赖

```python
class PatternAnalyzer:
    def analyze_pattern(self, processed_log: Dict[str, Any]) -> Dict[str, Any]:
        """分析日志特征"""
        return {
            'key_patterns': self._identify_key_patterns(processed_log),
            'constant_parts': self._find_constants(processed_log),
            'variable_parts': self._identify_variables(processed_log),
            'context_dependencies': self._analyze_context(processed_log)
        }
```

### 2.2 规则构建阶段

#### 2.2.1 规则模板选择
根据日志特征选择合适的规则模板：
- 单行规则模板
- 多行规则模板
- 关联规则模板

```python
class RuleBuilder:
    def select_rule_template(self, analysis_result: Dict[str, Any]) -> str:
        """根据分析结果选择合适的规则模板"""
        if analysis_result['is_multi_line']:
            return 'multi_line_template.json'
        elif analysis_result['has_correlation']:
            return 'correlation_template.json'
        else:
            return 'rule_template.json'
```

#### 2.2.2 规则构建示例
```json
{
    "id": "ERR_UNITY_NEW_001",
    "name": "新发现的Unity错误类型",
    "type": "multi_line",
    "description": "描述错误的具体原因和影响",
    "severity": "error",
    "category": "compilation",
    "segments": [
        {
            "order": 1,
            "pattern": "Error occurred while .*",
            "capture_groups": ["error_context"],
            "required": true
        },
        {
            "order": 2,
            "pattern": "at .*\\(.*:.*\\)",
            "capture_groups": ["stack_location"],
            "required": false
        }
    ],
    "metadata": {
        "created_at": "2025-10-22",
        "author": "规则创建者",
        "version": "1.0.0"
    }
}
```

### 2.3 规则验证阶段

#### 2.3.1 基础验证
- Schema 验证
- 正则表达式验证
- 规则冲突检查
- 测试用例验证

```python
class RuleValidator:
    def validate_new_rule(self, rule: Dict[str, Any], 
                         test_logs: List[str]) -> ValidationResult:
        """验证新规则的有效性"""
        # 1. Schema 验证
        self._validate_schema(rule)
        
        # 2. 正则表达式验证
        self._validate_regex_patterns(rule)
        
        # 3. 规则冲突检查
        conflicts = self._check_rule_conflicts(rule)
        
        # 4. 测试用例验证
        test_results = self._run_test_cases(rule, test_logs)
        
        return ValidationResult(
            schema_valid=True,
            regex_valid=True,
            conflicts=conflicts,
            test_results=test_results
        )
```

#### 2.3.2 性能测试
- 匹配时间测试
- 内存使用测试
- 误报率计算

```python
class PerformanceTester:
    def test_rule_performance(self, rule: Dict[str, Any], 
                            sample_logs: List[str]) -> PerformanceMetrics:
        """测试规则的性能表现"""
        return {
            'avg_match_time': self._measure_match_time(rule, sample_logs),
            'memory_usage': self._measure_memory_usage(rule, sample_logs),
            'false_positive_rate': self._calculate_false_positives(rule, sample_logs)
        }
```

### 2.4 规则部署阶段

#### 2.4.1 规则文件更新
- 确定目标文件
- 创建规则备份
- 更新规则文件
- 更新规则索引

```python
class RuleDeployer:
    def deploy_rule(self, rule: Dict[str, Any], 
                   category: str) -> bool:
        """部署新规则到规则库"""
        # 1. 确定目标文件
        target_file = f"config/error_rules/categories/{category}/{self._get_rule_file(rule)}"
        
        # 2. 创建备份
        self._backup_rules(target_file)
        
        # 3. 更新规则文件
        self._update_rule_file(target_file, rule)
        
        # 4. 更新索引
        self._update_rule_index(rule)
        
        return True
```

#### 2.4.2 部署验证
- 检查文件存在性
- 验证规则加载
- 执行冒烟测试

```python
class DeploymentVerifier:
    def verify_deployment(self, rule_id: str) -> bool:
        """验证规则部署是否成功"""
        # 1. 检查规则文件存在性
        self._check_rule_file_exists()
        
        # 2. 验证规则可被加载
        self._verify_rule_loading()
        
        # 3. 执行简单测试
        self._run_smoke_test()
        
        return True
```

## 3. 实际操作示例

### 3.1 错误信息示例
```plaintext
Error: IL2CPP error occurred while processing method 'void Example.Method()'
at (wrapper managed-to-native) System.Object:Internal_FromJniHandle
Stack trace:
  at UnityEngine.AndroidJNI.ExceptionOccurred () [0x00000]
  at UnityEditor.Android.PostProcessor.Tasks.BuildGradleProject.Execute () [0x00000]
```

### 3.2 规则文件示例
```json
{
    "id": "IL2CPP_ERR_001",
    "name": "IL2CPP Method Processing Error",
    "type": "multi_line",
    "category": "compilation",
    "severity": "error",
    "segments": [
        {
            "order": 1,
            "pattern": "Error: IL2CPP error occurred while processing method '([^']*)'",
            "capture_groups": ["method_name"],
            "required": true
        },
        {
            "order": 2,
            "pattern": "at .*AndroidJNI\\..*",
            "capture_groups": ["jni_context"],
            "required": false
        }
    ],
    "metadata": {
        "created_at": "2025-10-22",
        "description": "IL2CPP在处理特定方法时遇到的编译错误",
        "solution": "检查方法是否包含不支持的JNI调用或不安全代码"
    }
}
```

### 3.3 部署验证示例
```python
# 验证规则
validation_result = rule_validator.validate_new_rule(
    rule=new_rule,
    test_logs=[original_error_log]
)

# 测试性能
perf_metrics = performance_tester.test_rule_performance(
    rule=new_rule,
    sample_logs=sample_logs
)

# 如果验证通过，部署规则
if validation_result.is_valid and perf_metrics.is_acceptable:
    deployer.deploy_rule(new_rule, "compilation")

# 验证部署
deployment_success = deployment_verifier.verify_deployment("IL2CPP_ERR_001")

if deployment_success:
    print("规则更新成功！")
else:
    print("规则更新失败，正在回滚...")
    deployer.rollback()
```

## 4. 注意事项

### 4.1 流程要点
1. 确保新规则被正确提取和格式化
2. 验证规则的有效性
3. 检查是否与现有规则产生冲突
4. 确认性能满足要求
5. 确保部署过程可靠且可回滚
6. 保持完整的记录和文档

### 4.2 最佳实践
1. 使用自动化脚本执行更新流程
2. 保持规则命名和分类的一致性
3. 定期检查和清理过时规则
4. 维护完善的测试用例库
5. 建立规则更新的审核机制