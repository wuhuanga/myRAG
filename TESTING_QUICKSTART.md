# 测试快速开始指南

## 环境准备

### 1. 激活 conda 环境

```bash
conda activate lightrag
```

### 2. 安装测试依赖

```bash
pip install pytest pytest-asyncio requests
```

### 3. 确保服务运行

- ✅ FastAPI 服务器（默认 localhost:8000）
- ✅ Nebula Graph（默认 localhost:9669）
- ✅ Milvus（默认 localhost:19530）
- ✅ LLM API 可访问
- ✅ Embedding 服务可访问

## 快速运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 只运行集成测试

```bash
pytest tests/ -m integration -v
```

### 运行特定测试文件

```bash
# 数据隔离测试
pytest tests/test_isolation.py -v

# API 测试
pytest tests/test_api.py -v

# 存储层测试
pytest tests/test_storage.py -v

# 错误处理测试
pytest tests/test_error.py -v
```

### 跳过慢速测试

```bash
pytest tests/ -m "not slow" -v
```

### 运行单个测试

```bash
pytest tests/test_isolation.py::TestLogicalIsolation::test_delete_one_workspace_preserves_others -v
```

## 常见问题

### 问题 1: ModuleNotFoundError: No module named 'requests'

**解决**: 确保已激活正确的 conda 环境并安装依赖

```bash
conda activate lightrag
pip install pytest pytest-asyncio requests
```

### 问题 2: 测试超时

**解决**: 增加超时时间或确保 LLM/Embedding 服务响应正常

### 问题 3: Connection refused

**解决**: 确保 FastAPI 服务器在运行

```bash
# 在另一个终端启动服务器
python -m uvicorn app.main:app --reload
```

## 测试标记说明

- `@pytest.mark.integration` - 需要外部服务
- `@pytest.mark.offline` - 不需要外部服务
- `@pytest.mark.slow` - 执行时间较长
- `@pytest.mark.concurrent` - 并发测试

## 查看测试覆盖率

```bash
pip install pytest-cov
pytest tests/ --cov=app --cov=xwrag --cov-report=html
open htmlcov/index.html
```

## 调试测试

```bash
# 显示 print 输出
pytest tests/test_isolation.py -v -s

# 进入调试器
pytest tests/test_isolation.py -v --pdb

# 只运行失败的测试
pytest tests/ --lf
```

## 并行运行测试（可选）

```bash
pip install pytest-xdist
pytest tests/ -n auto  # 使用所有 CPU 核心
```

## 示例：运行第一个测试

```bash
# 1. 激活环境
conda activate lightrag

# 2. 确保服务器运行
# (在另一个终端)
python -m uvicorn app.main:app --reload

# 3. 运行一个简单的测试
pytest tests/test_error.py::TestInputValidation::test_invalid_rag_id_format -v -s

# 4. 如果成功，运行所有测试
pytest tests/ -v
```

## 性能建议

- 首次运行会创建实例和索引数据，较慢（~2-3分钟）
- 后续测试会重用某些资源，速度更快
- 并发测试可能需要更多时间
- 使用 `-m "not slow"` 跳过耗时测试

## 获取帮助

查看详细文档：
```bash
cat tests/README.md
```
