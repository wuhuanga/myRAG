# 后端 API 快速入门指南

## 📚 文档索引

- **[API 接口文档](API_DOCUMENTATION.md)** - 完整的接口文档，包含所有 30+ 个接口的详细说明和调用示例
- **[API 结构说明](API_STRUCTURE.md)** - 项目结构和迁移指南
- **[本文档]** - 快速入门指南

## 🚀 快速开始

### 1. 启动服务

```bash
# 安装依赖
pip install fastapi uvicorn python-multipart aiofiles
pip install xwrag transformers llama-index-llms-litellm
pip install textract python-dotenv nest-asyncio

# 启动服务（开发模式）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 访问 API 文档

启动后访问:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **根路径**: http://localhost:8000

### 3. 基本使用流程

#### 步骤 1: 创建 RAG 实例

```python
import requests

# 创建 RAG 实例
response = requests.post(
    "http://localhost:8000/api/admin/rag_instances/create",
    json={
        "rag_id": "my_knowledge_base",
        "description": "我的知识库",
        "working_dir": "./rag_data/kb1",
        "workspace": "default",
        "chunk_token_size": 1200,
        "enable_llm_cache": True
    }
)
print(response.json())
```

#### 步骤 2: 插入文档

```python
# 方式 1: 直接插入文本
response = requests.post(
    "http://localhost:8000/api/documents/insert",
    json={
        "rag_id": "my_knowledge_base",
        "content": "你的文档内容...",
        "file_path": "document1.txt"
    }
)

# 方式 2: 上传文件
with open("your_file.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/documents/upload?rag_id=my_knowledge_base",
        files={"file": f}
    )

# 方式 3: 批量插入
response = requests.post(
    "http://localhost:8000/api/documents/batch_insert",
    json={
        "rag_id": "my_knowledge_base",
        "documents": [
            {"content": "文档1内容", "file_path": "doc1.txt"},
            {"content": "文档2内容", "file_path": "doc2.txt"}
        ]
    }
)
```

#### 步骤 3: 查询知识库

```python
# 查询
response = requests.post(
    "http://localhost:8000/api/query/",
    json={
        "rag_id": "my_knowledge_base",
        "question": "你的问题?",
        "mode": "hybrid",  # naive/local/global/hybrid
        "top_k": 20
    }
)

result = response.json()
print(f"回答: {result['answer']}")
```

## 🎯 核心功能

### 1. 多 RAG 实例管理

```python
# 创建实例
POST /api/admin/rag_instances/create

# 列出所有实例
GET /api/admin/rag_instances/list

# 获取实例详情
GET /api/admin/rag_instances/{rag_id}

# 删除实例
DELETE /api/admin/rag_instances/{rag_id}
```

### 2. 文档管理

```python
# 上传文档
POST /api/documents/upload?rag_id=xxx

# 插入文档内容
POST /api/documents/insert

# 批量插入
POST /api/documents/batch_insert

# 查看文档状态
GET /api/documents/status/{rag_id}

# 获取文档列表
GET /api/documents/list/{rag_id}/{status}
```

### 3. 知识图谱操作

#### 实体管理

```python
# 创建实体
POST /api/graph/entities/create
{
  "rag_id": "my_kb",
  "entity_name": "Python",
  "description": "编程语言",
  "entity_type": "TECHNOLOGY"
}

# 编辑、删除、查询实体
POST /api/graph/entities/edit
POST /api/graph/entities/delete
POST /api/graph/entities/info
POST /api/graph/entities/merge
```

#### 关系管理

```python
# 创建关系
POST /api/graph/relations/create
{
  "rag_id": "my_kb",
  "source_entity": "Python",
  "target_entity": "Django",
  "description": "用于开发",
  "weight": 0.9
}

# 编辑、删除、查询关系
POST /api/graph/relations/edit
POST /api/graph/relations/delete
POST /api/graph/relations/info
```

### 4. 数据导出

```python
# 导出为 CSV
POST /api/graph/export
{
  "rag_id": "my_kb",
  "output_path": "./export.csv",
  "file_format": "csv"  # csv/excel/md/txt
}
```

### 5. 缓存管理

```python
# 清除 LLM 缓存
POST /api/query/clear_cache
{
  "rag_id": "my_kb",
  "cache_type": "llm_cache"  # llm_cache/all
}
```

## 🔍 查询模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **naive** | 简单向量检索 | 快速查询，不需要复杂推理 |
| **local** | 局部图查询 | 关注实体邻近关系 |
| **global** | 全局图查询 | 需要全局视角的查询 |
| **hybrid** | 混合查询 | **推荐**，结合多种策略 |

## ⚙️ 配置参数说明

### RAG 实例创建参数

#### 必填参数
- `rag_id`: 实例唯一标识
- `working_dir`: 工作目录
- `workspace`: 工作空间

#### 可选参数 (存储配置)
- `kv_storage`: KV 存储类型
- `vector_storage`: 向量存储类型
- `graph_storage`: 图存储类型
- `doc_status_storage`: 文档状态存储类型

#### 可选参数 (查询配置)
- `top_k`: 查询返回的 top k 结果
- `chunk_top_k`: 分块查询的 top k
- `max_entity_tokens`: 实体最大 token 数
- `max_relation_tokens`: 关系最大 token 数
- `max_total_tokens`: 总最大 token 数

#### 可选参数 (分块配置)
- `chunk_token_size`: 分块大小 (默认: 1200)
- `chunk_overlap_token_size`: 重叠大小 (默认: 100)
- `related_chunk_number`: 相关分块数 (默认: 5)

#### 可选参数 (其他)
- `cosine_threshold`: 余弦相似度阈值 (默认: 0.3)
- `enable_llm_cache`: 是否启用 LLM 缓存 (默认: true)
- `enable_llm_cache_for_entity_extract`: 实体提取缓存 (默认: true)

### 查询参数

```python
{
  "rag_id": "my_kb",
  "question": "问题",
  "mode": "hybrid",              # 查询模式
  "only_need_context": True,     # 只返回上下文
  "top_k": 20,                   # Top K 结果
  "chunk_top_k": 10,             # 分块 Top K
  "max_entity_tokens": 6000,     # 实体最大 tokens
  "max_relation_tokens": 8000,   # 关系最大 tokens
  "max_total_tokens": 16300      # 总最大 tokens
}
```

## 📊 完整示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建 RAG 实例
def create_rag_instance():
    response = requests.post(
        f"{BASE_URL}/api/admin/rag_instances/create",
        json={
            "rag_id": "medical_kb",
            "description": "医疗知识库",
            "working_dir": "./rag_data/medical",
            "workspace": "medical",
            "chunk_token_size": 1500,
            "cosine_threshold": 0.35
        }
    )
    return response.json()

# 2. 批量插入文档
def insert_documents():
    documents = [
        {
            "content": "糖尿病是一种代谢性疾病...",
            "file_path": "diabetes.txt"
        },
        {
            "content": "高血压是常见的心血管疾病...",
            "file_path": "hypertension.txt"
        }
    ]

    response = requests.post(
        f"{BASE_URL}/api/documents/batch_insert",
        json={
            "rag_id": "medical_kb",
            "documents": documents
        }
    )
    return response.json()

# 3. 创建实体和关系
def create_knowledge_graph():
    # 创建实体
    entities = ["糖尿病", "胰岛素", "血糖"]
    for entity in entities:
        requests.post(
            f"{BASE_URL}/api/graph/entities/create",
            json={
                "rag_id": "medical_kb",
                "entity_name": entity,
                "description": f"{entity}相关描述",
                "entity_type": "MEDICAL_TERM"
            }
        )

    # 创建关系
    requests.post(
        f"{BASE_URL}/api/graph/relations/create",
        json={
            "rag_id": "medical_kb",
            "source_entity": "糖尿病",
            "target_entity": "胰岛素",
            "description": "缺乏或抵抗",
            "weight": 0.9
        }
    )

# 4. 查询
def query_knowledge():
    response = requests.post(
        f"{BASE_URL}/api/query/",
        json={
            "rag_id": "medical_kb",
            "question": "糖尿病的主要症状有哪些？",
            "mode": "hybrid",
            "top_k": 20
        }
    )
    return response.json()

# 5. 导出数据
def export_data():
    response = requests.post(
        f"{BASE_URL}/api/graph/export",
        json={
            "rag_id": "medical_kb",
            "output_path": "./exports/medical_kg.csv",
            "file_format": "csv"
        }
    )
    return response.json()

# 执行示例
if __name__ == "__main__":
    print("1. 创建 RAG 实例...")
    print(create_rag_instance())

    print("\n2. 插入文档...")
    print(insert_documents())

    print("\n3. 创建知识图谱...")
    create_knowledge_graph()

    print("\n4. 查询知识库...")
    print(query_knowledge())

    print("\n5. 导出数据...")
    print(export_data())
```

### JavaScript 示例

```javascript
const BASE_URL = "http://localhost:8000";

// 1. 创建 RAG 实例
async function createRAGInstance() {
  const response = await fetch(`${BASE_URL}/api/admin/rag_instances/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rag_id: "my_kb",
      description: "My Knowledge Base",
      working_dir: "./rag_data/kb1",
      workspace: "default"
    })
  });
  return await response.json();
}

// 2. 插入文档
async function insertDocument() {
  const response = await fetch(`${BASE_URL}/api/documents/insert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rag_id: "my_kb",
      content: "Your document content...",
      file_path: "document.txt"
    })
  });
  return await response.json();
}

// 3. 查询
async function query() {
  const response = await fetch(`${BASE_URL}/api/query/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rag_id: "my_kb",
      question: "Your question?",
      mode: "hybrid"
    })
  });
  return await response.json();
}

// 执行
(async () => {
  console.log('Creating RAG instance...');
  console.log(await createRAGInstance());

  console.log('Inserting document...');
  console.log(await insertDocument());

  console.log('Querying...');
  console.log(await query());
})();
```

### cURL 示例

```bash
# 1. 创建 RAG 实例
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_kb",
    "working_dir": "./rag_data/kb1",
    "workspace": "default"
  }'

# 2. 插入文档
curl -X POST "http://localhost:8000/api/documents/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_kb",
    "content": "Document content...",
    "file_path": "doc.txt"
  }'

# 3. 查询
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_kb",
    "question": "Your question?",
    "mode": "hybrid"
  }'
```

## 🔗 WebSocket 使用

```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket 已连接');

  // 发送查询
  ws.send(JSON.stringify({
    type: "query",
    rag_id: "my_kb",
    question: "你的问题?",
    mode: "hybrid"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);

  if (data.type === "answer") {
    console.log('回答:', data.context);
  }
};
```

## 📝 最佳实践

1. **先创建 RAG 实例**: 使用其他功能前必须先创建实例
2. **选择合适的查询模式**: 大多数情况推荐使用 `hybrid` 模式
3. **使用批量操作**: 批量插入可以提高性能
4. **定期清除缓存**: 大量更新后建议清除缓存
5. **合理设置参数**: 根据实际需求调整 `top_k`、`chunk_token_size` 等参数
6. **启用缓存**: 设置 `enable_llm_cache=true` 加速重复查询

## 🆘 常见问题

### Q: RAG 实例不存在
**A:** 确保先调用创建实例接口，并使用正确的 `rag_id`

### Q: 查询结果不理想
**A:** 尝试以下方法:
- 调整查询模式 (hybrid 模式通常效果最好)
- 增加 `top_k` 值
- 调整 `cosine_threshold` 阈值
- 确保文档已正确插入

### Q: 如何查看文档处理状态
**A:** 使用 `/api/documents/status/{rag_id}` 查看统计，使用 `/api/documents/list/{rag_id}/{status}` 查看详细列表

### Q: 如何清除所有数据
**A:** 删除 RAG 实例即可: `DELETE /api/admin/rag_instances/{rag_id}`

## 📚 更多信息

- **完整 API 文档**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **项目结构说明**: [API_STRUCTURE.md](API_STRUCTURE.md)
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**版本**: v3.0.0
**最后更新**: 2025-01-15
