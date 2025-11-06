# 并发安全性和架构设计深度分析

## 问题一：全局锁与同进程并发问题

### 📊 当前实现分析

#### 1.1 全局变量的作用域

在 `app/dependencies.py` 中：

```python
# 全局 RAG 实例管理器
rag_manager = RAGInstanceManager()
```

**关键点**:
- ✅ 这是一个**模块级全局变量**
- ✅ 在同一个 Python 进程中，所有导入此模块的地方共享**同一个** `rag_manager` 实例
- ⚠️ 不同的 Python 进程会有**各自独立**的 `rag_manager` 实例

#### 1.2 锁的作用范围

在 `app/dependencies_concurrent.py` 的改进版本中：

```python
class ConcurrentRAGInstanceManager:
    def __init__(self):
        self.instances: Dict[str, lightragProcessor] = {}
        self._lock = asyncio.Lock()  # 进程内的异步锁
```

**重要特性**:

1. **`asyncio.Lock` 是进程内的锁**
   - ✅ 同一进程内有效
   - ❌ 不能跨进程（多进程部署时每个进程有自己的锁）
   - ❌ 不能跨机器

2. **锁保护的范围**
   ```python
   async def create_instance(self, config):
       async with self._lock:  # 锁只保护这个代码块
           if config.rag_id in self.instances:
               raise ValueError("实例已存在")
           # 创建并存储实例
           self.instances[config.rag_id] = processor
   ```

   锁**只保护**:
   - ✅ `instances` 字典的读写操作
   - ✅ 实例的创建、删除、列表操作

   锁**不保护**:
   - ❌ lightrag 实例内部的操作（insert、query 等）
   - ❌ 不同 RAG 实例之间的操作

#### 1.3 同进程多实例的并发情况

**场景**: 同一进程创建两个 lightrag 实例

```python
# 创建两个不同的 RAG 实例
rag_instance_1 = await manager.create_instance(config_1)  # rag_id = "kb1"
rag_instance_2 = await manager.create_instance(config_2)  # rag_id = "kb2"

# 并发操作这两个实例
await asyncio.gather(
    rag_instance_1.rag.insert("文档A"),  # ❓ 这里有并发问题吗？
    rag_instance_2.rag.insert("文档B")   # ❓ 这里有并发问题吗？
)
```

**分析**:

| 操作层级 | 是否共享锁 | 并发安全性 | 说明 |
|---------|-----------|-----------|------|
| **Manager 层** | ✅ 共享 | ✅ 安全 | `manager._lock` 保护 instances 字典 |
| **不同 RAG 实例** | ❌ 不共享 | ✅ 安全 | 每个实例独立，无共享状态 |
| **同一 RAG 实例内部** | ❓ 取决于 lightrag | ⚠️ 需检查 | 取决于 lightrag 库的实现 |

### 🎯 结论：问题一

#### ✅ 安全的场景

1. **不同 RAG 实例的并发操作**
   ```python
   # ✅ 完全安全：两个实例相互独立
   await asyncio.gather(
       instance_1.query("问题1"),
       instance_2.query("问题2")
   )
   ```

2. **Manager 层的管理操作**
   ```python
   # ✅ 安全：锁保护
   await asyncio.gather(
       manager.create_instance(config_1),
       manager.create_instance(config_2)
   )
   ```

#### ⚠️ 需要注意的场景

**同一个 lightrag 实例的并发写操作**

```python
instance = manager.get_instance("kb1")

# ⚠️ 需要检查 lightrag 库是否支持
await asyncio.gather(
    instance.rag.insert("文档A"),  # 并发写入
    instance.rag.insert("文档B"),  # 并发写入
    instance.rag.insert("文档C")   # 并发写入
)
```

**潜在问题**:
- lightrag 内部可能有共享状态（如文件句柄、数据库连接）
- 需要检查 lightrag 源码确认是否线程安全/协程安全

**建议**:
1. **查询操作**: 通常是只读的，并发安全 ✅
2. **写入操作**:
   - 使用批量接口 ✅
   - 或使用应用层的 `Semaphore` 控制并发数 ✅

---

## 问题二：文件索引队列机制

### 📋 你提出的架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  进程1 (API) │────▶│  任务队列     │────▶│  进程2 (Indexer) │
│  上传文件    │     │  (Redis/DB)  │     │  专门负责索引    │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                                            │
       │                                            │
       ▼                                            ▼
  添加到队列                                   从队列取任务
  返回任务ID                                   执行索引操作
```

### ✅ 这个设计的优点

1. **职责分离**
   - API 进程：快速响应，不阻塞
   - Indexer 进程：专注于计算密集型任务

2. **资源控制**
   - 可以限制索引进程的资源使用
   - 避免索引操作影响 API 响应速度

3. **可扩展性**
   - 可以根据需要增加 Indexer 进程数量
   - 横向扩展能力强

### ⚠️ 这个设计的问题和解决方案

#### 问题 1: 单点故障

**问题**: 如果唯一的 Indexer 进程挂掉，所有索引任务停止

**解决方案**:

```python
# 方案A: 多个 Indexer 进程 + 竞争锁
# 每个进程从队列取任务时加锁，确保同一任务不被重复处理

import redis
from contextlib import contextmanager

@contextmanager
def task_lock(redis_client, task_id, timeout=300):
    """分布式任务锁"""
    lock_key = f"task_lock:{task_id}"
    lock = redis_client.lock(lock_key, timeout=timeout)
    try:
        acquired = lock.acquire(blocking=False)
        if acquired:
            yield True
        else:
            yield False
    finally:
        if acquired:
            lock.release()

# 使用
async def process_task(task_id):
    with task_lock(redis_client, task_id) as acquired:
        if acquired:
            # 执行索引任务
            await index_document(task_id)
        else:
            # 其他进程正在处理
            pass
```

```python
# 方案B: 主从架构 + 心跳检测
# 主 Indexer 挂掉后，从 Indexer 自动接管

class IndexerWithHeartbeat:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.is_primary = False

    async def try_become_primary(self):
        """尝试成为主 Indexer"""
        result = self.redis.set(
            "indexer_primary",
            self.instance_id,
            nx=True,  # 只在不存在时设置
            ex=10     # 10秒过期
        )
        self.is_primary = result

    async def heartbeat_loop(self):
        """心跳循环"""
        while True:
            await self.try_become_primary()
            if self.is_primary:
                # 处理任务
                await self.process_tasks()
            await asyncio.sleep(5)
```

#### 问题 2: 性能瓶颈

**问题**: 单个进程可能无法处理大量文件索引请求

**解决方案**:

```python
# 方案A: 任务分片 - 多个 Indexer 处理不同的 RAG 实例

# Indexer 1: 处理 rag_id 以 "a-m" 开头的任务
# Indexer 2: 处理 rag_id 以 "n-z" 开头的任务

def get_indexer_shard(rag_id: str) -> int:
    """根据 rag_id 分配到不同的分片"""
    first_char = rag_id[0].lower()
    if 'a' <= first_char <= 'm':
        return 0
    else:
        return 1

# 添加任务时指定分片
await add_task_to_queue(
    task_data,
    shard=get_indexer_shard(rag_id)
)
```

```python
# 方案B: 动态工作进程池

from concurrent.futures import ProcessPoolExecutor

class IndexerPool:
    def __init__(self, max_workers=4):
        self.pool = ProcessPoolExecutor(max_workers=max_workers)

    async def process_task(self, task):
        """在进程池中处理任务"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.pool,
            index_document_sync,  # 同步版本的索引函数
            task
        )
        return result
```

#### 问题 3: 队列持久化

**问题**: 进程重启后队列中的任务丢失

**解决方案**:

```python
# 使用可靠的消息队列（Redis、RabbitMQ、Celery）

# 方案A: Redis + 持久化
import aioredis

class PersistentTaskQueue:
    def __init__(self):
        self.redis = aioredis.from_url(
            "redis://localhost",
            decode_responses=True
        )

    async def add_task(self, rag_id: str, task_data: dict):
        """添加任务到队列（持久化）"""
        task = {
            "task_id": str(uuid.uuid4()),
            "rag_id": rag_id,
            "data": task_data,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "retry_count": 0
        }

        # 存储任务详情
        await self.redis.hset(
            f"task:{task['task_id']}",
            mapping=task
        )

        # 添加到待处理队列
        await self.redis.rpush(
            f"queue:{rag_id}",
            task['task_id']
        )

        return task['task_id']

    async def get_next_task(self, rag_id: str):
        """获取下一个任务（原子操作）"""
        # 使用 BLPOP 阻塞式获取，确保原子性
        result = await self.redis.blpop(
            f"queue:{rag_id}",
            timeout=5
        )

        if result:
            _, task_id = result
            task_data = await self.redis.hgetall(f"task:{task_id}")
            return task_data

        return None

    async def mark_task_complete(self, task_id: str):
        """标记任务完成"""
        await self.redis.hset(
            f"task:{task_id}",
            "status",
            "completed"
        )
```

```python
# 方案B: 使用 Celery（推荐用于生产环境）

from celery import Celery

app = Celery('indexer', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def index_document_task(self, rag_id: str, document_data: dict):
    """索引文档任务（自动重试、持久化）"""
    try:
        # 执行索引
        result = index_document(rag_id, document_data)
        return result
    except Exception as e:
        # 失败后自动重试
        raise self.retry(exc=e, countdown=60)

# API 端提交任务
task = index_document_task.delay(rag_id, document_data)
return {"task_id": task.id}
```

#### 问题 4: 状态同步

**问题**: API 进程如何知道索引任务的进度？

**解决方案**:

```python
# 方案A: 任务状态存储

class TaskStatus:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def update_status(self, task_id: str, status: str, progress: int = 0):
        """更新任务状态"""
        await self.redis.hset(
            f"task_status:{task_id}",
            mapping={
                "status": status,
                "progress": progress,
                "updated_at": datetime.now().isoformat()
            }
        )

    async def get_status(self, task_id: str):
        """获取任务状态"""
        return await self.redis.hgetall(f"task_status:{task_id}")

# API 端点: 查询任务状态
@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    status = await task_status.get_status(task_id)
    return {
        "task_id": task_id,
        "status": status.get("status"),
        "progress": int(status.get("progress", 0))
    }
```

```python
# 方案B: WebSocket 实时推送

class TaskProgressNotifier:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def subscribe(self, task_id: str, websocket: WebSocket):
        """订阅任务进度"""
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)

    async def notify_progress(self, task_id: str, progress: int):
        """通知进度更新"""
        if task_id in self.connections:
            for ws in self.connections[task_id]:
                await ws.send_json({
                    "task_id": task_id,
                    "progress": progress,
                    "timestamp": datetime.now().isoformat()
                })

# WebSocket 端点
@app.websocket("/ws/tasks/{task_id}")
async def task_progress_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    await notifier.subscribe(task_id, websocket)
    # 保持连接...
```

---

## 🎯 推荐的完整架构

### 架构 A: 轻量级方案（适合中小规模）

```
┌─────────────┐
│  FastAPI    │
│  多 Worker  │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│   Redis      │
│  任务队列     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Indexer     │
│  1-3 个进程  │
└──────────────┘
```

**实现要点**:
- FastAPI 启动 4-8 个 worker
- Redis 作为任务队列和状态存储
- 2-3 个 Indexer 进程，使用分布式锁避免冲突
- 适合 QPS < 1000 的场景

### 架构 B: 生产级方案（适合大规模）

```
┌─────────────┐     ┌──────────────┐
│   Nginx     │────▶│   FastAPI    │
│  负载均衡    │     │  8+ Workers  │
└─────────────┘     └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Celery     │
                    │   Broker     │
                    │  (RabbitMQ)  │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐  ┌──────────┐
     │ Worker 1 │   │ Worker 2 │  │ Worker N │
     │ Indexer  │   │ Indexer  │  │ Indexer  │
     └──────────┘   └──────────┘  └──────────┘
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │  状态存储     │
                    └──────────────┘
```

**实现要点**:
- Nginx 负载均衡
- FastAPI 多个 worker 进程
- Celery 作为任务队列（支持优先级、重试、延迟）
- 多个 Celery worker 并行处理索引任务
- PostgreSQL 存储任务状态和元数据
- 适合 QPS > 1000 的场景

---

## 📝 代码实现示例

### 完整的队列索引实现

```python
# indexer_queue.py
import asyncio
import aioredis
import logging
from typing import Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class IndexerQueue:
    """索引任务队列管理器"""

    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        """连接 Redis"""
        self.redis = await aioredis.from_url(
            self.redis_url,
            decode_responses=True
        )

    async def submit_indexing_task(
        self,
        rag_id: str,
        content: str,
        file_path: str,
        doc_id: str = None
    ) -> str:
        """
        提交索引任务到队列

        Returns:
            task_id: 任务 ID
        """
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "rag_id": rag_id,
            "content": content,
            "file_path": file_path,
            "doc_id": doc_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "retry_count": 0
        }

        # 存储任务详情
        await self.redis.hset(
            f"task:{task_id}",
            mapping=task_data
        )

        # 添加到队列
        await self.redis.rpush(
            f"indexer_queue:{rag_id}",
            task_id
        )

        logger.info(f"任务已提交: {task_id}")
        return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        task_data = await self.redis.hgetall(f"task:{task_id}")
        if not task_data:
            return {"error": "任务不存在"}
        return task_data

    async def process_queue(self, rag_id: str):
        """
        处理队列中的任务（由 Indexer 进程调用）
        """
        while True:
            try:
                # 阻塞式获取任务（最多等待 5 秒）
                result = await self.redis.blpop(
                    f"indexer_queue:{rag_id}",
                    timeout=5
                )

                if not result:
                    # 队列为空，等待
                    await asyncio.sleep(1)
                    continue

                _, task_id = result

                # 获取任务详情
                task_data = await self.redis.hgetall(f"task:{task_id}")

                if not task_data:
                    logger.error(f"任务数据不存在: {task_id}")
                    continue

                # 更新状态为处理中
                await self.redis.hset(
                    f"task:{task_id}",
                    "status",
                    "processing"
                )

                # 执行索引（这里需要调用实际的索引函数）
                try:
                    await self._execute_indexing(task_data)

                    # 标记完成
                    await self.redis.hset(
                        f"task:{task_id}",
                        mapping={
                            "status": "completed",
                            "completed_at": datetime.now().isoformat()
                        }
                    )

                    logger.info(f"任务完成: {task_id}")

                except Exception as e:
                    logger.error(f"任务执行失败: {task_id}, 错误: {e}")

                    # 增加重试次数
                    retry_count = int(task_data.get("retry_count", 0)) + 1

                    if retry_count < 3:
                        # 重新加入队列
                        await self.redis.hset(
                            f"task:{task_id}",
                            "retry_count",
                            retry_count
                        )
                        await self.redis.rpush(
                            f"indexer_queue:{rag_id}",
                            task_id
                        )
                        logger.info(f"任务重试 ({retry_count}/3): {task_id}")
                    else:
                        # 标记失败
                        await self.redis.hset(
                            f"task:{task_id}",
                            mapping={
                                "status": "failed",
                                "error": str(e),
                                "failed_at": datetime.now().isoformat()
                            }
                        )

            except Exception as e:
                logger.error(f"处理队列时出错: {e}")
                await asyncio.sleep(5)

    async def _execute_indexing(self, task_data: Dict[str, Any]):
        """执行实际的索引操作"""
        from app.dependencies import get_rag_manager

        manager = get_rag_manager()
        processor = manager.get_instance(task_data["rag_id"])

        # 执行索引
        if task_data.get("doc_id"):
            processor.rag.insert(
                task_data["content"],
                ids=[task_data["doc_id"]],
                file_paths=[task_data["file_path"]]
            )
        else:
            processor.rag.insert(
                task_data["content"],
                file_paths=[task_data["file_path"]]
            )


# 全局队列管理器
indexer_queue = IndexerQueue()
```

### 在 API 中使用

```python
# app/routers/documents_with_queue.py

from fastapi import APIRouter
from app.indexer_queue import indexer_queue

router = APIRouter()


@router.post("/documents/insert_async")
async def insert_document_async(request: InsertRequest):
    """异步插入文档（提交到队列）"""

    # 提交到队列，立即返回
    task_id = await indexer_queue.submit_indexing_task(
        rag_id=request.rag_id,
        content=request.content,
        file_path=request.file_path,
        doc_id=request.doc_id
    )

    return {
        "status": "submitted",
        "task_id": task_id,
        "message": "文档已提交到索引队列"
    }


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """查询任务状态"""
    status = await indexer_queue.get_task_status(task_id)
    return status
```

### 启动 Indexer 进程

```python
# indexer_worker.py

import asyncio
import logging
from app.indexer_queue import indexer_queue

logging.basicConfig(level=logging.INFO)


async def main():
    """Indexer Worker 主函数"""
    print("Indexer Worker 启动...")

    # 连接 Redis
    await indexer_queue.connect()

    # 监听所有 RAG 实例的队列（或指定特定实例）
    rag_ids = ["kb1", "kb2", "kb3"]  # 从配置中读取

    # 为每个 RAG 实例创建一个处理协程
    tasks = [
        indexer_queue.process_queue(rag_id)
        for rag_id in rag_ids
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 总结与建议

### 问题一答案：全局锁

1. **同进程内**:
   - ✅ 不同 RAG 实例的操作是安全的（实例隔离）
   - ⚠️ 同一 RAG 实例的并发写入需要注意（取决于 lightrag 实现）
   - ✅ Manager 的管理操作是安全的（锁保护）

2. **多进程部署**:
   - ❌ `asyncio.Lock` 不能跨进程
   - 需要使用分布式锁（Redis）或任务队列

### 问题二答案：队列索引

你的设计很好！但需要考虑：

✅ **优点**:
- 职责分离
- 性能可控
- 易于扩展

⚠️ **需要完善**:
1. 增加故障恢复机制（主从或多 worker）
2. 使用持久化队列（Redis/Celery）
3. 实现任务状态追踪
4. 考虑性能瓶颈时的水平扩展

### 🎯 最终建议

**对于你的场景，建议**:

1. **小规模（< 100 用户）**: 直接并发访问，无需队列
2. **中等规模（100-1000 用户）**: 使用 Redis + 简单队列
3. **大规模（> 1000 用户）**: 使用 Celery + RabbitMQ

**实现优先级**:
1. 🔥 先实现基本功能（直接索引）
2. 🔥 添加队列支持（Redis）
3. 🔥 添加状态追踪
4. ⭐ 优化：多 worker、失败重试
5. ⭐ 监控和告警

需要我帮你实现具体的队列版本吗？
