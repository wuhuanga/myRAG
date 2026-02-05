# myRAG API 文档

**版本：** 4.0.0  
**最后更新：** 2026-02-01  
**服务名称：** RAG Backend API  
**基础URL：** `http://localhost:8000`

---

## 目录

1. [概述](#1-概述)
2. [管理接口](#2-管理接口)
3. [文档管理接口](#3-文档管理接口)
4. [查询接口](#4-查询接口)
5. [图谱管理接口](#5-图谱管理接口)
6. [错误码说明](#6-错误码说明)

---

## 1. 概述

### 1.1 版本特性

**v4.0.0 新特性：**
- ✅ 支持多知识库并发查询（Scatter-Gather 模式）
- ✅ 所有查询接口支持 `rag_id` 和 `rag_ids` 参数
- ✅ 新增全量文档状态列表接口
- ✅ 修复文档状态统计字段
- ✅ 优化 NebulaGraph 查询语法

### 1.2 认证方式

当前版本暂不需要认证。

### 1.3 通用响应格式

成功响应：
```json
{
  "status": "success",
  "data": { ... }
}
```

错误响应：
```json
{
  "detail": "错误信息"
}
```

---

## 2. 管理接口

### 2.1 健康检查

**接口：** `GET /api/admin/health`

**描述：** 检查服务健康状态和 RAG 实例数量

**请求示例：**
```bash
curl "http://localhost:8000/api/admin/health"
```

**响应示例：**
```json
{
  "status": "healthy",
  "rag_instances_count": 3,
  "ucd_initialized": false,
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

---

### 2.2 创建 RAG 实例

**接口：** `POST /api/admin/rag_instances/create`

**描述：** 创建新的 RAG 知识库实例

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库唯一标识 |
| workspace | string | 否 | 工作空间名称 |
| working_dir | string | 否 | 工作目录路径 |
| llm_model | string | 否 | LLM 模型名称 |
| embedding_model | string | 否 | 向量模型名称 |
| kv_storage | string | 否 | KV 存储类型 (json/mongo/redis/postgres) |
| vector_storage | string | 否 | 向量存储类型 (milvus) |
| graph_storage | string | 否 | 图存储类型 (nebula/neo4j) |
| doc_status_storage | string | 否 | 文档状态存储类型 |
| entity_extract_max_gleaning | integer | 否 | 实体提取迭代次数（默认1，设为0可提升性能） |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "workspace": "medical_kb",
    "working_dir": "storage_001",
    "entity_extract_max_gleaning": 0
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "RAG 实例 'rag_001' 创建成功",
  "rag_id": "rag_001",
  "working_dir": "storage_001",
  "workspace": "medical_kb",
  "llm_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small"
}
```

---

### 2.3 列出所有 RAG 实例

**接口：** `GET /api/admin/rag_instances/list`

**描述：** 获取所有 RAG 实例列表

**请求示例：**
```bash
curl "http://localhost:8000/api/admin/rag_instances/list"
```

**响应示例：**
```json
[
  {
    "rag_id": "rag_001",
    "workspace": "medical_kb",
    "working_dir": "storage_001",
    "created_at": "2026-01-30T08:00:00",
    "llm_model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-small"
  }
]
```

---

### 2.4 获取 RAG 实例详情

**接口：** `GET /api/admin/rag_instances/{rag_id}`

**描述：** 获取指定 RAG 实例的详细配置信息

**请求示例：**
```bash
curl "http://localhost:8000/api/admin/rag_instances/rag_001"
```

**响应示例：**
```json
{
  "status": "success",
  "rag_id": "rag_001",
  "working_dir": "storage_001",
  "workspace": "medical_kb",
  "created_at": "2026-01-30T08:00:00",
  "llm_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small",
  "embedding_dim": 1536,
  "config": {
    "kv_storage": "JsonKVStorage",
    "vector_storage": "MilvusVectorDBStorage",
    "graph_storage": "NebulaGraphStorage",
    "doc_status_storage": "JsonDocStatusStorage",
    "top_k": 60,
    "chunk_top_k": 5,
    "max_entity_tokens": 4000
  }
}
```


### 2.5 删除 RAG 实例（内存）

**接口：** `DELETE /api/admin/rag_instances/{rag_id}`

**描述：** 删除内存中的 RAG 实例，保留存储数据

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/rag_001"
```

**响应示例：**
```json
{
  "status": "success",
  "message": "RAG 实例 'rag_001' 已删除（存储数据保留）",
  "rag_id": "rag_001"
}
```

---

### 2.6 彻底删除 RAG 实例

**接口:** `DELETE /api/admin/rag_instances/{rag_id}/complete`

**描述：** 彻底删除 RAG 实例及其所有存储数据（不可逆）

**查询参数：**
- `cleanup_storage`: `boolean` (默认 `true`)

**⚠️ 警告：** 此操作将永久删除该 workspace 的所有数据：
- NebulaGraph 中的所有图数据（节点和边）
- Milvus 中的所有 Collections（向量数据）
- 工作目录中的所有文件

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/rag_001/complete?cleanup_storage=true"
```

**响应示例：**
```json
{
  "status": "success",
  "message": "RAG 实例 'rag_001' 及其所有数据已彻底删除",
  "rag_id": "rag_001",
  "cleaned_resources": [
    "NebulaGraph图数据",
    "Milvus向量数据",
    "工作目录文件"
  ]
}
```

---

### 2.7 初始化 UCD 建模器

**接口：** `POST /api/admin/ucd/init`

**描述：** 初始化 UCD（用例图）建模器

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| base_url | string | 否 | http://localhost:4000 | API 基础URL |
| api_key | string | 否 | sk-1234 | API 密钥 |
| model_name | string | 否 | gpt-4 | 模型名称 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/admin/ucd/init" \\
  -H "Content-Type: application/json" \\
  -d '{
    "base_url": "http://localhost:4000",
    "api_key": "sk-your-key",
    "model_name": "gpt-4"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "UCD 建模器初始化成功",
  "config": {
    "base_url": "http://localhost:4000",
    "model_name": "gpt-4"
  }
}
```

---

## 3. 文档管理接口

### 3.1 上传文档

**接口：** `POST /api/documents/upload`

**描述：** 上传文件并处理（提取实体和关系）

**请求类型：** `multipart/form-data`

**请求参数：**
- `rag_id`: `string` (必填) - 知识库 ID
- `file`: `file` (必填) - 文件对象
- `custom_id`: `string` (选填) - 自定义文档 ID

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \\
  -F "rag_id=rag_001" \\
  -F "file=@document.pdf" \\
  -F "custom_id=doc_001"
```

**响应示例：**
```json
{
  "status": "success",
  "message": "文档 document.pdf 已成功上传并处理",
  "file_path": "uploaded_files/rag_001_document.pdf",
  "custom_id": "doc_001",
  "rag_id": "rag_001"
}
```

---

### 3.2 插入文档内容

**接口：** `POST /api/documents/insert`

**描述：** 直接插入文本内容作为文档

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| content | string | 是 | 文档内容 |
| file_path | string | 是 | 文件名或路径 |
| doc_id | string | 否 | 自定义文档 ID |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/documents/insert" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "content": "这是一篇关于人工智能的文章...",
    "file_path": "ai_article.txt",
    "doc_id": "doc_002"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "文档内容已成功插入(文件: ai_article.txt)",
  "file_path": "ai_article.txt",
  "doc_id": "doc_002",
  "content_length": 1500,
  "rag_id": "rag_001"
}
```

---

### 3.3 批量插入文档

**接口：** `POST /api/documents/batch_insert`

**描述：** 批量插入多个文档内容

**请求参数：**
```json
{
  "rag_id": "string (必填)",
  "documents": [
    {
      "content": "string (必填)",
      "file_path": "string (必填)",
      "doc_id": "string (选填)"
    }
  ]
}
```

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/documents/batch_insert" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "documents": [
      {"content": "第一篇文档...", "file_path": "doc1.txt"},
      {"content": "第二篇文档...", "file_path": "doc2.txt"}
    ]
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "成功批量插入 2 个文档",
  "count": 2,
  "files": ["doc1.txt", "doc2.txt"],
  "rag_id": "rag_001"
}
```

---

### 3.4 获取文档状态统计

**接口：** `GET /api/documents/status/{rag_id}`

**描述：** 获取指定知识库的文档处理状态统计

**请求示例：**
```bash
curl "http://localhost:8000/api/documents/status/rag_001"
```

**响应示例：**
```json
{
  "total": 10,
  "processed": 8,
  "pending": 1,
  "processing": 1,
  "failed": 0,
  "status_counts": {
    "processed": 8,
    "pending": 1,
    "processing": 1,
    "failed": 0
  }
}
```

**状态说明：**
- `pending`: 待处理 - 文档在队列中等待处理
- `processing`: 处理中 - 正在提取实体和关系
- `processed`: 已处理 - 处理完成，可以查询
- `failed`: 失败 - 处理过程中出错


### 3.5 按状态获取文档列表

**接口：** `GET /api/documents/list/{rag_id}/{status}`

**描述：** 获取指定状态的文档列表

**路径参数：**
- `rag_id`: 知识库 ID
- `status`: 文档状态 (`PROCESSED` / `PENDING` / `FAILED`)

**请求示例：**
```bash
curl "http://localhost:8000/api/documents/list/rag_001/PROCESSED"
```

**响应示例：**
```json
{
  "status": "PROCESSED",
  "count": 8,
  "documents": [
    {
      "doc_id": "3749dba1-5520-45ea-b7d7-d2250691fdbd",
      "file_name": "uploaded_files/rag_001_document.pdf",
      "created_at": "2026-01-30T08:05:24.071676+00:00",
      "updated_at": "2026-01-30T08:09:13.760415+00:00",
      "error_message": null,
      "status": "PROCESSED"
    }
  ]
}
```

---

### 3.6 获取全量文档状态列表

**接口：** `GET /api/documents/doc_status/{rag_id}`

**描述：** 获取指定知识库的所有文档详细状态（专门用于数据同步）

**请求示例：**
```bash
curl "http://localhost:8000/api/documents/doc_status/rag_001"
```

**响应示例：**
```json
{
  "rag_id": "rag_001",
  "total": 10,
  "doc_status_summary": {
    "PROCESSED": 8,
    "PENDING": 1,
    "PROCESSING": 1,
    "FAILED": 0
  },
  "doc_status_list": [
    {
      "doc_id": "3749dba1-5520-45ea-b7d7-d2250691fdbd",
      "file_name": "document.pdf",
      "status": "processed",
      "created_at": "2026-01-30T08:05:24.071676+00:00",
      "updated_at": "2026-01-30T08:09:13.760415+00:00",
      "error_message": null
    }
  ]
}
```

---

### 3.7 删除文档

**接口：** `DELETE /api/documents/delete/{rag_id}/{doc_id}`

**描述：** 删除指定文档及其所有关联数据

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/documents/delete/rag_001/3749dba1-5520-45ea-b7d7-d2250691fdbd"
```

**响应示例：**
```json
{
  "status": "success",
  "doc_id": "3749dba1-5520-45ea-b7d7-d2250691fdbd",
  "file_path": "uploaded_files/rag_001_document.pdf",
  "message": "文档及其关联数据已成功删除",
  "rag_id": "rag_001",
  "file_deleted": true,
  "file_delete_message": "原始文件已删除: rag_001_document.pdf"
}
```

---

## 4. 查询接口

### 4.1 查询知识库

**接口：** `POST /api/query/`

**描述：** 查询知识库并生成回答（⭐ 支持单知识库和多知识库）

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 选填* | - | 单知识库 ID |
| rag_ids | string[] | 选填* | - | 多知识库 ID 列表 |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式 (naive/local/global/hybrid) |
| only_need_context | boolean | 否 | false | 是否只返回上下文 |
| top_k | integer | 否 | 60 | 图谱检索数量 |
| chunk_top_k | integer | 否 | 5 | 文档块检索数量 |
| max_entity_tokens | integer | 否 | 4000 | 实体token上限 |
| max_relation_tokens | integer | 否 | 4000 | 关系token上限 |
| max_total_tokens | integer | 否 | 10000 | 总token上限 |
| stream | boolean | 否 | false | 是否流式返回 |
| enable_rerank | boolean | 否 | true | 是否启用重排序 |
| response_type | string | 否 | - | 响应类型 (simple/full) |
| hl_keywords | string[] | 否 | - | 高优先级关键字 |
| ll_keywords | string[] | 否 | - | 低优先级关键字 |

\* `rag_id` 和 `rag_ids` 必须提供其一

**单知识库请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "question": "什么是人工智能？",
    "mode": "hybrid"
  }'
```

**单知识库响应示例：**
```json
{
  "rag_ids": ["rag_001"],
  "question": "什么是人工智能？",
  "answer": "人工智能（AI）是计算机科学的一个分支...",
  "mode": "hybrid",
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

**多知识库请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_ids": ["rag_001", "rag_002"],
    "question": "什么是人工智能？",
    "mode": "hybrid"
  }'
```

**多知识库响应示例：**
```json
{
  "rag_ids": ["rag_001", "rag_002"],
  "question": "什么是人工智能？",
  "answer": "【知识库: rag_001】\\n人工智能（AI）是...\\n\\n【知识库: rag_002】\\n从法律角度看...",
  "mode": "hybrid",
  "timestamp": "2026-02-01T10:30:00.123456",
  "sources": [
    {"rag_id": "rag_001", "answer_length": 500},
    {"rag_id": "rag_002", "answer_length": 450}
  ]
}
```

**查询模式说明：**
- `naive`: 仅使用向量检索
- `local`: 向量检索 + 实体关系
- `global`: 全局图谱检索
- `hybrid`: 混合模式（推荐）

---

### 4.2 关键字检索

**接口：** `POST /api/query/keywords`

**描述：** 使用关键字列表检索知识库（⭐ 支持单知识库和多知识库）

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 选填* | - | 单知识库 ID |
| rag_ids | string[] | 选填* | - | 多知识库 ID 列表 |
| keywords | string[] | 是 | - | 关键字列表 |
| mode | string | 否 | hybrid | 查询模式 |
| only_need_context | boolean | 否 | true | 是否只返回上下文 |
| enable_rerank | boolean | 否 | true | 是否启用重排序 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/keywords" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_ids": ["rag_001", "rag_002"],
    "keywords": ["人工智能", "机器学习"]
  }'
```

**响应示例：**
```json
{
  "rag_ids": ["rag_001", "rag_002"],
  "keywords": ["人工智能", "机器学习"],
  "context": "【知识库: rag_001】\\n检索到的内容...\\n\\n【知识库: rag_002】\\n检索到的内容...",
  "mode": "hybrid",
  "timestamp": "2026-02-01T10:30:00.123456",
  "sources": [
    {"rag_id": "rag_001", "context_length": 2500},
    {"rag_id": "rag_002", "context_length": 1800}
  ]
}
```


### 4.3 UCD 建模查询

**接口：** `POST /api/query/ucd`

**描述：** 执行查询并进行 UCD（用例图）建模（⭐ 支持单知识库和多知识库）

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 选填* | - | 单知识库 ID |
| rag_ids | string[] | 选填* | - | 多知识库 ID 列表 |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式 |
| out_json | string | 否 | - | 输出JSON文件路径 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/ucd" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "question": "描述用户登录流程",
    "mode": "hybrid",
    "out_json": "ucd_output.json"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "rag_ids": ["rag_001"],
  "question": "描述用户登录流程",
  "context": "检索到的上下文...",
  "ucd_model": {
    "use_cases": [...],
    "actors": [...]
  },
  "output_file": "ucd_output.json",
  "mode": "hybrid",
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

---

### 4.4 清除 LLM 缓存

**接口：** `POST /api/query/clear_cache`

**描述：** 清除指定知识库的 LLM 缓存

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| cache_type | string | 是 | 缓存类型 (llm_cache/all) |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/clear_cache" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "cache_type": "llm_cache"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "RAG 实例 rag_001 的 LLM 缓存已清除",
  "rag_id": "rag_001",
  "cache_type": "llm_cache"
}
```

---

### 4.5 图谱清理检索

**接口：** `POST /api/query/graph-clean`

**描述：** 使用关键字检索知识图谱，返回清理后的实体和关系（⭐ 支持单知识库和多知识库）

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 选填* | 单知识库 ID |
| rag_ids | string[] | 选填* | 多知识库 ID 列表 |
| keywords | string[] | 否 | 关键字列表（可为空） |
| enable_rerank | boolean | 否 | 是否启用重排序 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/graph-clean" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_ids": ["rag_001"],
    "keywords": ["人工智能", "深度学习"]
  }'
```

**响应示例：**
```json
{
  "rag_ids": ["rag_001"],
  "keywords": ["人工智能", "深度学习"],
  "entities": [
    {
      "entity_name": "人工智能",
      "description": "计算机科学的一个分支",
      "entity_type": "CONCEPT"
    },
    {
      "entity_name": "深度学习",
      "description": "机器学习的子领域",
      "entity_type": "TECHNOLOGY"
    }
  ],
  "relationships": [
    {
      "src_id": "深度学习",
      "tgt_id": "人工智能",
      "description": "深度学习是人工智能的重要分支",
      "keywords": "机器学习"
    }
  ],
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

---

### 4.6 仅检索文档块

**接口：** `POST /api/query/chunks-only`

**描述：** 使用关键字检索，只返回文档 chunks（⭐ 支持单知识库和多知识库）

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 选填* | 单知识库 ID |
| rag_ids | string[] | 选填* | 多知识库 ID 列表 |
| keywords | string[] | 否 | 关键字列表（可为空） |
| chunk_top_k | integer | 否 | 返回文档块数量 |
| enable_rerank | boolean | 否 | 是否启用重排序 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/query/chunks-only" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_ids": ["rag_001", "rag_002"],
    "keywords": ["人工智能"],
    "chunk_top_k": 5
  }'
```

**响应示例：**
```json
{
  "rag_ids": ["rag_001", "rag_002"],
  "keywords": ["人工智能"],
  "chunks": [
    {
      "content": "人工智能是计算机科学的一个重要分支...",
      "file_path": "uploaded_files/rag_001_document.pdf",
      "chunk_id": "chunk_001",
      "reference_id": "ref_001"
    }
  ],
  "timestamp": "2026-02-01T10:30:00.123456",
  "sources": [
    {"rag_id": "rag_001", "chunks_count": 3},
    {"rag_id": "rag_002", "chunks_count": 2}
  ]
}
```

---

## 5. 图谱管理接口

### 5.1 获取完整图谱（ECharts 格式）

**接口：** `GET /api/graph/echarts`

**描述：** 获取知识库的完整知识图谱（⭐ 支持单知识库和多知识库）

**查询参数：**
- `rag_ids`: `string[]` (必填) - 知识库 ID 列表（可传入一个或多个）

**单知识库请求示例：**
```bash
curl "http://localhost:8000/api/graph/echarts?rag_ids=rag_001"
```

**单知识库响应示例：**
```json
{
  "status": "success",
  "rag_ids": ["rag_001"],
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "symbolSize": 50,
        "category": 0,
        "description": "计算机科学的一个分支",
        "degree": 15
      }
    ],
    "links": [
      {
        "source": "深度学习",
        "target": "人工智能",
        "description": "深度学习是人工智能的子领域"
      }
    ],
    "categories": [
      {"name": "CONCEPT"},
      {"name": "TECHNOLOGY"}
    ]
  }
}
```

**多知识库请求示例：**
```bash
curl "http://localhost:8000/api/graph/echarts?rag_ids=rag_001&rag_ids=rag_002"
```

**多知识库响应示例：**
```json
{
  "status": "success",
  "rag_ids": ["rag_001", "rag_002"],
  "data": {
    "nodes": [...],
    "links": [...],
    "categories": [...]
  },
  "sources": [
    {"rag_id": "rag_001", "nodes_count": 229, "links_count": 418},
    {"rag_id": "rag_002", "nodes_count": 150, "links_count": 280}
  ]
}
```

---

### 5.2 获取 Top-K 度数子图

**接口：** `GET /api/graph/echarts/top-k`

**描述：** 获取度数最高的 K 个节点及其子图（⭐ 支持单知识库和多知识库）

**查询参数：**
- `rag_ids`: `string[]` (必填) - 知识库 ID 列表
- `k`: `integer` (选填, 默认 50) - 返回节点数量

**请求示例：**
```bash
curl "http://localhost:8000/api/graph/echarts/top-k?rag_ids=rag_001&k=10"
```

**响应示例：**
```json
{
  "status": "success",
  "rag_ids": ["rag_001"],
  "k": 10,
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "symbolSize": 80,
        "category": 0,
        "description": "计算机科学的一个分支",
        "degree": 25
      }
    ],
    "links": [...],
    "categories": [...]
  }
}
```

---

### 5.3 获取节点邻居子图

**接口：** `GET /api/graph/echarts/neighbors`

**描述：** 获取指定节点的邻居子图（⭐ 支持单知识库和多知识库）

**查询参数：**
- `node_id`: `string` (必填) - 中心节点 ID（实体名）
- `rag_ids`: `string[]` (必填) - 知识库 ID 列表

**请求示例：**
```bash
# URL 编码后的"人工智能"
curl "http://localhost:8000/api/graph/echarts/neighbors?node_id=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD&rag_ids=rag_001"
```

**响应示例：**
```json
{
  "status": "success",
  "node_id": "人工智能",
  "rag_ids": ["rag_001"],
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "symbolSize": 60,
        "category": 0,
        "description": "计算机科学的一个分支",
        "degree": 25
      },
      {
        "id": "机器学习",
        "name": "机器学习",
        "symbolSize": 40,
        "category": 1,
        "description": "人工智能的子领域",
        "degree": 15
      }
    ],
    "links": [
      {
        "source": "机器学习",
        "target": "人工智能",
        "description": "机器学习是人工智能的重要方法"
      }
    ],
    "categories": [...]
  }
}
```


### 5.4 导出图谱数据

**接口：** `POST /api/graph/export`

**描述：** 导出知识图谱数据（JSON 或 GraphML 格式）

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 是 | - | 知识库 ID |
| format | string | 否 | json | 导出格式 (json/graphml) |
| output_path | string | 否 | - | 输出文件路径 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/export" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "format": "json",
    "output_path": "graph_export.json"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "图谱数据已导出",
  "rag_id": "rag_001",
  "format": "json",
  "output_path": "graph_export.json",
  "nodes_count": 229,
  "edges_count": 418
}
```

---

### 5.5 多知识库图谱合并

**接口：** `POST /api/graph/echarts/multi`

**描述：** 合并多个知识库的图谱数据（POST 方式，支持复杂参数）

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_ids | string[] | 是 | - | 知识库 ID 列表 |
| merge_strategy | string | 否 | union | 合并策略 (union/intersection) |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/echarts/multi" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_ids": ["rag_001", "rag_002"],
    "merge_strategy": "union"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "rag_ids": ["rag_001", "rag_002"],
  "merge_strategy": "union",
  "data": {
    "nodes": [...],
    "links": [...],
    "categories": [...]
  },
  "sources": [
    {"rag_id": "rag_001", "nodes_count": 229},
    {"rag_id": "rag_002", "nodes_count": 150}
  ]
}
```

---

### 5.6 创建实体

**接口：** `POST /api/graph/entities/create`

**描述：** 手动创建新实体

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 是 | - | 知识库 ID |
| entity_name | string | 是 | - | 实体名称 |
| description | string | 否 | - | 实体描述 |
| entity_type | string | 否 | UNKNOWN | 实体类型 |
| source_id | string | 否 | manual_creation | 来源ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/entities/create" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "entity_name": "量子计算",
    "description": "利用量子力学原理进行计算的技术",
    "entity_type": "TECHNOLOGY"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "实体 '量子计算' 已创建",
  "entity_name": "量子计算",
  "rag_id": "rag_001"
}
```

---

### 5.7 编辑实体

**接口：** `POST /api/graph/entities/edit`

**描述：** 编辑现有实体信息

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 是 | - | 知识库 ID |
| entity_name | string | 是 | - | 要编辑的实体名称 |
| updated_data | object | 是 | - | 更新数据 |
| allow_rename | boolean | 否 | true | 是否允许重命名 |

**updated_data 对象：**
| 字段 | 类型 | 说明 |
|------|------|------|
| entity_name | string | 新名称（重命名） |
| description | string | 新描述 |
| entity_type | string | 新类型 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/entities/edit" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "entity_name": "量子计算",
    "updated_data": {
      "description": "基于量子力学原理的超高性能计算技术",
      "entity_type": "ADVANCED_TECHNOLOGY"
    }
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "实体 '量子计算' 已更新",
  "entity_name": "量子计算",
  "rag_id": "rag_001"
}
```

---

### 5.8 删除实体

**接口：** `POST /api/graph/entities/delete`

**描述：** 删除指定实体及其所有关系

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| entity_name | string | 是 | 要删除的实体名称 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/entities/delete" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "entity_name": "量子计算"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "实体 '量子计算' 及其关系已删除",
  "entity_name": "量子计算",
  "rag_id": "rag_001"
}
```

---

### 5.9 获取实体信息

**接口：** `POST /api/graph/entities/info`

**描述：** 获取指定实体的详细信息

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| entity_name | string | 是 | 实体名称 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/entities/info" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "entity_name": "人工智能"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "entity": {
    "entity_name": "人工智能",
    "description": "计算机科学的一个分支",
    "entity_type": "CONCEPT",
    "source_id": "chunk_001",
    "file_path": "uploaded_files/rag_001_document.pdf",
    "created_at": "2026-01-30T08:00:00"
  },
  "rag_id": "rag_001"
}
```

---

### 5.10 合并实体

**接口：** `POST /api/graph/entities/merge`

**描述：** 将一个实体合并到另一个实体

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| source_entity | string | 是 | 被合并的实体 |
| target_entity | string | 是 | 目标实体 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/entities/merge" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "source_entity": "AI",
    "target_entity": "人工智能"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "实体 'AI' 已合并到 '人工智能'",
  "source_entity": "AI",
  "target_entity": "人工智能",
  "rag_id": "rag_001"
}
```

---

### 5.11 创建关系

**接口：** `POST /api/graph/relations/create`

**描述：** 手动创建两个实体之间的关系

**请求参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| rag_id | string | 是 | - | 知识库 ID |
| source_entity | string | 是 | - | 源实体名称 |
| target_entity | string | 是 | - | 目标实体名称 |
| description | string | 否 | - | 关系描述 |
| keywords | string | 否 | - | 关键字 |
| source_id | string | 否 | manual_creation | 来源ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/relations/create" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "source_entity": "深度学习",
    "target_entity": "神经网络",
    "description": "深度学习基于多层神经网络",
    "keywords": "机器学习, 人工智能"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "关系已创建: 深度学习 -> 神经网络",
  "source_entity": "深度学习",
  "target_entity": "神经网络",
  "rag_id": "rag_001"
}
```

---

### 5.12 编辑关系

**接口：** `POST /api/graph/relations/edit`

**描述：** 编辑现有关系信息

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |
| updated_data | object | 是 | 更新数据 |

**updated_data 对象：**
| 字段 | 类型 | 说明 |
|------|------|------|
| description | string | 新描述 |
| keywords | string | 新关键字 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/relations/edit" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "source_entity": "深度学习",
    "target_entity": "神经网络",
    "updated_data": {
      "description": "深度学习是基于深层神经网络的机器学习方法"
    }
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "关系已更新: 深度学习 -> 神经网络",
  "source_entity": "深度学习",
  "target_entity": "神经网络",
  "rag_id": "rag_001"
}
```

---

### 5.13 删除关系

**接口：** `POST /api/graph/relations/delete`

**描述：** 删除指定的关系

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/relations/delete" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "source_entity": "深度学习",
    "target_entity": "神经网络"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "message": "关系已删除: 深度学习 -> 神经网络",
  "source_entity": "深度学习",
  "target_entity": "神经网络",
  "rag_id": "rag_001"
}
```

---

### 5.14 获取关系信息

**接口：** `POST /api/graph/relations/info`

**描述：** 获取指定关系的详细信息

**请求参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rag_id | string | 是 | 知识库 ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/graph/relations/info" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "rag_001",
    "source_entity": "深度学习",
    "target_entity": "人工智能"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "relation": {
    "source_entity": "深度学习",
    "target_entity": "人工智能",
    "description": "深度学习是人工智能的重要分支",
    "keywords": "机器学习, 神经网络",
    "source_id": "chunk_001",
    "file_path": "uploaded_files/rag_001_document.pdf",
    "created_at": "2026-01-30T08:00:00"
  },
  "rag_id": "rag_001"
}
```

---

## 6. 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在（RAG 实例或文档未找到） |
| 500 | 服务器内部错误 |
| 207 | 多状态（部分成功） |

### 常见错误示例

**RAG 实例不存在：**
```json
{
  "detail": "RAG 实例 'rag_999' 不存在"
}
```

**文档未找到：**
```json
{
  "detail": "文档未找到: doc_id_123"
}
```

**参数错误：**
```json
{
  "detail": "必须提供 rag_id 或 rag_ids 参数之一"
}
```

**查询失败：**
```json
{
  "detail": "所有知识库查询均失败"
}
```

---

## 附录

### A. 多知识库查询说明

v4.0.0 版本支持所有查询接口使用多知识库模式：

**参数规则：**
- 提供 `rag_id`: 单知识库模式
- 提供 `rag_ids`: 多知识库模式
- 两者只能提供其一

**并发模式：**
- 使用 Scatter-Gather 模式并发查询所有知识库
- 真正的并行处理（asyncio.gather），提升性能

**结果合并：**
- 答案/上下文：按知识库拼接
- 图谱数据：合并节点和边
- Chunks：直接合并

**Source 字段：**
多知识库响应会包含 `sources` 字段，标识每个知识库的贡献：
```json
{
  "sources": [
    {"rag_id": "rag_001", "answer_length": 500},
    {"rag_id": "rag_002", "answer_length": 450}
  ]
}
```

### B. 文档状态流转

```
pending (待处理)
    ↓
processing (处理中) → failed (失败)
    ↓
processed (已处理)
```

### C. 性能优化建议

1. **实体提取优化：**
   - 设置 `entity_extract_max_gleaning: 0` 可大幅提升处理速度（减少 LLM 调用次数）
   - 默认值为 1，会进行二次提取以提高准确性

2. **查询优化：**
   - 使用 `enable_rerank: true` 提升检索准确性
   - 调整 `top_k` 和 `chunk_top_k` 平衡性能和质量

3. **缓存管理：**
   - 定期清理 LLM 缓存避免占用过多空间
   - 使用 `/api/query/clear_cache` 接口

### D. 运维和示例脚本

#### D.1 NebulaGraph 管理命令

**启动所有 NebulaGraph 服务：**
```bash
sudo /usr/local/nebula/scripts/nebula.service start all
```

**停止所有 NebulaGraph 服务：**
```bash
sudo /usr/local/nebula/scripts/nebula.service stop all
```

**查看服务状态：**
```bash
sudo /usr/local/nebula/scripts/nebula.service status all
```

#### D.2 Milvus 管理命令

**安装 Milvus（Debian/Ubuntu）：**
```bash
apt install -y ./milvus_2.6.4-1_amd64.deb
```

**启动 Milvus 服务：**
```bash
systemctl start milvus
```

**查看 Milvus 状态：**
```bash
systemctl status milvus
```

**停止 Milvus 服务：**
```bash
systemctl stop milvus
```

#### D.3 API 服务器启动

**使用 tmux 启动并记录日志：**
```bash
# 创建新的 tmux 会话
tmux new -s myrag

# 启动 API 服务器并记录日志
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 |& tee log.txt

# 分离会话：按 Ctrl+B，然后按 D
# 重新连接：tmux attach -t myrag
```

**Docker Compose 启动（推荐）：**
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f rag-api

# 停止所有服务
docker-compose down
```

#### D.4 完整示例工作流

以下是一个完整的端到端工作流脚本示例：

```bash
#!/bin/bash

# myRAG 完整示例工作流
# 演示如何创建 RAG 实例、上传文档、查询知识库

BASE_URL="http://localhost:8000"

echo "========================================="
echo "1. 健康检查"
echo "========================================="
curl -X GET "${BASE_URL}/api/admin/health" | jq
sleep 1

echo ""
echo "========================================="
echo "2. 创建 RAG 实例"
echo "========================================="
curl -X POST "${BASE_URL}/api/admin/rag_instances/create" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "demo_rag",
    "workspace": "demo_workspace",
    "working_dir": "demo_storage",
    "entity_extract_max_gleaning": 0
  }' | jq
sleep 2

echo ""
echo "========================================="
echo "3. 上传文档"
echo "========================================="
curl -X POST "${BASE_URL}/api/documents/upload" \\
  -F "rag_id=demo_rag" \\
  -F "file=@test_document.txt" \\
  -F "custom_id=doc_001" | jq
sleep 1

echo ""
echo "========================================="
echo "4. 查看文档处理状态"
echo "========================================="
curl -X GET "${BASE_URL}/api/documents/status/demo_rag" | jq
sleep 1

echo ""
echo "========================================="
echo "5. 查询知识库"
echo "========================================="
curl -X POST "${BASE_URL}/api/query/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "rag_id": "demo_rag",
    "question": "文档主要内容是什么？",
    "mode": "hybrid"
  }' | jq
sleep 1

echo ""
echo "========================================="
echo "6. 获取知识图谱（ECharts 格式）"
echo "========================================="
curl -X GET "${BASE_URL}/api/graph/echarts?rag_ids=demo_rag" | jq
sleep 1

echo ""
echo "========================================="
echo "7. 获取 Top-K 度数子图"
echo "========================================="
curl -X GET "${BASE_URL}/api/graph/echarts/top-k?rag_ids=demo_rag&k=10" | jq
sleep 1

echo ""
echo "========================================="
echo "8. 列出所有 RAG 实例"
echo "========================================="
curl -X GET "${BASE_URL}/api/admin/rag_instances/list" | jq
sleep 1

echo ""
echo "========================================="
echo "工作流执行完成！"
echo "========================================="
```

**使用方法：**
1. 将上述脚本保存为 `test_workflow.sh`
2. 准备测试文档 `test_document.txt`
3. 赋予执行权限：`chmod +x test_workflow.sh`
4. 运行：`./test_workflow.sh`

**注意事项：**
- 脚本使用 `jq` 格式化 JSON 输出，请确保已安装：`apt install jq`
- 确保 NebulaGraph 和 Milvus 服务已启动
- 确保 API 服务器正在运行

---

**文档结束**

**版本历史：**
- v4.0.0 (2026-02-01): 多知识库支持、全量文档状态接口、NebulaGraph查询优化
- v3.0.0: 模块化架构、多实例支持
- v2.0.0: 基础 RAG 功能

**技术支持：** 请提交 Issue 到项目仓库
