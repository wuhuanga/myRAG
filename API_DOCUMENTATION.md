# RAG Backend API 接口文档

## 目录

- [1. 系统管理接口](#1-系统管理接口)
  - [1.1 健康检查](#11-健康检查)
  - [1.2 创建 RAG 实例](#12-创建-rag-实例)
  - [1.3 列出所有 RAG 实例](#13-列出所有-rag-实例)
  - [1.4 获取 RAG 实例详情](#14-获取-rag-实例详情)
  - [1.5 删除 RAG 实例](#15-删除-rag-实例)
  - [1.6 初始化 UCD 建模器](#16-初始化-ucd-建模器)
- [2. 文档管理接口](#2-文档管理接口)
  - [2.1 上传文档](#21-上传文档)
  - [2.2 插入文档内容](#22-插入文档内容)
  - [2.3 批量插入文档](#23-批量插入文档)
  - [2.4 获取文档状态统计](#24-获取文档状态统计)
  - [2.5 获取指定状态的文档列表](#25-获取指定状态的文档列表)
- [3. 查询接口](#3-查询接口)
  - [3.1 查询知识库](#31-查询知识库)
  - [3.2 UCD 建模查询](#32-ucd-建模查询)
  - [3.3 清除缓存](#33-清除缓存)
- [4. 图操作接口 - 实体管理](#4-图操作接口---实体管理)
  - [4.1 创建实体](#41-创建实体)
  - [4.2 编辑实体](#42-编辑实体)
  - [4.3 删除实体](#43-删除实体)
  - [4.4 获取实体信息](#44-获取实体信息)
  - [4.5 合并实体](#45-合并实体)
- [5. 图操作接口 - 关系管理](#5-图操作接口---关系管理)
  - [5.1 创建关系](#51-创建关系)
  - [5.2 编辑关系](#52-编辑关系)
  - [5.3 删除关系](#53-删除关系)
  - [5.4 获取关系信息](#54-获取关系信息)
- [6. 数据导出接口](#6-数据导出接口)
  - [6.1 导出知识图谱数据](#61-导出知识图谱数据)
- [7. WebSocket 接口](#7-websocket-接口)
  - [7.1 实时查询](#71-实时查询)
  - [7.2 实体操作](#72-实体操作)
  - [7.3 UCD 建模](#73-ucd-建模)

---

## 1. 系统管理接口

### 1.1 健康检查

检查系统运行状态和 RAG 实例数量。

**接口地址**

```
GET /api/admin/health
```

**请求参数**

无

**响应示例**

```json
{
  "status": "healthy",
  "rag_instances_count": 2,
  "ucd_initialized": true,
  "timestamp": "2025-01-15T10:30:00.123456"
}
```

**调用示例 (curl)**

```bash
curl -X GET "http://localhost:8000/api/admin/health"
```

**调用示例 (Python)**

```python
import requests

response = requests.get("http://localhost:8000/api/admin/health")
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
fetch('http://localhost:8000/api/admin/health')
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 1.2 创建 RAG 实例

创建一个新的 RAG 实例，可以配置各种参数。

**接口地址**

```
POST /api/admin/rag_instances/create
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例的唯一标识符 |
| description | string | 否 | null | 实例描述 |
| working_dir | string | 是 | - | 工作目录路径 |
| workspace | string | 是 | - | 工作空间名称 |
| kv_storage | string | 否 | null | KV 存储类型 |
| vector_storage | string | 否 | null | 向量存储类型 |
| graph_storage | string | 否 | null | 图存储类型 |
| doc_status_storage | string | 否 | null | 文档状态存储类型 |
| top_k | integer | 否 | null | 查询返回的 top k 结果 |
| chunk_top_k | integer | 否 | null | 分块查询返回的 top k 结果 |
| max_entity_tokens | integer | 否 | null | 实体的最大 token 数 |
| max_relation_tokens | integer | 否 | null | 关系的最大 token 数 |
| max_total_tokens | integer | 否 | null | 总的最大 token 数 |
| cosine_threshold | float | 否 | 0.3 | 余弦相似度阈值 |
| related_chunk_number | integer | 否 | 5 | 相关分块数量 |
| chunk_token_size | integer | 否 | 1200 | 分块 token 大小 |
| chunk_overlap_token_size | integer | 否 | 100 | 分块重叠 token 大小 |
| enable_llm_cache | boolean | 否 | true | 是否启用 LLM 缓存 |
| enable_llm_cache_for_entity_extract | boolean | 否 | true | 是否为实体提取启用 LLM 缓存 |
| llm_model | string | 否 | null | LLM 模型名称 |
| embedding_model | string | 否 | null | Embedding 模型名称 |
| embedding_dim | integer | 否 | null | Embedding 维度 |
| embedding_max_token | integer | 否 | null | Embedding 最大 token 数 |
| litellm_url | string | 否 | null | LiteLLM 服务地址 |
| litellm_key | string | 否 | null | LiteLLM API 密钥 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "description": "医疗知识图谱实例",
  "working_dir": "./rag_data/medical",
  "workspace": "medical_workspace",
  "cosine_threshold": 0.35,
  "chunk_token_size": 1500,
  "chunk_overlap_token_size": 150,
  "enable_llm_cache": true,
  "enable_llm_cache_for_entity_extract": true,
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "RAG 实例 'medical_knowledge' 创建成功",
  "rag_id": "medical_knowledge",
  "working_dir": "./rag_data/medical",
  "workspace": "medical_workspace",
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "description": "医疗知识图谱实例",
    "working_dir": "./rag_data/medical",
    "workspace": "medical_workspace",
    "cosine_threshold": 0.35,
    "chunk_token_size": 1500
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "description": "医疗知识图谱实例",
    "working_dir": "./rag_data/medical",
    "workspace": "medical_workspace",
    "cosine_threshold": 0.35,
    "chunk_token_size": 1500,
    "enable_llm_cache": True
}

response = requests.post(
    "http://localhost:8000/api/admin/rag_instances/create",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  description: "医疗知识图谱实例",
  working_dir: "./rag_data/medical",
  workspace: "medical_workspace",
  cosine_threshold: 0.35,
  chunk_token_size: 1500
};

fetch('http://localhost:8000/api/admin/rag_instances/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 1.3 列出所有 RAG 实例

获取所有已创建的 RAG 实例列表。

**接口地址**

```
GET /api/admin/rag_instances/list
```

**请求参数**

无

**响应示例**

```json
[
  {
    "rag_id": "medical_knowledge",
    "description": "医疗知识图谱实例",
    "working_dir": "./rag_data/medical",
    "workspace": "medical_workspace",
    "created_at": "2025-01-15T10:00:00.123456",
    "llm_model": "gpt-4",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  {
    "rag_id": "legal_docs",
    "description": "法律文档知识库",
    "working_dir": "./rag_data/legal",
    "workspace": "legal_workspace",
    "created_at": "2025-01-15T11:00:00.123456",
    "llm_model": "gpt-4",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  }
]
```

**调用示例 (curl)**

```bash
curl -X GET "http://localhost:8000/api/admin/rag_instances/list"
```

**调用示例 (Python)**

```python
import requests

response = requests.get("http://localhost:8000/api/admin/rag_instances/list")
instances = response.json()
for instance in instances:
    print(f"RAG ID: {instance['rag_id']}, Description: {instance['description']}")
```

**调用示例 (JavaScript)**

```javascript
fetch('http://localhost:8000/api/admin/rag_instances/list')
  .then(response => response.json())
  .then(instances => {
    instances.forEach(instance => {
      console.log(`RAG ID: ${instance.rag_id}, Description: ${instance.description}`);
    });
  });
```

---

### 1.4 获取 RAG 实例详情

获取指定 RAG 实例的详细配置信息。

**接口地址**

```
GET /api/admin/rag_instances/{rag_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |

**响应示例**

```json
{
  "status": "success",
  "rag_id": "medical_knowledge",
  "working_dir": "./rag_data/medical",
  "workspace": "medical_workspace",
  "created_at": "2025-01-15T10:00:00.123456",
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dim": 384,
  "config": {
    "kv_storage": null,
    "vector_storage": null,
    "graph_storage": null,
    "doc_status_storage": null,
    "top_k": null,
    "chunk_top_k": null,
    "max_entity_tokens": null,
    "max_relation_tokens": null,
    "max_total_tokens": null,
    "cosine_threshold": 0.35,
    "related_chunk_number": 5,
    "chunk_token_size": 1500,
    "chunk_overlap_token_size": 150,
    "enable_llm_cache": true,
    "enable_llm_cache_for_entity_extract": true
  }
}
```

**调用示例 (curl)**

```bash
curl -X GET "http://localhost:8000/api/admin/rag_instances/medical_knowledge"
```

**调用示例 (Python)**

```python
import requests

rag_id = "medical_knowledge"
response = requests.get(f"http://localhost:8000/api/admin/rag_instances/{rag_id}")
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const ragId = "medical_knowledge";
fetch(`http://localhost:8000/api/admin/rag_instances/${ragId}`)
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 1.5 删除 RAG 实例

删除指定的 RAG 实例。

**接口地址**

```
DELETE /api/admin/rag_instances/{rag_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |

**响应示例**

```json
{
  "status": "success",
  "message": "RAG 实例 'medical_knowledge' 已删除",
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/medical_knowledge"
```

**调用示例 (Python)**

```python
import requests

rag_id = "medical_knowledge"
response = requests.delete(f"http://localhost:8000/api/admin/rag_instances/{rag_id}")
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const ragId = "medical_knowledge";
fetch(`http://localhost:8000/api/admin/rag_instances/${ragId}`, {
  method: 'DELETE'
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 1.6 初始化 UCD 建模器

初始化 UCD (Use Case Diagram) 建模器，用于 UCD 建模查询。

**接口地址**

```
POST /api/admin/ucd/init
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| base_url | string | 否 | http://localhost:4000 | LiteLLM 服务地址 |
| api_key | string | 否 | sk-1234 | API 密钥 |
| model_name | string | 否 | gpt-4 | 模型名称 |

**请求示例**

```json
{
  "base_url": "http://localhost:4000",
  "api_key": "sk-your-api-key",
  "model_name": "gpt-4"
}
```

**响应示例**

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

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/admin/ucd/init" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "http://localhost:4000",
    "api_key": "sk-1234",
    "model_name": "gpt-4"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "base_url": "http://localhost:4000",
    "api_key": "sk-1234",
    "model_name": "gpt-4"
}

response = requests.post(
    "http://localhost:8000/api/admin/ucd/init",
    json=data
)
print(response.json())
```

---

## 2. 文档管理接口

### 2.1 上传文档

上传文档文件并插入到指定的 RAG 实例中。

**接口地址**

```
POST /api/documents/upload
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string (query) | 是 | RAG 实例 ID |
| file | file | 是 | 要上传的文档文件 |
| custom_id | string (query) | 否 | 自定义文档 ID |

**响应示例**

```json
{
  "status": "success",
  "message": "文档 medical_paper.pdf 已成功上传并处理",
  "file_path": "uploaded_files/medical_paper.pdf",
  "custom_id": "doc_001",
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/documents/upload?rag_id=medical_knowledge&custom_id=doc_001" \
  -F "file=@/path/to/medical_paper.pdf"
```

**调用示例 (Python)**

```python
import requests

rag_id = "medical_knowledge"
custom_id = "doc_001"
file_path = "/path/to/medical_paper.pdf"

with open(file_path, 'rb') as f:
    files = {'file': f}
    params = {
        'rag_id': rag_id,
        'custom_id': custom_id
    }
    response = requests.post(
        "http://localhost:8000/api/documents/upload",
        params=params,
        files=files
    )
    print(response.json())
```

**调用示例 (JavaScript/FormData)**

```javascript
const formData = new FormData();
const fileInput = document.querySelector('input[type="file"]');
formData.append('file', fileInput.files[0]);

const ragId = "medical_knowledge";
const customId = "doc_001";

fetch(`http://localhost:8000/api/documents/upload?rag_id=${ragId}&custom_id=${customId}`, {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 2.2 插入文档内容

直接插入文档内容（不通过文件上传）。

**接口地址**

```
POST /api/documents/insert
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| content | string | 是 | 文档内容 |
| file_path | string | 是 | 文件路径或文件名称 |
| doc_id | string | 否 | 自定义文档 ID |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "content": "糖尿病是一种代谢性疾病，其特征是血糖水平持续升高。主要分为1型和2型糖尿病...",
  "file_path": "diabetes_overview.txt",
  "doc_id": "diabetes_001"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "文档内容已成功插入（文件: diabetes_overview.txt）",
  "file_path": "diabetes_overview.txt",
  "doc_id": "diabetes_001",
  "content_length": 150,
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/documents/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "content": "糖尿病是一种代谢性疾病，其特征是血糖水平持续升高...",
    "file_path": "diabetes_overview.txt",
    "doc_id": "diabetes_001"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "content": "糖尿病是一种代谢性疾病，其特征是血糖水平持续升高...",
    "file_path": "diabetes_overview.txt",
    "doc_id": "diabetes_001"
}

response = requests.post(
    "http://localhost:8000/api/documents/insert",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  content: "糖尿病是一种代谢性疾病，其特征是血糖水平持续升高...",
  file_path: "diabetes_overview.txt",
  doc_id: "diabetes_001"
};

fetch('http://localhost:8000/api/documents/insert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 2.3 批量插入文档

一次性插入多个文档。

**接口地址**

```
POST /api/documents/batch_insert
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| documents | array | 是 | 文档数组 |
| documents[].content | string | 是 | 文档内容 |
| documents[].file_path | string | 是 | 文件路径 |
| documents[].doc_id | string | 否 | 文档 ID |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "documents": [
    {
      "content": "高血压是一种常见的心血管疾病...",
      "file_path": "hypertension.txt",
      "doc_id": "hypertension_001"
    },
    {
      "content": "冠心病是冠状动脉粥样硬化性心脏病的简称...",
      "file_path": "coronary_heart_disease.txt",
      "doc_id": "chd_001"
    },
    {
      "content": "心律失常是指心脏冲动的频率、节律、起源部位...",
      "file_path": "arrhythmia.txt"
    }
  ]
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "成功批量插入 3 个文档",
  "count": 3,
  "files": [
    "hypertension.txt",
    "coronary_heart_disease.txt",
    "arrhythmia.txt"
  ],
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/documents/batch_insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "documents": [
      {
        "content": "高血压是一种常见的心血管疾病...",
        "file_path": "hypertension.txt",
        "doc_id": "hypertension_001"
      },
      {
        "content": "冠心病是冠状动脉粥样硬化性心脏病的简称...",
        "file_path": "coronary_heart_disease.txt",
        "doc_id": "chd_001"
      }
    ]
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "documents": [
        {
            "content": "高血压是一种常见的心血管疾病...",
            "file_path": "hypertension.txt",
            "doc_id": "hypertension_001"
        },
        {
            "content": "冠心病是冠状动脉粥样硬化性心脏病的简称...",
            "file_path": "coronary_heart_disease.txt",
            "doc_id": "chd_001"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/documents/batch_insert",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  documents: [
    {
      content: "高血压是一种常见的心血管疾病...",
      file_path: "hypertension.txt",
      doc_id: "hypertension_001"
    },
    {
      content: "冠心病是冠状动脉粥样硬化性心脏病的简称...",
      file_path: "coronary_heart_disease.txt",
      doc_id: "chd_001"
    }
  ]
};

fetch('http://localhost:8000/api/documents/batch_insert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 2.4 获取文档状态统计

获取指定 RAG 实例的文档处理状态统计。

**接口地址**

```
GET /api/documents/status/{rag_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |

**响应示例**

```json
{
  "total": 15,
  "processed": 12,
  "pending": 2,
  "failed": 1,
  "status_counts": {
    "PROCESSED": 12,
    "PENDING": 2,
    "FAILED": 1
  }
}
```

**调用示例 (curl)**

```bash
curl -X GET "http://localhost:8000/api/documents/status/medical_knowledge"
```

**调用示例 (Python)**

```python
import requests

rag_id = "medical_knowledge"
response = requests.get(f"http://localhost:8000/api/documents/status/{rag_id}")
status = response.json()
print(f"总文档数: {status['total']}, 已处理: {status['processed']}, 待处理: {status['pending']}, 失败: {status['failed']}")
```

**调用示例 (JavaScript)**

```javascript
const ragId = "medical_knowledge";
fetch(`http://localhost:8000/api/documents/status/${ragId}`)
  .then(response => response.json())
  .then(status => {
    console.log(`总文档数: ${status.total}, 已处理: ${status.processed}`);
  });
```

---

### 2.5 获取指定状态的文档列表

获取指定状态的文档详细列表。

**接口地址**

```
GET /api/documents/list/{rag_id}/{status}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| status | string | 是 | 文档状态 (PROCESSED/PENDING/FAILED) |

**响应示例**

```json
{
  "status": "PROCESSED",
  "count": 12,
  "documents": [
    {
      "doc_id": "diabetes_001",
      "file_name": "diabetes_overview.txt",
      "created_at": "2025-01-15T10:30:00.123456",
      "updated_at": "2025-01-15T10:31:00.123456",
      "error_message": null,
      "status": "PROCESSED"
    },
    {
      "doc_id": "hypertension_001",
      "file_name": "hypertension.txt",
      "created_at": "2025-01-15T10:32:00.123456",
      "updated_at": "2025-01-15T10:33:00.123456",
      "error_message": null,
      "status": "PROCESSED"
    }
  ]
}
```

**调用示例 (curl)**

```bash
# 获取已处理的文档
curl -X GET "http://localhost:8000/api/documents/list/medical_knowledge/PROCESSED"

# 获取待处理的文档
curl -X GET "http://localhost:8000/api/documents/list/medical_knowledge/PENDING"

# 获取失败的文档
curl -X GET "http://localhost:8000/api/documents/list/medical_knowledge/FAILED"
```

**调用示例 (Python)**

```python
import requests

rag_id = "medical_knowledge"
status = "PROCESSED"  # 可以是 PROCESSED, PENDING, FAILED

response = requests.get(f"http://localhost:8000/api/documents/list/{rag_id}/{status}")
result = response.json()

print(f"状态为 {result['status']} 的文档数量: {result['count']}")
for doc in result['documents']:
    print(f"文档 ID: {doc['doc_id']}, 文件名: {doc['file_name']}")
```

**调用示例 (JavaScript)**

```javascript
const ragId = "medical_knowledge";
const status = "PROCESSED";

fetch(`http://localhost:8000/api/documents/list/${ragId}/${status}`)
  .then(response => response.json())
  .then(result => {
    console.log(`状态为 ${result.status} 的文档数量: ${result.count}`);
    result.documents.forEach(doc => {
      console.log(`文档 ID: ${doc.doc_id}, 文件名: ${doc.file_name}`);
    });
  });
```

---

## 3. 查询接口

### 3.1 查询知识库

查询 RAG 知识库，支持多种查询模式和参数配置。

**接口地址**

```
POST /api/query/
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式 (naive/local/global/hybrid) |
| only_need_context | boolean | 否 | true | 是否只需要上下文 |
| top_k | integer | 否 | 20 | 查询返回的 top k 结果 |
| chunk_top_k | integer | 否 | 10 | 分块查询返回的 top k 结果 |
| max_entity_tokens | integer | 否 | 6000 | 实体的最大 token 数 |
| max_relation_tokens | integer | 否 | 8000 | 关系的最大 token 数 |
| max_total_tokens | integer | 否 | 16300 | 总的最大 token 数 |

**查询模式说明**

- `naive`: 简单查询，只使用向量检索
- `local`: 局部查询，关注实体的邻近关系
- `global`: 全局查询，考虑整个知识图谱
- `hybrid`: 混合查询，结合多种策略（推荐）

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "question": "糖尿病的主要症状有哪些？",
  "mode": "hybrid",
  "only_need_context": true,
  "top_k": 20,
  "chunk_top_k": 10,
  "max_entity_tokens": 6000,
  "max_relation_tokens": 8000,
  "max_total_tokens": 16300
}
```

**响应示例**

```json
{
  "rag_id": "medical_knowledge",
  "question": "糖尿病的主要症状有哪些？",
  "answer": "糖尿病的主要症状包括：\n1. 多饮（口渴）\n2. 多尿（尿频）\n3. 多食（饥饿感增加）\n4. 体重下降\n5. 疲劳乏力\n6. 视力模糊...",
  "mode": "hybrid",
  "timestamp": "2025-01-15T12:00:00.123456"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "question": "糖尿病的主要症状有哪些？",
    "mode": "hybrid",
    "top_k": 20
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "question": "糖尿病的主要症状有哪些？",
    "mode": "hybrid",
    "only_need_context": True,
    "top_k": 20,
    "chunk_top_k": 10
}

response = requests.post(
    "http://localhost:8000/api/query/",
    json=data
)
result = response.json()
print(f"问题: {result['question']}")
print(f"回答: {result['answer']}")
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  question: "糖尿病的主要症状有哪些？",
  mode: "hybrid",
  top_k: 20
};

fetch('http://localhost:8000/api/query/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(result => {
    console.log(`问题: ${result.question}`);
    console.log(`回答: ${result.answer}`);
  });
```

---

### 3.2 UCD 建模查询

执行查询并进行 UCD (Use Case Diagram) 建模。

**接口地址**

```
POST /api/query/ucd
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式 |
| out_json | string | 否 | output_uc.json | 输出 JSON 文件路径 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "question": "医院挂号系统的用例有哪些？",
  "mode": "hybrid",
  "out_json": "hospital_registration_uc.json"
}
```

**响应示例**

```json
{
  "status": "success",
  "rag_id": "medical_knowledge",
  "question": "医院挂号系统的用例有哪些？",
  "context": "从知识库检索到的上下文内容...",
  "ucd_model": {
    "actors": ["患者", "医生", "系统管理员"],
    "use_cases": ["注册账号", "预约挂号", "查看病历", "开具处方"]
  },
  "output_file": "hospital_registration_uc.json",
  "mode": "hybrid",
  "timestamp": "2025-01-15T12:00:00.123456"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/query/ucd" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "question": "医院挂号系统的用例有哪些？",
    "mode": "hybrid",
    "out_json": "hospital_uc.json"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "question": "医院挂号系统的用例有哪些？",
    "mode": "hybrid",
    "out_json": "hospital_registration_uc.json"
}

response = requests.post(
    "http://localhost:8000/api/query/ucd",
    json=data
)
result = response.json()
print(f"UCD 模型: {result['ucd_model']}")
print(f"输出文件: {result['output_file']}")
```

---

### 3.3 清除缓存

清除指定 RAG 实例的 LLM 缓存。

**接口地址**

```
POST /api/query/clear_cache
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| cache_type | string | 否 | all | 缓存类型 (llm_cache/all) |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "cache_type": "llm_cache"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "RAG 实例 medical_knowledge 的 LLM 缓存已清除",
  "rag_id": "medical_knowledge",
  "cache_type": "llm_cache"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/query/clear_cache" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "cache_type": "llm_cache"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "cache_type": "llm_cache"  # 或 "all"
}

response = requests.post(
    "http://localhost:8000/api/query/clear_cache",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  cache_type: "llm_cache"
};

fetch('http://localhost:8000/api/query/clear_cache', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 4. 图操作接口 - 实体管理

### 4.1 创建实体

在知识图谱中创建一个新实体。

**接口地址**

```
POST /api/graph/entities/create
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| entity_name | string | 是 | - | 实体名称 |
| description | string | 否 | null | 实体描述 |
| entity_type | string | 否 | UNKNOWN | 实体类型 |
| source_id | string | 否 | manual_creation | 来源 ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "entity_name": "糖尿病",
  "description": "一种代谢性疾病，其特征是血糖水平持续升高",
  "entity_type": "DISEASE",
  "source_id": "manual_creation",
  "file_path": "manual_creation"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "实体 '糖尿病' 创建成功",
  "entity": {
    "entity_name": "糖尿病",
    "description": "一种代谢性疾病，其特征是血糖水平持续升高",
    "entity_type": "DISEASE"
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/entities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "description": "一种代谢性疾病",
    "entity_type": "DISEASE"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "description": "一种代谢性疾病，其特征是血糖水平持续升高",
    "entity_type": "DISEASE"
}

response = requests.post(
    "http://localhost:8000/api/graph/entities/create",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  entity_name: "糖尿病",
  description: "一种代谢性疾病，其特征是血糖水平持续升高",
  entity_type: "DISEASE"
};

fetch('http://localhost:8000/api/graph/entities/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 4.2 编辑实体

编辑已存在的实体信息。

**接口地址**

```
POST /api/graph/entities/edit
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| entity_name | string | 是 | - | 实体名称 |
| updated_data | object | 是 | - | 要更新的数据 |
| allow_rename | boolean | 否 | true | 是否允许重命名 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "entity_name": "糖尿病",
  "updated_data": {
    "description": "一种以高血糖为特征的代谢性疾病，由于胰岛素分泌缺陷或作用障碍引起",
    "entity_type": "CHRONIC_DISEASE"
  },
  "allow_rename": false
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "实体 '糖尿病' 更新成功",
  "entity": {
    "entity_name": "糖尿病",
    "description": "一种以高血糖为特征的代谢性疾病，由于胰岛素分泌缺陷或作用障碍引起",
    "entity_type": "CHRONIC_DISEASE"
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/entities/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "updated_data": {
      "description": "更新后的描述",
      "entity_type": "CHRONIC_DISEASE"
    },
    "allow_rename": false
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "updated_data": {
        "description": "一种以高血糖为特征的代谢性疾病",
        "entity_type": "CHRONIC_DISEASE"
    },
    "allow_rename": False
}

response = requests.post(
    "http://localhost:8000/api/graph/entities/edit",
    json=data
)
print(response.json())
```

---

### 4.3 删除实体

删除指定的实体及其关联关系。

**接口地址**

```
POST /api/graph/entities/delete
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| entity_name | string | 是 | 要删除的实体名称 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "entity_name": "糖尿病"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "实体 '糖尿病' 及其关联关系已删除",
  "entity_name": "糖尿病",
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/entities/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病"
}

response = requests.post(
    "http://localhost:8000/api/graph/entities/delete",
    json=data
)
print(response.json())
```

---

### 4.4 获取实体信息

获取指定实体的详细信息。

**接口地址**

```
POST /api/graph/entities/info
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| entity_name | string | 是 | - | 实体名称 |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "entity_name": "糖尿病",
  "include_vector_data": false
}
```

**响应示例**

```json
{
  "status": "success",
  "entity_info": {
    "entity_name": "糖尿病",
    "description": "一种代谢性疾病",
    "entity_type": "DISEASE",
    "source_id": "manual_creation",
    "file_path": "manual_creation",
    "related_entities": ["胰岛素", "血糖", "并发症"],
    "created_at": "2025-01-15T10:00:00.123456",
    "updated_at": "2025-01-15T11:00:00.123456"
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/entities/info" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "include_vector_data": false
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "entity_name": "糖尿病",
    "include_vector_data": False
}

response = requests.post(
    "http://localhost:8000/api/graph/entities/info",
    json=data
)
entity_info = response.json()
print(f"实体信息: {entity_info['entity_info']}")
```

---

### 4.5 合并实体

将多个实体合并为一个目标实体。

**接口地址**

```
POST /api/graph/entities/merge
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| source_entities | array | 是 | - | 要合并的源实体列表 |
| target_entity | string | 是 | - | 目标实体名称 |
| merge_strategy | object | 否 | null | 合并策略 |
| target_entity_data | object | 否 | null | 目标实体数据 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "source_entities": ["DM", "Diabetes", "糖尿症"],
  "target_entity": "糖尿病",
  "merge_strategy": {
    "description": "concat",
    "entity_type": "prefer_target"
  },
  "target_entity_data": {
    "description": "一种代谢性疾病",
    "entity_type": "DISEASE"
  }
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "成功合并 3 个实体到 '糖尿病'",
  "merged_entity": {
    "entity_name": "糖尿病",
    "description": "一种代谢性疾病",
    "entity_type": "DISEASE",
    "merged_from": ["DM", "Diabetes", "糖尿症"]
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/entities/merge" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "source_entities": ["DM", "Diabetes"],
    "target_entity": "糖尿病"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "source_entities": ["DM", "Diabetes", "糖尿症"],
    "target_entity": "糖尿病",
    "target_entity_data": {
        "description": "一种代谢性疾病",
        "entity_type": "DISEASE"
    }
}

response = requests.post(
    "http://localhost:8000/api/graph/entities/merge",
    json=data
)
print(response.json())
```

---

## 5. 图操作接口 - 关系管理

### 5.1 创建关系

在两个实体之间创建关系。

**接口地址**

```
POST /api/graph/relations/create
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| source_entity | string | 是 | - | 源实体名称 |
| target_entity | string | 是 | - | 目标实体名称 |
| description | string | 否 | null | 关系描述 |
| keywords | string | 否 | null | 关键词 |
| weight | float | 否 | 1.0 | 关系权重 |
| source_id | string | 否 | manual_creation | 来源 ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "source_entity": "糖尿病",
  "target_entity": "胰岛素",
  "description": "缺乏或抵抗",
  "keywords": "激素,分泌,作用",
  "weight": 0.9,
  "source_id": "manual_creation",
  "file_path": "manual_creation"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "关系 '糖尿病' -> '胰岛素' 创建成功",
  "relation": {
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "description": "缺乏或抵抗",
    "keywords": "激素,分泌,作用",
    "weight": 0.9
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/relations/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "description": "缺乏或抵抗",
    "weight": 0.9
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "description": "缺乏或抵抗",
    "keywords": "激素,分泌,作用",
    "weight": 0.9
}

response = requests.post(
    "http://localhost:8000/api/graph/relations/create",
    json=data
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
const data = {
  rag_id: "medical_knowledge",
  source_entity: "糖尿病",
  target_entity: "胰岛素",
  description: "缺乏或抵抗",
  keywords: "激素,分泌,作用",
  weight: 0.9
};

fetch('http://localhost:8000/api/graph/relations/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 5.2 编辑关系

编辑已存在的关系。

**接口地址**

```
POST /api/graph/relations/edit
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |
| updated_data | object | 是 | 要更新的数据 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "source_entity": "糖尿病",
  "target_entity": "胰岛素",
  "updated_data": {
    "description": "胰岛素分泌不足或作用障碍",
    "weight": 0.95,
    "keywords": "激素,胰岛,血糖调节"
  }
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "关系 '糖尿病' -> '胰岛素' 更新成功",
  "relation": {
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "description": "胰岛素分泌不足或作用障碍",
    "weight": 0.95
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/relations/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "updated_data": {
      "description": "胰岛素分泌不足或作用障碍",
      "weight": 0.95
    }
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "updated_data": {
        "description": "胰岛素分泌不足或作用障碍",
        "weight": 0.95
    }
}

response = requests.post(
    "http://localhost:8000/api/graph/relations/edit",
    json=data
)
print(response.json())
```

---

### 5.3 删除关系

删除两个实体之间的关系。

**接口地址**

```
POST /api/graph/relations/delete
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例 ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "source_entity": "糖尿病",
  "target_entity": "胰岛素"
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "关系 '糖尿病' -> '胰岛素' 已删除",
  "source_entity": "糖尿病",
  "target_entity": "胰岛素",
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/relations/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素"
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素"
}

response = requests.post(
    "http://localhost:8000/api/graph/relations/delete",
    json=data
)
print(response.json())
```

---

### 5.4 获取关系信息

获取两个实体之间关系的详细信息。

**接口地址**

```
POST /api/graph/relations/info
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| source_entity | string | 是 | - | 源实体名称 |
| target_entity | string | 是 | - | 目标实体名称 |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "source_entity": "糖尿病",
  "target_entity": "胰岛素",
  "include_vector_data": false
}
```

**响应示例**

```json
{
  "status": "success",
  "relation_info": {
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "description": "缺乏或抵抗",
    "keywords": "激素,分泌,作用",
    "weight": 0.9,
    "source_id": "manual_creation",
    "file_path": "manual_creation",
    "created_at": "2025-01-15T10:00:00.123456",
    "updated_at": "2025-01-15T11:00:00.123456"
  },
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
curl -X POST "http://localhost:8000/api/graph/relations/info" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "include_vector_data": false
  }'
```

**调用示例 (Python)**

```python
import requests

data = {
    "rag_id": "medical_knowledge",
    "source_entity": "糖尿病",
    "target_entity": "胰岛素",
    "include_vector_data": False
}

response = requests.post(
    "http://localhost:8000/api/graph/relations/info",
    json=data
)
relation_info = response.json()
print(f"关系信息: {relation_info['relation_info']}")
```

---

## 6. 数据导出接口

### 6.1 导出知识图谱数据

导出知识图谱数据到文件。

**接口地址**

```
POST /api/graph/export
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例 ID |
| output_path | string | 是 | - | 输出文件路径 |
| file_format | string | 否 | csv | 文件格式 (csv/excel/md/txt) |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**

```json
{
  "rag_id": "medical_knowledge",
  "output_path": "./exports/medical_kg.csv",
  "file_format": "csv",
  "include_vector_data": false
}
```

**响应示例**

```json
{
  "status": "success",
  "message": "数据已成功导出到 ./exports/medical_kg.csv",
  "output_path": "./exports/medical_kg.csv",
  "format": "csv",
  "rag_id": "medical_knowledge"
}
```

**调用示例 (curl)**

```bash
# 导出为 CSV
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "output_path": "./exports/medical_kg.csv",
    "file_format": "csv"
  }'

# 导出为 Excel
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "output_path": "./exports/medical_kg.xlsx",
    "file_format": "excel"
  }'

# 导出为 Markdown
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "medical_knowledge",
    "output_path": "./exports/medical_kg.md",
    "file_format": "md"
  }'
```

**调用示例 (Python)**

```python
import requests

# 导出为 CSV
data = {
    "rag_id": "medical_knowledge",
    "output_path": "./exports/medical_kg.csv",
    "file_format": "csv",
    "include_vector_data": False
}

response = requests.post(
    "http://localhost:8000/api/graph/export",
    json=data
)
print(response.json())

# 导出为 Excel
data_excel = {
    "rag_id": "medical_knowledge",
    "output_path": "./exports/medical_kg.xlsx",
    "file_format": "excel"
}

response = requests.post(
    "http://localhost:8000/api/graph/export",
    json=data_excel
)
print(response.json())
```

**调用示例 (JavaScript)**

```javascript
// 导出为 CSV
const data = {
  rag_id: "medical_knowledge",
  output_path: "./exports/medical_kg.csv",
  file_format: "csv",
  include_vector_data: false
};

fetch('http://localhost:8000/api/graph/export', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 7. WebSocket 接口

WebSocket 提供实时双向通信,适合需要实时交互的场景。

**连接地址**

```
ws://localhost:8000/ws
```

### 7.1 实时查询

**发送消息格式**

```json
{
  "type": "query",
  "rag_id": "medical_knowledge",
  "question": "糖尿病的主要症状有哪些？",
  "mode": "hybrid"
}
```

**接收消息格式**

状态消息:
```json
{
  "type": "status",
  "message": "正在查询..."
}
```

结果消息:
```json
{
  "type": "answer",
  "rag_id": "medical_knowledge",
  "question": "糖尿病的主要症状有哪些？",
  "context": "糖尿病的主要症状包括多饮、多尿、多食、体重下降...",
  "mode": "hybrid"
}
```

错误消息:
```json
{
  "type": "error",
  "message": "错误信息"
}
```

**调用示例 (Python)**

```python
import asyncio
import websockets
import json

async def query_via_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 发送查询
        query_message = {
            "type": "query",
            "rag_id": "medical_knowledge",
            "question": "糖尿病的主要症状有哪些？",
            "mode": "hybrid"
        }
        await websocket.send(json.dumps(query_message))

        # 接收响应
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"收到消息: {data}")

            if data["type"] == "answer":
                print(f"回答: {data['context']}")
                break
            elif data["type"] == "error":
                print(f"错误: {data['message']}")
                break

asyncio.run(query_via_websocket())
```

**调用示例 (JavaScript)**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
  console.log('WebSocket 连接已建立');

  // 发送查询
  const queryMessage = {
    type: "query",
    rag_id: "medical_knowledge",
    question: "糖尿病的主要症状有哪些？",
    mode: "hybrid"
  };
  ws.send(JSON.stringify(queryMessage));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);

  if (data.type === "status") {
    console.log('状态:', data.message);
  } else if (data.type === "answer") {
    console.log('问题:', data.question);
    console.log('回答:', data.context);
  } else if (data.type === "error") {
    console.error('错误:', data.message);
  }
};

ws.onerror = function(error) {
  console.error('WebSocket 错误:', error);
};

ws.onclose = function() {
  console.log('WebSocket 连接已关闭');
};
```

---

### 7.2 实体操作

**创建实体消息格式**

```json
{
  "type": "entity_operation",
  "rag_id": "medical_knowledge",
  "operation": "create",
  "entity_name": "高血压",
  "entity_data": {
    "description": "血压持续升高的疾病",
    "entity_type": "DISEASE"
  }
}
```

**删除实体消息格式**

```json
{
  "type": "entity_operation",
  "rag_id": "medical_knowledge",
  "operation": "delete",
  "entity_name": "高血压"
}
```

**接收消息格式**

创建成功:
```json
{
  "type": "entity_created",
  "rag_id": "medical_knowledge",
  "result": {
    "entity_name": "高血压",
    "description": "血压持续升高的疾病",
    "entity_type": "DISEASE"
  }
}
```

删除成功:
```json
{
  "type": "entity_deleted",
  "rag_id": "medical_knowledge",
  "result": {
    "status": "success",
    "message": "实体已删除"
  }
}
```

**调用示例 (Python)**

```python
import asyncio
import websockets
import json

async def create_entity_via_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 创建实体
        message = {
            "type": "entity_operation",
            "rag_id": "medical_knowledge",
            "operation": "create",
            "entity_name": "高血压",
            "entity_data": {
                "description": "血压持续升高的疾病",
                "entity_type": "DISEASE"
            }
        }
        await websocket.send(json.dumps(message))

        # 接收响应
        response = await websocket.recv()
        data = json.loads(response)
        print(f"实体创建结果: {data}")

asyncio.run(create_entity_via_websocket())
```

**调用示例 (JavaScript)**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
  // 创建实体
  const message = {
    type: "entity_operation",
    rag_id: "medical_knowledge",
    operation: "create",
    entity_name: "高血压",
    entity_data: {
      description: "血压持续升高的疾病",
      entity_type: "DISEASE"
    }
  };
  ws.send(JSON.stringify(message));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === "entity_created") {
    console.log('实体创建成功:', data.result);
  } else if (data.type === "entity_deleted") {
    console.log('实体删除成功:', data.result);
  }
};
```

---

### 7.3 UCD 建模

**发送消息格式**

```json
{
  "type": "query_ucd",
  "rag_id": "medical_knowledge",
  "question": "医院挂号系统的用例有哪些？",
  "mode": "hybrid",
  "out_json": "hospital_registration_uc.json"
}
```

**接收消息格式**

状态消息:
```json
{
  "type": "status",
  "message": "正在检索知识..."
}
```

```json
{
  "type": "status",
  "message": "正在进行 UCD 建模..."
}
```

结果消息:
```json
{
  "type": "ucd_result",
  "rag_id": "medical_knowledge",
  "question": "医院挂号系统的用例有哪些？",
  "context": "检索到的上下文...",
  "ucd_model": {
    "actors": ["患者", "医生", "系统管理员"],
    "use_cases": ["注册账号", "预约挂号", "查看病历"]
  },
  "output_file": "hospital_registration_uc.json"
}
```

**调用示例 (Python)**

```python
import asyncio
import websockets
import json

async def ucd_modeling_via_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 发送 UCD 建模请求
        message = {
            "type": "query_ucd",
            "rag_id": "medical_knowledge",
            "question": "医院挂号系统的用例有哪些？",
            "mode": "hybrid",
            "out_json": "hospital_uc.json"
        }
        await websocket.send(json.dumps(message))

        # 接收响应
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"收到消息: {data}")

            if data["type"] == "ucd_result":
                print(f"UCD 模型: {data['ucd_model']}")
                print(f"输出文件: {data['output_file']}")
                break
            elif data["type"] == "error":
                print(f"错误: {data['message']}")
                break

asyncio.run(ucd_modeling_via_websocket())
```

**调用示例 (JavaScript)**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
  const message = {
    type: "query_ucd",
    rag_id: "medical_knowledge",
    question: "医院挂号系统的用例有哪些？",
    mode: "hybrid",
    out_json: "hospital_uc.json"
  };
  ws.send(JSON.stringify(message));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);

  if (data.type === "status") {
    console.log('状态:', data.message);
  } else if (data.type === "ucd_result") {
    console.log('UCD 模型:', data.ucd_model);
    console.log('输出文件:', data.output_file);
  } else if (data.type === "error") {
    console.error('错误:', data.message);
  }
};
```

---

## 附录

### 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 (如 RAG 实例不存在) |
| 500 | 服务器内部错误 |

### 常见错误示例

**RAG 实例不存在**
```json
{
  "detail": "RAG 实例 'unknown_rag' 不存在"
}
```

**RAG 系统未初始化**
```json
{
  "detail": "RAG 系统未初始化"
}
```

**必填参数缺失**
```json
{
  "detail": "必须提供 file_path 参数（文件路径或文件名称）"
}
```

### 最佳实践

1. **创建 RAG 实例**: 在使用其他接口之前，先创建 RAG 实例
2. **使用合适的查询模式**:
   - `hybrid` 模式适合大多数场景
   - `local` 模式适合查询实体附近的信息
   - `global` 模式适合需要全局视角的查询
3. **批量操作**: 使用批量插入接口可以提高性能
4. **定期清除缓存**: 在更新了大量数据后，建议清除缓存
5. **合理设置参数**: 根据实际需求调整 `top_k`、`chunk_token_size` 等参数

### 性能优化建议

1. **启用缓存**: 设置 `enable_llm_cache=true` 可以加速重复查询
2. **调整分块大小**: 根据文档特点调整 `chunk_token_size`
3. **使用合适的阈值**: 调整 `cosine_threshold` 可以平衡召回率和准确率
4. **批量操作**: 使用批量插入减少网络开销

---

**文档版本**: v3.0.0
**最后更新**: 2025-01-15
**联系方式**: 如有问题请提交 Issue
