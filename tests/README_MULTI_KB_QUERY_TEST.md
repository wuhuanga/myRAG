# 多知识库查询接口测试说明

本文档介绍如何测试所有支持多知识库查询的 RAG 接口。

## 测试覆盖范围

### RAG 查询接口（5个）

1. **标准查询** (`POST /api/query/`)
   - 单知识库模式（向后兼容）
   - 多知识库模式

2. **关键字检索** (`POST /api/query/keywords`)
   - 单知识库模式
   - 多知识库模式

3. **清理图谱检索** (`POST /api/query/graph-clean`)
   - 单知识库模式
   - 多知识库模式

4. **仅 Chunks 检索** (`POST /api/query/chunks-only`)
   - 单知识库模式
   - 多知识库模式

5. **UCD 建模** (`POST /api/query/ucd`)
   - 单知识库模式
   - 多知识库模式

### 其他测试

6. **向后兼容性测试** - 验证旧版 `rag_id` 参数仍然有效
7. **错误处理测试** - 验证无效知识库 ID 的处理

## 前置条件

### 1. 启动服务器

```bash
# 确保服务器正在运行
python app/main.py
```

服务器应该运行在 `http://localhost:8000`

### 2. 创建测试知识库

测试需要两个知识库：`test_kb1` 和 `test_kb2`

#### 方法 1: 通过 API 创建（推荐）

```bash
# 创建知识库 1
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb1",
    "description": "测试知识库1",
    "workspace": "test_kb1",
    "working_dir": "./rag_storage"
  }'

# 创建知识库 2
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb2",
    "description": "测试知识库2",
    "workspace": "test_kb2",
    "working_dir": "./rag_storage"
  }'
```

#### 方法 2: 插入测试文档

为了获得更真实的测试结果，建议为每个知识库插入一些测试文档：

```bash
# 为知识库 1 插入文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=test_kb1" \
  -F "file=@docs/test_doc1.txt"

# 为知识库 2 插入文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=test_kb2" \
  -F "file=@docs/test_doc2.txt"
```

## 运行测试

### 方法 1: 使用测试脚本（推荐）

```bash
# 直接运行测试脚本
./run_multi_kb_query_test.sh
```

脚本会：
- 检查服务器是否运行
- 激活 conda 环境（如果需要）
- 运行所有测试
- 显示测试结果总结

### 方法 2: 直接运行 Python 测试

```bash
# 确保服务器正在运行
python tests/test_multi_kb_query.py
```

## 测试输出示例

```
========================================
多知识库查询接口测试
========================================
测试知识库: ['test_kb1', 'test_kb2']
单知识库: test_kb1
========================================

[10:30:15.123] ========== 测试 1.1: 标准查询 - 单知识库 ==========
[10:30:15.456] ✓ PASS - 标准查询-单知识库
          响应: ['test_kb1']

[10:30:15.789] ========== 测试 1.2: 标准查询 - 多知识库 ==========
[10:30:16.123] ✓ PASS - 标准查询-多知识库
          查询 2 个知识库, sources: True

...

============================================================
测试总结
============================================================
总测试数: 12
通过: 12
失败: 0
通过率: 100.0%
============================================================
```

## 测试配置

测试配置在 `tests/test_multi_kb_query.py` 文件顶部：

```python
# 配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# 测试用的知识库 ID
TEST_RAG_IDS = ["test_kb1", "test_kb2"]
TEST_SINGLE_RAG_ID = "test_kb1"
```

如果你的服务器运行在不同端口或使用不同的知识库 ID，请修改这些配置。

## 测试验证点

每个测试会验证以下内容：

### 1. 响应格式
- ✅ 响应包含 `rag_ids` 字段（数组格式）
- ✅ 单知识库模式返回单元素数组
- ✅ 多知识库模式返回多元素数组

### 2. 数据完整性
- ✅ 标准查询返回 `answer` 字段
- ✅ 关键字检索返回 `context` 字段
- ✅ 图谱检索返回 `entities` 和 `relationships`
- ✅ Chunks 检索返回 `chunks` 数组

### 3. 多知识库特性
- ✅ 多知识库查询包含 `sources` 字段
- ✅ `sources` 字段记录每个知识库的贡献
- ✅ 结果正确合并多个知识库的数据

### 4. 向后兼容性
- ✅ 旧版 `rag_id` 参数仍然有效
- ✅ 使用 `rag_id` 时返回格式也是 `rag_ids` 数组

### 5. 错误处理
- ✅ 无效知识库 ID 返回适当错误
- ✅ 错误信息清晰明确

## 常见问题

### Q1: 测试失败：服务器未运行

**错误**: `✗ 服务器未运行！`

**解决方法**:
```bash
# 启动服务器
python app/main.py
```

### Q2: 测试失败：知识库不存在

**错误**: `HTTP 404: RAG 实例不存在`

**解决方法**: 创建测试知识库（参考"前置条件"部分）

### Q3: UCD 建模测试跳过

**输出**: `跳过（UCD builder 未初始化）`

**说明**: 这是正常的，UCD builder 是可选组件。如果未初始化，测试会自动跳过。

### Q4: 部分知识库查询失败

**错误**: `所有知识库查询均失败`

**原因**: 可能是知识库未初始化或没有插入文档

**解决方法**:
1. 检查知识库是否创建成功
2. 为知识库插入一些测试文档
3. 等待文档处理完成

## 调试建议

### 1. 查看详细日志

修改测试文件，添加更详细的日志输出：

```python
# 在测试文件中添加
import json

# 打印完整响应
print(json.dumps(data, indent=2, ensure_ascii=False))
```

### 2. 单独运行某个测试

在测试文件的 `run_all_tests` 方法中注释掉其他测试：

```python
async def run_all_tests(self):
    async with aiohttp.ClientSession() as session:
        # 只运行标准查询测试
        await self.test_standard_query_single(session)
        await self.test_standard_query_multi(session)
        # 其他测试已注释
```

### 3. 使用 curl 手动测试

```bash
# 测试单知识库查询
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb1",
    "question": "测试问题",
    "mode": "hybrid",
    "only_need_context": true
  }' | jq

# 测试多知识库查询
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["test_kb1", "test_kb2"],
    "question": "测试问题",
    "mode": "hybrid",
    "only_need_context": true
  }' | jq
```

## 扩展测试

如果需要添加自定义测试，可以在测试类中添加新方法：

```python
async def test_custom_scenario(self, session):
    """自定义测试场景"""
    print(f"\n[{timestamp()}] ========== 自定义测试 ==========")

    url = f"{BASE_URL}{API_PREFIX}/query/"
    payload = {
        "rag_ids": ["test_kb1", "test_kb2", "test_kb3"],
        "question": "自定义问题",
        "mode": "hybrid",
        "top_k": 20
    }

    try:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                # 添加自定义验证逻辑
                self.log_result("自定义测试", True, "测试通过")
            else:
                self.log_result("自定义测试", False, f"HTTP {resp.status}")
    except Exception as e:
        self.log_result("自定义测试", False, f"异常: {str(e)}")
```

然后在 `run_all_tests` 中调用：

```python
await self.test_custom_scenario(session)
```

## 贡献

如果你发现测试中的问题或有改进建议，请提交 Issue 或 Pull Request。
