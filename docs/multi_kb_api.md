# 多知识库查询接口完整文档

本文档介绍所有支持多知识库查询的接口，包括 RAG 查询接口和图谱查询接口。

## 目录

### 一、RAG 查询接口
- [1. 标准查询 (/api/query/)](#1-标准查询-apiquery)
- [2. 关键字检索 (/api/query/keywords)](#2-关键字检索-apiquerykeywords)
- [3. UCD 建模查询 (/api/query/ucd)](#3-ucd-建模查询-apiqueryucd)
- [4. 清理图谱检索 (/api/query/graph-clean)](#4-清理图谱检索-apiquerygraph-clean)
- [5. 仅 Chunks 检索 (/api/query/chunks-only)](#5-仅-chunks-检索-apiquerychunks-only)

### 二、图谱查询接口
- [6. 完整图谱查询 (/api/graph/echarts)](#6-完整图谱查询-apigraphecharts)
- [7. Top-K 节点查询 (/api/graph/echarts/top-k)](#7-top-k-节点查询-apigraphechartstop-k)
- [8. 邻居节点查询 (/api/graph/echarts/neighbors)](#8-邻居节点查询-apigraphechartsneighbors)
- [9. POST 方式查询 (/api/graph/echarts/multi)](#9-post-方式查询-apigraphechartsmulti)

### 三、附录
- [10. 通用说明](#10-通用说明)
- [11. 错误响应](#11-错误响应)
- [12. 完整示例代码](#12-完整示例代码)

---

# 一、RAG 查询接口

## 1. 标准查询 (/api/query/)

执行标准的 RAG 查询，支持单个或多个知识库。

### 接口信息

- **URL**: `/api/query/`
- **方法**: `POST`
- **说明**: 支持 naive/local/global/hybrid 四种查询模式

### 请求参数

**Content-Type**: `application/json`

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 否* | - | 单知识库模式（向后兼容） |
| rag_ids | string[] | 否* | - | 多知识库模式 |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | "hybrid" | 查询模式：naive/local/global/hybrid |
| only_need_context | boolean | 否 | true | 是否只返回上下文 |
| top_k | integer | 否 | null | 检索的实体/关系数量 |
| chunk_top_k | integer | 否 | null | 检索的文本块数量 |
| max_entity_tokens | integer | 否 | null | 实体最大 token 数 |
| max_relation_tokens | integer | 否 | null | 关系最大 token 数 |
| max_total_tokens | integer | 否 | null | 总最大 token 数 |
| stream | boolean | 否 | null | 是否启用流式输出 |
| enable_rerank | boolean | 否 | null | 是否启用 Rerank |
| response_type | string | 否 | null | 响应格式 |
| conversation_history | object[] | 否 | null | 对话历史 |
| hl_keywords | string[] | 否 | null | 高优先级关键词 |
| ll_keywords | string[] | 否 | null | 低优先级关键词 |
| user_prompt | string | 否 | null | 用户自定义提示词 |
| include_references | boolean | 否 | null | 是否包含引用列表 |

\* 注意：`rag_id` 和 `rag_ids` 必须提供其中一个

### 调用示例

#### 单知识库查询（向后兼容）

```bash
# cURL 示例
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "kb1",
    "question": "什么是RAG？",
    "mode": "hybrid"
  }'

# Python 示例
import requests

response = requests.post(
    "http://localhost:8000/api/query/",
    json={
        "rag_id": "kb1",
        "question": "什么是RAG？",
        "mode": "hybrid"
    }
)
print(response.json())
```

#### 多知识库查询

```bash
# cURL 示例
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["kb1", "kb2", "kb3"],
    "question": "什么是RAG？",
    "mode": "hybrid",
    "only_need_context": true
  }'

# Python 示例
import requests

response = requests.post(
    "http://localhost:8000/api/query/",
    json={
        "rag_ids": ["kb1", "kb2", "kb3"],
        "question": "什么是RAG？",
        "mode": "hybrid",
        "only_need_context": true,
        "top_k": 10,
        "chunk_top_k": 5
    }
)
print(response.json())

# JavaScript/Axios 示例
const response = await axios.post('/api/query/', {
    rag_ids: ['kb1', 'kb2', 'kb3'],
    question: '什么是RAG？',
    mode: 'hybrid',
    only_need_context: true
});
console.log(response.data);
```

### 返回格式

```json
{
  "rag_ids": ["kb1", "kb2", "kb3"],
  "question": "什么是RAG？",
  "answer": "【知识库: kb1】\nRAG是检索增强生成...\n\n【知识库: kb2】\nRAG技术结合了...\n\n【知识库: kb3】\n在实际应用中...",
  "mode": "hybrid",
  "timestamp": "2026-01-11T10:30:00.123456",
  "sources": [
    {
      "rag_id": "kb1",
      "answer_length": 500
    },
    {
      "rag_id": "kb2",
      "answer_length": 320
    },
    {
      "rag_id": "kb3",
      "answer_length": 450
    }
  ]
}
```

### 说明

- **单知识库模式**: 使用 `rag_id` 参数，返回单个知识库的查询结果
- **多知识库模式**: 使用 `rag_ids` 参数，并发查询所有知识库并合并结果
- 多知识库查询会在答案中标注每部分来源于哪个知识库
- `sources` 字段记录每个知识库的贡献详情

---

## 2. 关键字检索 (/api/query/keywords)

使用关键字列表进行检索，支持单个或多个知识库。

### 接口信息

- **URL**: `/api/query/keywords`
- **方法**: `POST`
- **说明**: 基于关键字的精确检索，适合已知实体名称的场景

### 请求参数

**Content-Type**: `application/json`

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 否* | - | 单知识库模式 |
| rag_ids | string[] | 否* | - | 多知识库模式 |
| keywords | string[] | 否 | null | 关键字列表 |
| mode | string | 否 | "hybrid" | 检索模式 |
| only_need_context | boolean | 否 | true | 只返回上下文 |
| top_k | integer | 否 | null | 检索数量 |
| chunk_top_k | integer | 否 | null | 文本块数量 |
| max_entity_tokens | integer | 否 | null | 实体最大 token |
| max_relation_tokens | integer | 否 | null | 关系最大 token |
| max_total_tokens | integer | 否 | null | 总最大 token |
| enable_rerank | boolean | 否 | null | 是否启用 Rerank |

\* 注意：`rag_id` 和 `rag_ids` 必须提供其中一个

### 调用示例

#### 单知识库检索

```bash
curl -X POST "http://localhost:8000/api/query/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "kb1",
    "keywords": ["人工智能", "机器学习", "深度学习"],
    "mode": "hybrid"
  }'
```

#### 多知识库检索

```bash
curl -X POST "http://localhost:8000/api/query/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["kb1", "kb2"],
    "keywords": ["人工智能", "机器学习"],
    "mode": "hybrid",
    "top_k": 10
  }'
```

### 返回格式

```json
{
  "rag_ids": ["kb1", "kb2"],
  "keywords": ["人工智能", "机器学习"],
  "context": "【知识库: kb1】\n检索到的上下文内容...\n\n【知识库: kb2】\n检索到的上下文内容...",
  "mode": "hybrid",
  "timestamp": "2026-01-11T10:30:00.123456",
  "sources": [
    {
      "rag_id": "kb1",
      "context_length": 1200
    },
    {
      "rag_id": "kb2",
      "context_length": 800
    }
  ]
}
```

---

## 3. UCD 建模查询 (/api/query/ucd)

执行查询并进行 UCD（用例图）建模，支持多知识库。

### 接口信息

- **URL**: `/api/query/ucd`
- **方法**: `POST`
- **说明**: 先进行 RAG 检索，然后基于检索结果生成 UCD 模型

### 请求参数

**Content-Type**: `application/json`

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 否* | - | 单知识库模式 |
| rag_ids | string[] | 否* | - | 多知识库模式 |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | "hybrid" | 查询模式 |
| out_json | string | 否 | "output_uc.json" | 输出文件路径 |

\* 注意：`rag_id` 和 `rag_ids` 必须提供其中一个

### 调用示例

#### 单知识库 UCD 建模

```bash
curl -X POST "http://localhost:8000/api/query/ucd" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "kb1",
    "question": "用户登录流程",
    "mode": "hybrid",
    "out_json": "login_ucd.json"
  }'
```

#### 多知识库 UCD 建模

```bash
curl -X POST "http://localhost:8000/api/query/ucd" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["kb1", "kb2", "kb3"],
    "question": "用户登录和注册流程",
    "mode": "hybrid"
  }'
```

### 返回格式

```json
{
  "status": "success",
  "rag_ids": ["kb1", "kb2"],
  "question": "用户登录流程",
  "context": "【知识库: kb1】\n上下文...\n\n【知识库: kb2】\n上下文...",
  "ucd_model": {
    "actors": ["用户", "系统"],
    "use_cases": ["登录", "验证"],
    "relationships": []
  },
  "output_file": "output_uc.json",
  "mode": "hybrid",
  "timestamp": "2026-01-11T10:30:00.123456",
  "sources": [
    {
      "rag_id": "kb1",
      "context_length": 500
    },
    {
      "rag_id": "kb2",
      "context_length": 300
    }
  ]
}
```

---

## 4. 清理图谱检索 (/api/query/graph-clean)

使用关键字检索知识图谱，返回清理后的实体和关系（去除元数据）。

### 接口信息

- **URL**: `/api/query/graph-clean`
- **方法**: `POST`
- **说明**: 返回的数据只保留实体和关系的核心字段

### 请求参数

**Content-Type**: `application/json`

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 否* | - | 单知识库模式 |
| rag_ids | string[] | 否* | - | 多知识库模式 |
| keywords | string[] | 否 | null | 关键字列表 |
| top_k | integer | 否 | null | 检索数量 |
| chunk_top_k | integer | 否 | null | 文本块数量 |
| max_entity_tokens | integer | 否 | null | 实体最大 token |
| max_relation_tokens | integer | 否 | null | 关系最大 token |
| max_total_tokens | integer | 否 | null | 总最大 token |
| enable_rerank | boolean | 否 | null | 是否启用 Rerank |

\* 注意：`rag_id` 和 `rag_ids` 必须提供其中一个

### 调用示例

#### 单知识库图谱检索

```bash
curl -X POST "http://localhost:8000/api/query/graph-clean" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "kb1",
    "keywords": ["人工智能", "机器学习"],
    "top_k": 10
  }'
```

#### 多知识库图谱检索

```bash
curl -X POST "http://localhost:8000/api/query/graph-clean" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["kb1", "kb2", "kb3"],
    "keywords": ["人工智能"],
    "top_k": 20,
    "enable_rerank": true
  }'
```

### 返回格式

```json
{
  "rag_ids": ["kb1", "kb2"],
  "keywords": ["人工智能"],
  "entities": [
    {
      "entity_name": "人工智能",
      "description": "计算机科学的一个重要分支",
      "entity_type": "CONCEPT"
    },
    {
      "entity_name": "机器学习",
      "description": "实现人工智能的核心技术",
      "entity_type": "CONCEPT"
    }
  ],
  "relationships": [
    {
      "src_id": "人工智能",
      "tgt_id": "机器学习",
      "description": "包含",
      "keywords": "技术领域"
    }
  ],
  "timestamp": "2026-01-11T10:30:00.123456",
  "sources": [
    {
      "rag_id": "kb1",
      "entities_count": 5,
      "relationships_count": 4
    },
    {
      "rag_id": "kb2",
      "entities_count": 3,
      "relationships_count": 2
    }
  ]
}
```

### 说明

- 实体只保留：`entity_name`、`description`、`entity_type`
- 关系只保留：`src_id`、`tgt_id`、`description`、`keywords`
- 多知识库查询会合并所有实体和关系

---

## 5. 仅 Chunks 检索 (/api/query/chunks-only)

使用关键字检索，只返回文档 chunks，不包含图谱数据。

### 接口信息

- **URL**: `/api/query/chunks-only`
- **方法**: `POST`
- **说明**: 适合只需要文本块数据的场景

### 请求参数

**Content-Type**: `application/json`

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 否* | - | 单知识库模式 |
| rag_ids | string[] | 否* | - | 多知识库模式 |
| keywords | string[] | 否 | null | 关键字列表 |
| chunk_top_k | integer | 否 | null | 文本块数量 |
| max_total_tokens | integer | 否 | null | 总最大 token |
| enable_rerank | boolean | 否 | null | 是否启用 Rerank |

\* 注意：`rag_id` 和 `rag_ids` 必须提供其中一个

### 调用示例

#### 单知识库 Chunks 检索

```bash
curl -X POST "http://localhost:8000/api/query/chunks-only" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "kb1",
    "keywords": ["RAG技术"],
    "chunk_top_k": 5
  }'
```

#### 多知识库 Chunks 检索

```bash
curl -X POST "http://localhost:8000/api/query/chunks-only" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_ids": ["kb1", "kb2", "kb3"],
    "keywords": ["RAG", "向量数据库"],
    "chunk_top_k": 10,
    "enable_rerank": true
  }'
```

### 返回格式

```json
{
  "rag_ids": ["kb1", "kb2"],
  "keywords": ["RAG技术"],
  "chunks": [
    {
      "content": "RAG（检索增强生成）是一种结合检索和生成的技术...",
      "file_path": "docs/rag_intro.txt",
      "chunk_id": "chunk_001",
      "reference_id": "ref_001"
    },
    {
      "content": "向量数据库在 RAG 系统中扮演着关键角色...",
      "file_path": "docs/vector_db.txt",
      "chunk_id": "chunk_002",
      "reference_id": "ref_002"
    }
  ],
  "timestamp": "2026-01-11T10:30:00.123456",
  "sources": [
    {
      "rag_id": "kb1",
      "chunks_count": 7
    },
    {
      "rag_id": "kb2",
      "chunks_count": 3
    }
  ]
}
```

---

# 二、图谱查询接口

## 6. 完整图谱查询 (/api/graph/echarts)

获取一个或多个知识库的完整知识图谱数据（ECharts 格式）。

### 接口信息

- **URL**: `/api/graph/echarts`
- **方法**: `GET`
- **说明**: 查询知识库的全部实体和关系

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_ids | string[] | 是 | 知识库 ID 列表 |

### 调用示例

参考《多知识库图谱查询接口文档》中的详细说明。

---

## 7. Top-K 节点查询 (/api/graph/echarts/top-k)

获取度数最高的 Top-K 个节点构成的子图。

### 接口信息

- **URL**: `/api/graph/echarts/top-k`
- **方法**: `GET`
- **说明**: 每个知识库分别取 Top-K 节点

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_ids | string[] | 是 | - | 知识库 ID 列表 |
| k | integer | 否 | 10 | 返回节点数量 |

---

## 8. 邻居节点查询 (/api/graph/echarts/neighbors)

获取指定节点的邻居子图。

### 接口信息

- **URL**: `/api/graph/echarts/neighbors`
- **方法**: `GET`
- **说明**: 查询指定节点的直接邻居（一跳关系）

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| node_id | string | 是 | 中心节点 ID |
| rag_ids | string[] | 是 | 知识库 ID 列表 |

---

## 9. POST 方式查询 (/api/graph/echarts/multi)

使用 POST 请求查询多个知识库的完整图谱。

### 接口信息

- **URL**: `/api/graph/echarts/multi`
- **方法**: `POST`
- **说明**: 功能与 GET `/echarts` 相同，使用 POST 请求体

### 请求参数

**Content-Type**: `application/json`

```json
{
  "rag_ids": ["kb1", "kb2", "kb3"]
}
```

---

# 三、附录

## 10. 通用说明

### 10.1 向后兼容性

所有 RAG 查询接口都保持向后兼容：
- **旧版本调用**：使用 `rag_id` 参数（单知识库）
- **新版本调用**：使用 `rag_ids` 参数（多知识库）

### 10.2 并发查询策略

多知识库查询使用 `asyncio.gather` 实现真正的并发：
```python
tasks = [query_single_kb(rag_id) for rag_id in rag_ids]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 10.3 容错机制

- 部分知识库查询失败不影响整体结果
- 自动跳过不存在或未初始化的知识库
- 返回的 `rag_ids` 字段列出实际成功的知识库

### 10.4 结果合并策略

#### RAG 查询接口
- 简单拼接各知识库的答案
- 使用 `【知识库: {rag_id}】` 标注来源

#### 图谱查询接口
- 使用 `(entity_name, rag_id)` 作为节点唯一键
- 同名实体在不同知识库中视为不同节点
- 所有节点和边都带有 `rag_id` 标识

### 10.5 sources 字段

所有多知识库查询接口都包含可选的 `sources` 字段：
```json
{
  "sources": [
    {
      "rag_id": "kb1",
      "answer_length": 500  // 或其他统计信息
    }
  ]
}
```

---

## 11. 错误响应

### 11.1 参数错误 (400)

```json
{
  "detail": "必须提供 rag_id 或 rag_ids"
}
```

### 11.2 知识库不存在 (404)

```json
{
  "detail": "RAG 实例不存在: kb1"
}
```

或

```json
{
  "detail": "所有知识库查询均失败"
}
```

### 11.3 服务器错误 (500)

```json
{
  "detail": "查询失败: <错误详情>"
}
```

---

## 12. 完整示例代码

### 12.1 Python 客户端

```python
import requests
from typing import List, Optional, Dict, Any

class MultiKBQueryClient:
    """多知识库查询客户端"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def query(
        self,
        rag_ids: List[str],
        question: str,
        mode: str = "hybrid",
        **kwargs
    ) -> Dict[str, Any]:
        """标准 RAG 查询"""
        response = requests.post(
            f"{self.base_url}/api/query/",
            json={
                "rag_ids": rag_ids,
                "question": question,
                "mode": mode,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()

    def keywords_search(
        self,
        rag_ids: List[str],
        keywords: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """关键字检索"""
        response = requests.post(
            f"{self.base_url}/api/query/keywords",
            json={
                "rag_ids": rag_ids,
                "keywords": keywords,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()

    def graph_clean(
        self,
        rag_ids: List[str],
        keywords: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """清理图谱检索"""
        response = requests.post(
            f"{self.base_url}/api/query/graph-clean",
            json={
                "rag_ids": rag_ids,
                "keywords": keywords,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()

    def chunks_only(
        self,
        rag_ids: List[str],
        keywords: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """仅 Chunks 检索"""
        response = requests.post(
            f"{self.base_url}/api/query/chunks-only",
            json={
                "rag_ids": rag_ids,
                "keywords": keywords,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()

    def get_full_graph(self, rag_ids: List[str]) -> Dict[str, Any]:
        """获取完整图谱"""
        response = requests.get(
            f"{self.base_url}/api/graph/echarts",
            params={"rag_ids": rag_ids}
        )
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = MultiKBQueryClient()

    # 示例 1: 多知识库标准查询
    result1 = client.query(
        rag_ids=["kb1", "kb2", "kb3"],
        question="什么是RAG技术？",
        mode="hybrid",
        top_k=10
    )
    print(f"查询结果长度: {len(result1['answer'])}")
    print(f"查询的知识库: {result1['rag_ids']}")
    print(f"各库贡献: {result1.get('sources', [])}")

    # 示例 2: 关键字检索
    result2 = client.keywords_search(
        rag_ids=["kb1", "kb2"],
        keywords=["人工智能", "机器学习"],
        top_k=10
    )
    print(f"检索上下文长度: {len(result2['context'])}")

    # 示例 3: 清理图谱检索
    result3 = client.graph_clean(
        rag_ids=["kb1", "kb2"],
        keywords=["人工智能"],
        top_k=20
    )
    print(f"实体数量: {len(result3['entities'])}")
    print(f"关系数量: {len(result3['relationships'])}")

    # 示例 4: 仅 Chunks 检索
    result4 = client.chunks_only(
        rag_ids=["kb1", "kb2", "kb3"],
        keywords=["RAG"],
        chunk_top_k=10
    )
    print(f"Chunks 数量: {len(result4['chunks'])}")

    # 示例 5: 完整图谱查询
    result5 = client.get_full_graph(["kb1", "kb2"])
    print(f"节点数量: {len(result5['data']['nodes'])}")
    print(f"边数量: {len(result5['data']['links'])}")
```

### 12.2 JavaScript/TypeScript 客户端

```javascript
class MultiKBQueryClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * 标准 RAG 查询
     */
    async query(ragIds, question, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/query/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rag_ids: ragIds,
                question,
                mode: 'hybrid',
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }

    /**
     * 关键字检索
     */
    async keywordsSearch(ragIds, keywords, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/query/keywords`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rag_ids: ragIds,
                keywords,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }

    /**
     * 清理图谱检索
     */
    async graphClean(ragIds, keywords = null, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/query/graph-clean`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rag_ids: ragIds,
                keywords,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }

    /**
     * 仅 Chunks 检索
     */
    async chunksOnly(ragIds, keywords = null, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/query/chunks-only`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rag_ids: ragIds,
                keywords,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }

    /**
     * 获取完整图谱
     */
    async getFullGraph(ragIds) {
        const params = new URLSearchParams();
        ragIds.forEach(id => params.append('rag_ids', id));

        const response = await fetch(
            `${this.baseUrl}/api/graph/echarts?${params}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }
}

// 使用示例
const client = new MultiKBQueryClient();

// 示例 1: 多知识库查询
const result1 = await client.query(
    ['kb1', 'kb2', 'kb3'],
    '什么是RAG？',
    { top_k: 10, only_need_context: true }
);
console.log('查询结果:', result1);

// 示例 2: 关键字检索
const result2 = await client.keywordsSearch(
    ['kb1', 'kb2'],
    ['人工智能', '机器学习'],
    { top_k: 10 }
);
console.log('检索结果:', result2);

// 示例 3: 图谱检索
const result3 = await client.graphClean(
    ['kb1', 'kb2'],
    ['人工智能'],
    { top_k: 20 }
);
console.log('实体数量:', result3.entities.length);
console.log('关系数量:', result3.relationships.length);
```

---

## 附录：版本历史

- **v2.0** (2026-01-11): 全面支持多知识库查询
  - 改造所有 5 个 RAG 查询接口支持多知识库
  - 改造所有 4 个图谱查询接口支持多知识库
  - 使用 `asyncio.gather` 实现真正的并发查询
  - 添加 `sources` 字段追踪各知识库贡献
  - 保持向后兼容（支持 `rag_id` 和 `rag_ids`）
  - 实现容错机制和结果合并策略

- **v1.0** (2026-01-10): 初始版本
  - 仅图谱查询接口支持多知识库
