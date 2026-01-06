# myRAG 测试套件

完整的 pytest 测试套件，用于测试 myRAG 系统的各个方面。

## 📁 测试文件结构

```
tests/
├── conftest.py              # 公共 fixture 和配置
├── test_isolation.py        # 数据隔离测试
├── test_storage.py          # 存储层测试 (Nebula + Milvus)
├── test_api.py              # API 端点测试
├── test_lock.py             # 锁机制测试
├── test_error.py            # 错误处理测试
├── test_concurrent.py       # 并发测试
└── README.md                # 本文件
```

## 🎯 测试覆盖

### 1. 数据隔离测试 (`test_isolation.py`)
- ✅ 多 workspace 数据完全隔离
- ✅ 删除一个 workspace 不影响其他
- ✅ 跨 workspace 查询无数据泄漏
- ✅ Workspace 命名冲突处理
- ✅ 空 workspace 操作
- ✅ 大量 workspace 隔离

### 2. 存储层测试 (`test_storage.py`)
- ✅ Nebula Graph workspace 属性过滤
- ✅ Nebula 删除 workspace 数据
- ✅ Nebula 特殊字符处理
- ✅ Milvus Collection workspace 前缀
- ✅ Milvus 向量搜索隔离
- ✅ Milvus 批量插入
- ✅ 特殊字符（单引号、双引号、反斜杠）
- ✅ Unicode 和多语言内容
- ✅ 空内容和超长内容
- ✅ CRUD 完整周期

### 3. API 端点测试 (`test_api.py`)
- ✅ Admin 端点（创建、列表、删除实例）
- ✅ Documents 端点（插入文档）
- ✅ Query 端点（查询知识库）
- ✅ 不同查询模式（hybrid/local/global）
- ✅ 错误处理（404、422、400）
- ✅ 并发 API 调用
- ✅ 响应格式验证
- ✅ 时间戳格式验证

### 4. 锁机制测试 (`test_lock.py`)
- ✅ 不同 key 并行执行
- ✅ 相同 key 串行执行
- ✅ 多 key 锁定
- ✅ 锁超时行为
- ✅ 重入保护
- ✅ 锁性能开销
- ✅ 高并发锁处理
- ✅ 特殊字符 key

### 5. 错误处理测试 (`test_error.py`)
- ✅ 输入验证（无效格式、负数参数）
- ✅ 缺少必需参数
- ✅ 操作已删除的实例
- ✅ 查询和插入超时
- ✅ 失败后资源清理
- ✅ 部分清理失败处理
- ✅ 异常恢复
- ✅ 快速创建-删除循环

### 6. 并发测试 (`test_concurrent.py`)
- ✅ 并发创建实例
- ✅ 并发删除实例
- ✅ 并发插入文档（同一实例）
- ✅ 并发插入到多个实例
- ✅ 并发查询（同一实例）
- ✅ 并发查询多个实例
- ✅ 混合并发操作（创建、插入、查询、删除）
- ✅ 持续负载测试
- ⚠️  压力测试（大量实例）

## 🚀 运行测试

### 前置要求

1. **启动服务**：
   ```bash
   # 确保 FastAPI 服务器在运行
   python app/main.py  # 或你的启动命令
   ```

2. **环境依赖**：
   - Nebula Graph 服务（默认 localhost:9669）
   - Milvus 服务（默认 localhost:19530）
   - LLM API（用于实体提取）
   - Embedding 服务（用于向量生成）

3. **安装测试依赖**：
   ```bash
   pip install pytest pytest-asyncio requests
   ```

### 运行所有测试

```bash
# 从项目根目录运行
pytest tests/ -v

# 显示详细输出
pytest tests/ -v -s

# 生成覆盖率报告
pytest tests/ --cov=app --cov=xwrag --cov-report=html
```

### 运行特定测试文件

```bash
# 只运行隔离测试
pytest tests/test_isolation.py -v

# 只运行 API 测试
pytest tests/test_api.py -v

# 只运行存储层测试
pytest tests/test_storage.py -v
```

### 按标记运行

```bash
# 只运行集成测试
pytest tests/ -m integration -v

# 只运行离线测试（不需要外部服务）
pytest tests/ -m offline -v

# 运行并发测试
pytest tests/ -m concurrent -v

# 跳过慢速测试
pytest tests/ -m "not slow" -v
```

### 运行特定测试

```bash
# 运行特定测试类
pytest tests/test_isolation.py::TestLogicalIsolation -v

# 运行特定测试方法
pytest tests/test_isolation.py::TestLogicalIsolation::test_delete_one_workspace_preserves_others -v

# 使用关键词过滤
pytest tests/ -k "isolation" -v
pytest tests/ -k "concurrent and not slow" -v
```

## 📊 测试标记

测试使用以下标记分类：

- `@pytest.mark.integration` - 集成测试，需要 Nebula/Milvus 服务
- `@pytest.mark.offline` - 离线测试，不需要外部服务
- `@pytest.mark.slow` - 慢速测试，执行时间较长
- `@pytest.mark.concurrent` - 并发测试
- `@pytest.mark.asyncio` - 异步测试（自动添加）

## 🔧 配置

### 环境变量

可以通过环境变量配置测试：

```bash
# API 地址
export TEST_BASE_URL=http://localhost:8000

# Nebula 连接
export NEBULA_HOST=localhost
export NEBULA_PORT=9669

# Milvus 连接
export MILVUS_HOST=localhost
export MILVUS_PORT=19530

# 运行测试
pytest tests/ -v
```

### conftest.py 配置

查看 `conftest.py` 中的 `test_config` fixture 以了解所有可配置项。

## 📝 编写新测试

### 测试模板

```python
import pytest
from conftest import wait_for_indexing

@pytest.mark.integration
class TestMyFeature:
    """测试新功能"""

    def test_my_scenario(self, api_client, sample_documents):
        """
        测试场景描述

        验证：
        1. 第一个验证点
        2. 第二个验证点
        3. 第三个验证点
        """
        test_id = "test_my_feature"

        try:
            # 创建实例
            api_client.create_instance(test_id, "test_ws")
            time.sleep(2)

            # 插入文档
            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "test.txt"
            )
            wait_for_indexing(10)

            # 执行测试
            result = api_client.query(test_id, "test question")

            # 断言验证
            assert result.get("answer"), "Should return answer"

        finally:
            # 清理
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass
```

### 使用 Fixtures

常用的 fixtures（在 `conftest.py` 中定义）：

- `api_client` - API 客户端，提供便捷方法
- `test_config` - 测试配置字典
- `sample_documents` - 测试文档数据
- `special_char_documents` - 特殊字符测试数据
- `nebula_connection` - Nebula 连接（需要时）
- `milvus_connection` - Milvus 连接（需要时）

## 🐛 调试测试

### 查看详细输出

```bash
# 显示 print 输出
pytest tests/test_isolation.py -v -s

# 显示本地变量
pytest tests/test_isolation.py -v -l

# 进入调试器
pytest tests/test_isolation.py -v --pdb
```

### 只运行失败的测试

```bash
# 第一次运行
pytest tests/ -v

# 只重新运行失败的测试
pytest tests/ -v --lf

# 先运行失败的，再运行其他
pytest tests/ -v --ff
```

### 查看测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=app --cov=xwrag

# 生成 HTML 报告
pytest tests/ --cov=app --cov=xwrag --cov-report=html

# 查看报告
open htmlcov/index.html
```

## ⚠️ 注意事项

1. **测试隔离**：每个测试应该独立运行，不依赖其他测试的状态
2. **资源清理**：使用 `try-finally` 确保测试资源被清理
3. **等待索引**：插入文档后使用 `wait_for_indexing()` 等待索引完成
4. **并发测试**：并发测试可能需要更长的超时时间
5. **慢速测试**：标记慢速测试为 `@pytest.mark.slow`，允许跳过

## 📈 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      nebula:
        image: vesoft/nebula-standalone:latest
        ports:
          - 9669:9669

      milvus:
        image: milvusdb/milvus:latest
        ports:
          - 19530:19530

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      run: pytest tests/ -v --cov=app --cov=xwrag

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 📚 相关文档

- [Pytest 文档](https://docs.pytest.org/)
- [myRAG 项目文档](../README.md)
- [API 文档](../app/README.md)
- [测试指南](../TEST_GUIDE.md)

## 🤝 贡献

添加新测试时，请确保：

1. 测试有清晰的 docstring 说明测试目的
2. 使用适当的标记（integration/offline/slow）
3. 包含 try-finally 清理逻辑
4. 验证关键断言
5. 打印有用的调试信息

## 📞 联系

如有问题，请提 Issue 或联系项目维护者。
