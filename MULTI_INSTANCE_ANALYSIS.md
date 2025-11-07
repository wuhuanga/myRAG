# xwrag 多实例问题深度分析

> **核心结论**：在同一进程中创建多个 xwrag 实例会导致**性能问题**（串行化），但只要 workspace 不同就**不会数据干扰**。

---

## 🎯 快速回答您的问题

### 问题 1：多个实例对文档操作会变成串行吗？

**✅ 是的，会串行化。**

```python
# 同一进程中的两个实例
instance1 = xwrag(workspace="project_a", working_dir="./rag")
instance2 = xwrag(workspace="project_b", working_dir="./rag")

# 并发插入文档
instance1.insert("document 1")  # ← 获取全局锁
instance2.insert("document 2")  # ← 等待锁释放，被阻塞！⏸️
```

**原因**：所有实例共享以下全局锁：
- `_storage_lock` - 存储操作锁
- `_internal_lock` - 内部操作锁
- `_graph_db_lock` - 图数据库操作锁
- `_data_init_lock` - 数据初始化锁

### 问题 2：只要 workspace 不同就不会数据干扰？

**✅ 是的，数据完全隔离。**

```python
# workspace 不同 = namespace 不同 = 数据隔离
instance1 = xwrag(workspace="project_a")
# └─> namespace = "project_a_kv_store_full_docs"

instance2 = xwrag(workspace="project_b")
# └─> namespace = "project_b_kv_store_full_docs"

# 全局共享字典中的数据
_shared_dicts = {
    "project_a_kv_store_full_docs": {...},  # ← instance1 的数据
    "project_b_kv_store_full_docs": {...},  # ← instance2 的数据
}
# ✅ 完全隔离，互不干扰！
```

---

## 📊 详细技术分析

### 1. 全局锁共享机制

#### 源码分析（`xwrag/kg/shared_storage.py`）

```python
# 模块级全局变量
_storage_lock = None
_internal_lock = None
_initialized = None

def initialize_share_data(workers: int = 1):
    global _initialized, _storage_lock, _internal_lock

    # ⚠️ 关键检查
    if _initialized:
        # 已初始化，直接返回！
        # 所有后续的实例都会复用同一套锁
        return

    # 单进程模式
    if workers == 1:
        _storage_lock = asyncio.Lock()  # ← 创建全局锁
        _internal_lock = asyncio.Lock()

    _initialized = True  # ← 标记为已初始化
```

#### 实例化流程

```python
# 第一个实例
rag1 = xwrag(workspace="a")
# └─> __post_init__()
#     └─> initialize_share_data()  # 创建锁，_initialized = True

# 第二个实例
rag2 = xwrag(workspace="b")
# └─> __post_init__()
#     └─> initialize_share_data()  # 发现 _initialized = True，直接返回
#     └─> 使用相同的 _storage_lock ⚠️
```

#### 锁的使用（`xwrag/kg/json_kv_impl.py`）

```python
class JsonKVStorage:
    async def initialize(self):
        # 所有实例都获取同一个全局锁
        self._storage_lock = get_storage_lock()  # ← 返回全局 _storage_lock

    async def upsert(self, data):
        async with self._storage_lock:  # ← 互斥访问
            # 写入数据
            self._data[key] = value
```

### 2. 数据隔离机制

#### namespace 构建（`xwrag/kg/json_kv_impl.py`）

```python
class JsonKVStorage:
    def __post_init__(self):
        if self.workspace:
            # ✅ workspace 会成为 namespace 的一部分
            self.final_namespace = f"{self.workspace}_{self.namespace}"
        else:
            # ⚠️ 空 workspace 只使用 namespace
            self.final_namespace = self.namespace

    async def initialize(self):
        # 使用不同的 namespace 获取数据
        self._data = await get_namespace_data(self.final_namespace)
```

#### 数据存储结构

```python
# 全局共享字典
_shared_dicts = {
    # 实例1 (workspace="project_a")
    "project_a_kv_store_full_docs": {
        "doc1": {...},
        "doc2": {...},
    },

    # 实例2 (workspace="project_b")
    "project_b_kv_store_full_docs": {
        "doc3": {...},
        "doc4": {...},
    },

    # ✅ 不同 namespace，数据完全隔离
}
```

---

## ⚠️ 三种场景分析

### 场景 1：不同 workspace（推荐✅）

```python
instance1 = xwrag(workspace="unique_workspace_1", working_dir="./rag")
instance2 = xwrag(workspace="unique_workspace_2", working_dir="./rag")
```

| 维度 | 结果 | 说明 |
|------|------|------|
| **数据隔离** | ✅ 完全隔离 | 不同 namespace |
| **并发性能** | ❌ 串行化 | 共享全局锁 |
| **数据安全** | ✅ 安全 | 不会冲突 |
| **适用场景** | ✅ 多租户隔离 | 低并发可用 |

**性能影响**：
```
预期（理想情况）：
├─ 实例1.insert() ─┐  并行执行
├─ 实例2.insert() ─┤  50ms
└─ 实例3.insert() ─┘

实际（锁竞争）：
├─ 实例1.insert() ───→ 50ms
├─ 实例2.insert() ───→ 50ms (等待中)
└─ 实例3.insert() ───→ 50ms (等待中)
                       总耗时: 150ms
```

### 场景 2：相同 workspace（危险❌）

```python
instance1 = xwrag(workspace="shared", working_dir="./rag")
instance2 = xwrag(workspace="shared", working_dir="./rag")  # ⚠️ 相同！
```

| 维度 | 结果 | 说明 |
|------|------|------|
| **数据隔离** | ❌ 共享数据 | 相同 namespace |
| **并发性能** | ❌ 串行化 | 共享全局锁 |
| **数据安全** | ❌❌ 危险 | 数据混乱 |
| **适用场景** | ❌ 不推荐 | 会出现 BUG |

**数据冲突示例**：
```python
# 两个实例操作同一个 namespace
_shared_dicts["shared_kv_store_full_docs"] = {
    # instance1 写入
    "doc1": "content from instance1",

    # instance2 也写入（可能覆盖）
    "doc1": "content from instance2",  # ⚠️ 冲突！
}
```

### 场景 3：空 workspace（高风险❌）

```python
instance1 = xwrag(workspace="", working_dir="./rag")
instance2 = xwrag(workspace="", working_dir="./rag")  # ⚠️ 都是空
```

| 维度 | 结果 | 说明 |
|------|------|------|
| **数据隔离** | ❌ 共享数据 | namespace = "_kv_store_xxx" |
| **并发性能** | ❌ 串行化 | 共享全局锁 |
| **数据安全** | ❌❌ 危险 | 严重冲突 |
| **适用场景** | ❌ 禁止使用 | 会丢失数据 |

---

## 🎯 性能影响量化

### 并发查询测试（假设单次查询 50ms）

| 场景 | 实例数 | 并发数 | 理想耗时 | 实际耗时 | 性能损失 |
|------|--------|--------|----------|----------|----------|
| 单实例 | 1 | 10 | 50ms | 500ms | 0% (基准) |
| 多实例（共享锁） | 3 | 30 | 50ms | 1500ms | 97% ❌ |
| 多进程（独立锁） | 3 | 30 | 50ms | 500ms | 0% ✅ |

### 并发插入测试（假设单次插入 100ms）

| 场景 | 实例数 | 并发数 | 理想耗时 | 实际耗时 | QPS |
|------|--------|--------|----------|----------|-----|
| 单实例串行 | 1 | 1 | 100ms | 100ms | 10 |
| 多实例并发（共享锁） | 5 | 5 | 100ms | 500ms | 10 ❌ |
| 多进程并发（独立锁） | 5 | 5 | 100ms | 100ms | 50 ✅ |

---

## ✅ 解决方案和建议

### 方案 1：确保 workspace 唯一（临时方案）⭐

**适用场景**：中小规模应用，并发不高（< 10 QPS）

```python
# 修改 app/dependencies.py
class RAGInstanceManager:
    async def create_instance(self, config: RAGInstanceCreate):
        # ✅ 验证 workspace 唯一性
        if not config.workspace or config.workspace.strip() == "":
            raise ValueError(
                "workspace 不能为空。多实例环境下，必须为每个实例指定唯一的 workspace"
            )

        # ✅ 检查是否重复
        for rag_id, processor in self.instances.items():
            if processor.workspace == config.workspace:
                raise ValueError(
                    f"workspace '{config.workspace}' 已被实例 '{rag_id}' 使用，"
                    f"请使用不同的 workspace 以避免数据冲突"
                )

        # 创建实例...
```

**优点**：
- ✅ 避免数据冲突
- ✅ 实现简单
- ✅ 无需修改架构

**缺点**：
- ❌ 性能受限（锁竞争）
- ❌ 无法真正并行

---

### 方案 2：多进程架构（推荐）⭐⭐⭐

**适用场景**：生产环境，高并发（> 50 QPS）

#### 架构设计

```
┌─────────────────────────────────────────────┐
│           Nginx / Load Balancer             │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   ┌───▼───┐       ┌───▼───┐       ┌────────┐
   │Worker1│       │Worker2│  ...  │Worker N│
   │       │       │       │       │        │
   │ RAG 1 │       │ RAG 1 │       │ RAG 1  │
   └───────┘       └───────┘       └────────┘
   独立锁           独立锁           独立锁
```

#### 实现方式

**使用 Gunicorn + Uvicorn**：

```python
# gunicorn_config.py
workers = 4  # 4 个进程
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 300

# 每个 worker 有独立的全局变量
# 因此每个 worker 有独立的锁
```

**修改应用启动**：

```python
# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 每个 worker 启动时自动创建一个 RAG 实例
    from .dependencies import rag_manager
    from .models import RAGInstanceCreate

    default_config = RAGInstanceCreate(
        rag_id="default",
        workspace=f"worker_{os.getpid()}",  # 每个 worker 唯一
        working_dir=os.getenv("RAG_WORKING_DIR", "./rag_storage"),
    )

    await rag_manager.create_instance(default_config)
    logger.info(f"Worker {os.getpid()} 默认 RAG 实例已创建")

    yield

    # 清理
    rag_manager.delete_instance("default")

app = FastAPI(lifespan=lifespan)
```

**启动命令**：

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300
```

**优点**：
- ✅ **真正的并行**（进程级别）
- ✅ **完全隔离**（每个进程独立的全局变量）
- ✅ **高性能**（无锁竞争）
- ✅ **稳定性高**（进程崩溃不影响其他进程）

**缺点**：
- ❌ 无法动态创建多个实例（每个 worker 固定实例）
- ❌ 内存占用增加（每个进程加载完整模型）

---

### 方案 3：混合架构（灵活）⭐⭐

**适用场景**：需要动态多租户 + 高并发

#### 架构设计

```
┌─────────────────────────────────────────────┐
│      API Gateway (动态路由)                  │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┬──────────────┐
       │                │              │
   ┌───▼──────┐    ┌────▼────┐    ┌───▼──────┐
   │ Worker 1 │    │Worker 2 │    │ Worker 3 │
   │ Tenant A │    │Tenant B │    │ Tenant C │
   └──────────┘    └─────────┘    └──────────┘
```

#### 实现方式

**租户路由**：

```python
# app/main.py
@app.middleware("http")
async def tenant_router(request: Request, call_next):
    # 从请求中提取租户信息
    tenant_id = request.headers.get("X-Tenant-ID")

    # 将租户路由到特定的 worker（通过 hash）
    # 或者使用 Nginx upstream hash 实现

    response = await call_next(request)
    return response
```

**Nginx 配置**：

```nginx
upstream rag_backend {
    # 基于 X-Tenant-ID header 进行一致性 hash
    hash $http_x_tenant_id consistent;

    server 127.0.0.1:8001;  # Worker for Tenant A, B
    server 127.0.0.1:8002;  # Worker for Tenant C, D
    server 127.0.0.1:8003;  # Worker for Tenant E, F
}

server {
    listen 80;

    location / {
        proxy_pass http://rag_backend;
        proxy_set_header X-Tenant-ID $http_x_tenant_id;
    }
}
```

**优点**：
- ✅ 支持动态多租户
- ✅ 每个 worker 管理部分租户（减少锁竞争）
- ✅ 横向扩展能力强

**缺点**：
- ❌ 架构复杂度高
- ❌ 需要额外的路由层

---

## 📋 最佳实践总结

### ✅ 务必遵守的规则

1. **每个实例必须有唯一的 workspace**
   ```python
   # ✅ 正确
   instance1 = xwrag(workspace="tenant_001")
   instance2 = xwrag(workspace="tenant_002")

   # ❌ 错误
   instance1 = xwrag(workspace="shared")
   instance2 = xwrag(workspace="shared")  # 数据冲突！
   ```

2. **生产环境使用多进程架构**
   ```bash
   # ✅ 推荐
   gunicorn app.main:app --workers 4

   # ❌ 不推荐（高并发场景）
   uvicorn app.main:app --workers 1
   ```

3. **在创建实例时验证 workspace**
   ```python
   # 添加验证逻辑
   if not config.workspace:
       raise ValueError("workspace 不能为空")

   if config.workspace in existing_workspaces:
       raise ValueError(f"workspace '{config.workspace}' 已存在")
   ```

### ⚠️ 需要注意的限制

1. **性能限制**
   - 单进程多实例：QPS 受限于单个锁（~10-20 QPS）
   - 多进程架构：QPS 随进程数线性增长

2. **内存占用**
   - 每个实例加载独立的 embedding 模型
   - 估算：每个实例 ~2-4 GB（取决于模型大小）

3. **并发写入**
   - 同一实例的并发写入会串行化
   - 建议使用批量插入接口（`batch_insert`）

---

## 🔍 故障排查指南

### 症状 1：并发查询很慢

**原因**：多个实例共享锁，串行化执行

**解决方案**：
1. 检查是否在单进程中创建了多个实例
2. 迁移到多进程架构
3. 如果必须单进程，减少实例数量

### 症状 2：数据混乱或丢失

**原因**：多个实例使用了相同的 workspace

**解决方案**：
1. 检查所有实例的 workspace 配置
2. 确保每个实例有唯一的 workspace
3. 添加创建时的 workspace 唯一性验证

### 症状 3：内存占用过高

**原因**：创建了过多的 RAG 实例

**解决方案**：
1. 限制单个进程的实例数量（建议 < 5）
2. 使用实例池和复用策略
3. 迁移到多进程架构

---

## 📚 相关文档

- [CONCURRENCY_GUIDE.md](./CONCURRENCY_GUIDE.md) - 并发访问支持指南
- [CONCURRENCY_ANALYSIS.md](./CONCURRENCY_ANALYSIS.md) - 并发和架构深度分析
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API 接口文档

---

## 🔗 参考资源

- xwrag GitHub: https://github.com/HKUDS/xwrag
- FastAPI 文档: https://fastapi.tiangolo.com/
- Gunicorn 文档: https://docs.gunicorn.org/

---

**文档版本**: 1.0
**最后更新**: 2025-11-06
**作者**: Claude Code Assistant
