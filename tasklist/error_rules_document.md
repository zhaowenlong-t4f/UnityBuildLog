# Unity 错误规则系统设计文档

## 1. 系统概述
错误规则系统（Error Rules System）是Unity日志分析系统的规则引擎，负责定义和组织各类错误的识别规则。采用分布式的JSON配置文件组织，支持多层级的规则管理，提供灵活的模式匹配和规则组合能力。

## 2. 目录结构
```
config/
└── error_rules/
    ├── __init__.py              # 规则加载和管理
    ├── base_schema.json         # 基础规则模式定义
    ├── global_config.json       # 全局配置
    │
    ├── categories/             # 按错误类别组织规则
    │   ├── compilation/        # 编译错误规则
    │   │   ├── cs_errors.json     # C#编译错误
    │   │   ├── il2cpp_errors.json # IL2CPP相关错误
    │   │   └── shader_errors.json # Shader编译错误
    │   │
    │   ├── asset/             # 资源相关错误
    │   │   ├── missing_assets.json    # 资源丢失
    │   │   ├── import_errors.json     # 导入错误
    │   │   └── reference_errors.json  # 引用错误
    │   │
    │   ├── build/             # 构建系统错误
    │   │   ├── build_pipeline.json    # 构建管线错误
    │   │   ├── platform_specific.json # 平台特定错误
    │   │   └── packaging_errors.json  # 打包错误
    │   │
    │   └── runtime/           # 运行时错误
    │       ├── memory_errors.json     # 内存相关
    │       ├── performance_issues.json # 性能问题
    │       └── crash_patterns.json    # 崩溃模式
    │
    ├── patterns/              # 共享匹配模式
    │   ├── common_patterns.json       # 通用模式
    │   ├── stack_traces.json         # 堆栈跟踪模式
    │   └── file_paths.json           # 文件路径模式
    │
    └── templates/             # 规则模板
        ├── rule_template.json        # 基础规则模板
        ├── multi_line_template.json  # 多行规则模板
        └── correlation_template.json # 关联规则模板

```

## 3. 核心组件

### 3.1 规则基础模式（base_schema.json）
```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "pattern": {
            "type": "object",
            "properties": {
                "regex": { "type": "string" },
                "flags": { "type": "string" },
                "capture_groups": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        },
        "basic_rule": {
            "type": "object",
            "required": ["id", "name", "pattern"],
            "properties": {
                "id": { "type": "string" },
                "name": { "type": "string" },
                "description": { "type": "string" },
                "category": { "type": "string" },
                "severity": {
                    "enum": ["error", "warning", "fatal"]
                }
            }
        }
    }
}
```

### 3.2 全局配置（global_config.json）
```json
{
    "version": "1.0.0",
    "rule_loading": {
        "enabled_categories": ["compilation", "asset", "build", "runtime"],
        "pattern_override_priority": ["local", "category", "global"],
        "hot_reload": true
    },
    "execution": {
        "max_line_scan": 100,
        "max_segment_correlation": 5,
        "cache_size": "100MB"
    },
    "validation": {
        "strict_mode": true,
        "verify_patterns": true
    }
}
```

### 3.3 规则类型

#### 3.3.1 单行规则
```json
{
    "id": "ERR001",
    "name": "编译语法错误",
    "type": "single_line",
    "pattern": {
        "regex": "error CS\\d+:.*",
        "capture_groups": ["error_code", "message"]
    },
    "severity": "error"
}
```

#### 3.3.2 多行规则
```json
{
    "id": "ERR002",
    "name": "资源依赖错误",
    "type": "multi_line",
    "segments": [
        {
            "order": 1,
            "pattern": ".*Failed to load.*",
            "capture_groups": ["asset_name"],
            "required": true
        },
        {
            "order": 2,
            "pattern": ".*Missing dependency:.*",
            "capture_groups": ["dependency"],
            "required": false
        }
    ],
    "max_line_distance": 5
}
```

#### 3.3.3 关联规则
```json
{
    "id": "ERR003",
    "name": "编译错误链",
    "type": "correlation",
    "patterns": {
        "primary": {
            "regex": ".*Compiler Error.*",
            "capture_groups": ["error_code"]
        },
        "related": {
            "regex": ".*Related location:.*",
            "capture_groups": ["related_file"]
        }
    },
    "correlation": {
        "type": "causality",
        "max_distance": 3,
        "conditions": ["${error_code} in ${related_file}"]
    }
}
```

## 4. 规则管理功能

### 4.1 规则加载与验证
```python
class RuleManager:
    """规则管理器"""
    
    async def load_rules(self):
        """加载所有规则"""
        # 加载全局配置
        # 加载共享模式
        # 按类别加载规则
        pass
        
    def _validate_rules(self, rules: List[dict]):
        """验证规则合法性"""
        # Schema验证
        # 模式合法性检查
        # 规则冲突检测
        pass
```

### 4.2 规则组织与访问
```python
class RuleRegistry:
    """规则注册表"""
    
    def get_rules_by_category(self, category: str) -> List[dict]:
        """获取特定类别的规则"""
        pass
        
    def get_rule(self, rule_id: str) -> Optional[dict]:
        """获取特定规则"""
        pass
```

### 4.3 模式管理
```python
class PatternManager:
    """模式管理器"""
    
    def register_pattern(self, pattern: dict):
        """注册共享模式"""
        pass
        
    def resolve_pattern(self, pattern_ref: str) -> dict:
        """解析模式引用"""
        pass
```

## 5. 规则使用场景

### 5.1 编译错误识别
```json
{
    "id": "CS_ERR_001",
    "name": "C#编译错误",
    "type": "multi_line",
    "pattern_refs": ["stack_trace_csharp"],
    "patterns": {
        "main": {
            "regex": "error CS\\d+:.*",
            "capture_groups": ["error_code", "message"]
        }
    }
}
```

### 5.2 资源错误检测
```json
{
    "id": "ASSET_ERR_001",
    "name": "资源引用错误",
    "type": "correlation",
    "patterns": {
        "missing": {
            "regex": ".*Missing.*\\.meta$",
            "capture_groups": ["asset_path"]
        },
        "reference": {
            "regex": ".*referenced by.*",
            "capture_groups": ["referencer"]
        }
    }
}
```

### 5.3 平台特定问题
```json
{
    "id": "PLATFORM_ERR_001",
    "name": "iOS构建错误",
    "type": "multi_line",
    "platform": "ios",
    "segments": [
        {
            "pattern": ".*Xcode build failed.*",
            "required": true
        },
        {
            "pattern": ".*error:.*",
            "capture_groups": ["error_detail"]
        }
    ]
}
```

## 6. 性能优化

### 6.1 规则编译优化
- 正则表达式预编译
- 模式缓存机制
- 规则索引构建

### 6.2 匹配性能优化
- 多级过滤
- 并行匹配
- 早期终止

### 6.3 内存优化
- 惰性加载
- 缓存清理
- 内存限制

## 7. 扩展机制

### 7.1 新规则类型添加
1. 定义规则模板
2. 实现匹配逻辑
3. 注册规则处理器

### 7.2 自定义匹配器
1. 实现匹配器接口
2. 配置匹配规则
3. 注册到规则系统

### 7.3 规则转换器
1. 支持其他格式导入
2. 规则版本迁移
3. 规则合并工具

## 8. 监控与维护

### 8.1 性能指标
- 规则加载时间
- 匹配效率统计
- 内存使用监控

### 8.2 质量指标
- 规则覆盖率
- 误报统计
- 规则使用频率

### 8.3 维护工具
- 规则检验工具
- 性能分析工具
- 规则更新工具

## 9. 最佳实践

### 9.1 规则编写指南
1. 使用明确的命名
2. 提供详细描述
3. 合理使用捕获组
4. 优化正则表达式
5. 添加测试用例

### 9.2 规则组织建议
1. 按功能分类
2. 控制规则粒度
3. 复用共享模式
4. 维护规则文档

### 9.3 性能优化建议
1. 限制规则复杂度
2. 合理设置超时
3. 使用规则缓存
4. 定期清理无用规则

## 10. 错误处理

### 10.1 常见错误类型
- 规则格式错误
- 模式匹配失败
- 规则冲突错误
- 性能超限错误

### 10.2 错误处理策略
1. 详细错误日志
2. 降级处理方案
3. 自动恢复机制
4. 错误报告系统

## 11. 版本控制

### 11.1 版本管理
- 语义化版本号
- 变更日志维护
- 向后兼容性

### 11.2 升级策略
1. 规则迁移工具
2. 兼容性检查
3. 平滑升级方案

## 12. 安全考虑

### 12.1 输入验证
- 规则格式验证
- 正则表达式安全检查
- 资源限制控制

### 12.2 访问控制
- 规则修改权限
- 操作审计日志
- 敏感信息保护

## 13. 测试策略

### 13.1 单元测试
- 规则解析测试
- 匹配逻辑测试
- 边界条件测试

### 13.2 集成测试
- 规则加载测试
- 性能基准测试
- 系统集成测试

### 13.3 回归测试
- 自动化测试套件
- 测试用例管理
- 持续集成流程