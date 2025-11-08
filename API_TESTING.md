# RAG 后端 API 测试指南

本文档介绍如何使用测试脚本验证 RAG 后端 API 的功能。

---

## 📋 测试脚本说明

### 1. `test_backend_api.py` - 全面测试脚本

**功能**：完整的 API 功能测试，包含所有接口和并发测试

**测试内容**：
- ✅ 健康检查
- ✅ 创建两个 RAG 实例
- ✅ 同步上传文档（指定文件）
- ✅ 查询文档处理状态
- ✅ 执行知识库查询
- ✅ 并发上传测试
- ✅ 并发查询测试
- ✅ 清理测试数据（可选）

**运行方式**：
```bash
python test_backend_api.py
```

**测试配置**：

脚本会创建两个实例并上传指定的文档：

1. **实例1：satellite_project**
   - 文档：`/root/workplace/lightrag/LightRAG1/docx/卫星工程.docx`

2. **实例2：tender_docs**
   - 文档1：`/root/workplace/lightrag/LightRAG1/docx/子标书01.docx`
   - 文档2：`/root/workplace/lightrag/LightRAG1/docx/子标书02.docx`

**输出示例**：
```
================================================================================
                          RAG 后端 API 全面测试
================================================================================

================================================================================
                              测试 1: 健康检查
================================================================================

[12:34:56] [INFO] 服务状态: healthy
[12:34:56] [SUCCESS] ✓ 健康检查通过
...
```

### 2. `test_quick.py` - 快速测试脚本

**功能**：快速验证核心功能，适合日常检查

**测试内容**：
- 健康检查
- 创建单个实例
- 上传一个文档
- 执行一次查询
- 查看文档状态

**运行方式**：
```bash
python test_quick.py
```

**特点**：
- 执行速度快（约 1-2 分钟）
- 输出简洁
- 适合快速验证 API 是否正常

---

## 🚀 使用步骤

### 前置条件

**1. 确保后端服务正在运行**

```bash
# 方法1：使用启动脚本
./start_backend.sh

# 方法2：手动启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

验证服务运行：
```bash
curl http://localhost:8000/api/admin/health
```

预期输出：
```json
{
  "status": "healthy",
  "rag_instances_count": 0,
  "ucd_initialized": false,
  "timestamp": "2025-11-08T..."
}
```

**2. 安装依赖（如果需要）**

测试脚本需要 `requests` 库：
```bash
pip install requests
```

**3. 确保文档文件存在**

检查文档路径：
```bash
ls -lh /root/workplace/lightrag/LightRAG1/docx/
```

应该看到：
- 卫星工程.docx
- 子标书01.docx
- 子标书02.docx

如果文件不存在，请修改脚本中的文件路径。

---

## 📝 运行全面测试

### 步骤1：启动后端

```bash
cd /root/workplace/lightrag/LightRAG1
./start_backend.sh
```

### 步骤2：新开终端运行测试

```bash
cd /root/workplace/lightrag/LightRAG1
python test_backend_api.py
```

### 步骤3：查看测试结果

测试会按顺序执行以下步骤：

1. **健康检查** - 验证服务可访问
2. **创建实例** - 创建 2 个 RAG 实例
3. **列出实例** - 确认实例创建成功
4. **上传文档** - 同步上传 3 个文档
5. **文档状态** - 查看文档处理状态
6. **执行查询** - 测试知识库查询
7. **并发上传** - 测试并发文件上传
8. **并发查询** - 测试并发查询请求

### 步骤4：查看测试摘要

测试结束后会显示汇总信息：
```
================================================================================
                                  测试摘要
================================================================================

总测试数: 15
✓ 通过: 14
✗ 失败: 1

✓ 健康检查                                                      0.05s
✓ 创建实例 - satellite_project                                  2.31s
✓ 创建实例 - tender_docs                                        2.28s
✓ 列出实例                                                      0.02s
✓ 上传文档 - 卫星工程.docx                                       15.42s
...
```

### 步骤5：清理测试数据（可选）

测试结束时会询问是否删除测试实例：
```
是否删除测试创建的实例？(y/N):
```

- 输入 `y` - 删除所有测试实例和数据
- 输入 `N` 或直接回车 - 保留实例，可继续手动测试

---

## 🏃 运行快速测试

适合日常快速验证：

```bash
python test_quick.py
```

输出示例：
```
============================================================
RAG 后端 API 快速测试
============================================================

1️⃣  健康检查...
   ✓ 服务正常: {'status': 'healthy', ...}

2️⃣  创建 RAG 实例...
   ✓ 实例创建成功: quick_test

3️⃣  上传文档...
   ✓ 文档上传成功: 卫星工程.docx

4️⃣  执行查询...
   ✓ 查询成功
   回答长度: 523 字符
   预览: 卫星工程的主要内容包括...

5️⃣  文档状态...
   ✓ 总文档数: 1
   ✓ 已处理: 1
   ✓ 待处理: 0
   ✓ 失败: 0

============================================================
✅ 快速测试完成
============================================================

是否删除测试实例? (y/N):
```

---

## 🔧 自定义测试

### 修改测试文件路径

编辑 `test_backend_api.py`，找到以下部分：

```python
# 文件路径配置
DOC_DIR = Path("/root/workplace/lightrag/LightRAG1/docx")

INSTANCE_1_FILES = [DOC_DIR / "卫星工程.docx"]

INSTANCE_2_FILES = [
    DOC_DIR / "子标书01.docx",
    DOC_DIR / "子标书02.docx"
]
```

修改为您的文件路径。

### 修改 API 地址

如果后端运行在不同的地址或端口：

```python
# 修改这一行
BASE_URL = "http://localhost:8000"

# 例如：
BASE_URL = "http://192.168.1.100:8000"
```

### 添加自定义测试

在 `main()` 函数中添加您的测试逻辑：

```python
# 自定义查询测试
tester.query_knowledge(
    rag_id="your_instance_id",
    question="您的问题？",
    mode="hybrid"
)
```

---

## 📊 性能测试

### 并发上传测试

测试脚本会自动进行并发上传测试。如需调整并发数：

```python
# 在 concurrent_upload_test 方法中修改
with ThreadPoolExecutor(max_workers=3) as executor:  # 修改这里的数字
    ...
```

### 并发查询测试

调整并发查询数量：

```python
# 在 concurrent_query_test 方法中修改
with ThreadPoolExecutor(max_workers=5) as executor:  # 修改这里的数字
    ...
```

### 压力测试建议

对于生产环境压力测试，建议使用专业工具：

**使用 Apache Bench (ab)**：
```bash
# 安装
sudo apt-get install apache2-utils

# 测试健康检查接口
ab -n 1000 -c 10 http://localhost:8000/api/admin/health

# 说明：
# -n 1000: 总请求数
# -c 10: 并发数
```

**使用 wrk**：
```bash
# 安装
sudo apt-get install wrk

# 测试
wrk -t4 -c100 -d30s http://localhost:8000/api/admin/health

# 说明：
# -t4: 4个线程
# -c100: 100个并发连接
# -d30s: 持续30秒
```

---

## ❌ 常见问题

### 问题1：连接被拒绝

**错误信息**：
```
✗ 连接失败: Connection refused
```

**解决方法**：
1. 检查后端是否运行：
   ```bash
   curl http://localhost:8000/api/admin/health
   ```

2. 检查端口是否正确：
   ```bash
   netstat -tuln | grep 8000
   ```

3. 启动后端服务：
   ```bash
   ./start_backend.sh
   ```

### 问题2：文档上传超时

**错误信息**：
```
✗ 文档上传异常: Timeout
```

**解决方法**：
1. 增加超时时间（在脚本中修改）：
   ```python
   timeout=300  # 改为 600 或更大
   ```

2. 检查文档大小：
   ```bash
   ls -lh /path/to/your/document.docx
   ```

3. 查看后端日志中的错误信息

### 问题3：实例已存在

**错误信息**：
```
✗ 创建实例失败: Instance already exists
```

**解决方法**：

方法1 - 删除现有实例：
```bash
curl -X DELETE http://localhost:8000/api/admin/rag_instances/satellite_project
```

方法2 - 修改测试脚本中的实例ID：
```python
INSTANCE_1_ID = "satellite_project_v2"  # 改为新名称
```

### 问题4：文件不存在

**错误信息**：
```
✗ 文件不存在: /path/to/file.docx
```

**解决方法**：
1. 检查文件路径：
   ```bash
   ls -la /root/workplace/lightrag/LightRAG1/docx/
   ```

2. 修改脚本中的文件路径
3. 或使用其他可用的测试文件

### 问题5：查询返回空结果

**原因**：文档可能尚未处理完成

**解决方法**：
1. 检查文档状态：
   ```bash
   curl http://localhost:8000/api/documents/status/your_rag_id
   ```

2. 等待文档处理完成（PROCESSED）后再查询

3. 查看后端日志检查是否有处理错误

---

## 🔍 调试技巧

### 查看详细日志

**方法1 - 在脚本中启用调试**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**方法2 - 查看后端日志**：
后端日志会显示在运行 `uvicorn` 的终端中

**方法3 - 使用 curl 手动测试**：
```bash
# 健康检查
curl http://localhost:8000/api/admin/health

# 创建实例
curl -X POST http://localhost:8000/api/admin/rag_instances/create \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test",
    "workspace": "test_workspace"
  }'

# 上传文档
curl -X POST http://localhost:8000/api/documents/upload \
  -F "rag_id=test" \
  -F "file=@/path/to/document.docx"

# 查询
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test",
    "question": "测试问题",
    "mode": "hybrid"
  }'
```

### 使用 Swagger UI

访问 API 文档页面进行交互式测试：
```
http://localhost:8000/docs
```

在这里您可以：
- 查看所有 API 接口
- 在线测试每个接口
- 查看请求/响应示例

---

## 📚 相关文档

- **API 文档**：`app/README.md`
- **快速启动**：`QUICK_START.md`
- **防火墙配置**：`FIREWALL_SETUP.md`
- **迁移指南**：`MIGRATION_GUIDE.md`
- **前端故障排除**：`frontend/TROUBLESHOOTING.md`

---

## 💡 最佳实践

### 开发环境

1. **使用快速测试验证更改**
   ```bash
   # 每次代码修改后运行
   python test_quick.py
   ```

2. **完整测试用于发布前验证**
   ```bash
   # 发布前运行完整测试
   python test_backend_api.py
   ```

3. **保留测试实例用于调试**
   - 测试结束选择 `N`，保留实例
   - 手动测试和调试
   - 完成后再删除

### 生产环境

1. **定期运行健康检查**
   ```bash
   # 添加到 crontab
   */5 * * * * curl -f http://localhost:8000/api/admin/health || echo "API is down"
   ```

2. **监控文档处理状态**
   ```bash
   # 定期检查是否有失败的文档
   curl http://localhost:8000/api/documents/status/your_rag_id
   ```

3. **性能监控**
   - 记录查询响应时间
   - 监控文档处理耗时
   - 跟踪并发请求性能

---

## 🤝 贡献测试

如果您添加了新的 API 接口，请：

1. 在测试脚本中添加相应的测试方法
2. 更新本文档
3. 提交 Pull Request

**测试方法模板**：
```python
def test_your_feature(self):
    """测试您的功能"""
    self.log_separator("测试 X: 您的功能")
    start = time.time()

    try:
        # 您的测试逻辑
        response = self.session.post(...)
        duration = time.time() - start

        if response.status_code == 200:
            self.log("✓ 测试成功", "SUCCESS")
            self.record_result("您的功能", True, duration)
            return True
        else:
            self.log(f"✗ 测试失败: {response.status_code}", "ERROR")
            self.record_result("您的功能", False, duration)
            return False

    except Exception as e:
        duration = time.time() - start
        self.log(f"✗ 测试异常: {str(e)}", "ERROR")
        self.record_result("您的功能", False, duration, str(e))
        return False
```

---

**更新时间**：2025-11-08
**版本**：1.0
