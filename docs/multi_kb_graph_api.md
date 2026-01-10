# 多知识库图谱查询接口文档

本文档介绍改造后的知识图谱查询接口，支持单个或多个知识库的图谱数据查询。

## 目录

- [1. 完整图谱查询 (/echarts)](#1-完整图谱查询-echarts)
- [2. Top-K 节点查询 (/echarts/top-k)](#2-top-k-节点查询-echartstop-k)
- [3. 邻居节点查询 (/echarts/neighbors)](#3-邻居节点查询-echartsneighbors)
- [4. POST 方式查询 (/echarts/multi)](#4-post-方式查询-echartsmulti)
- [5. 返回数据说明](#5-返回数据说明)

---

## 1. 完整图谱查询 (/echarts)

获取一个或多个知识库的完整知识图谱数据（ECharts 格式）。

### 接口信息

- **URL**: `/api/graph/echarts`
- **方法**: `GET`
- **说明**: 查询知识库的全部实体和关系，支持多知识库合并查询

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_ids | string[] | 是 | 知识库 ID 列表，使用重复参数传递 |

### 调用示例

#### 单知识库查询

```bash
# cURL 示例
curl -X GET "http://localhost:8000/api/graph/echarts?rag_ids=kb1"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts",
    params={"rag_ids": "kb1"}
)
print(response.json())
```

#### 多知识库查询

```bash
# cURL 示例
curl -X GET "http://localhost:8000/api/graph/echarts?rag_ids=kb1&rag_ids=kb2&rag_ids=kb3"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts",
    params={"rag_ids": ["kb1", "kb2", "kb3"]}
)
print(response.json())

# JavaScript/Axios 示例
const response = await axios.get('/api/graph/echarts', {
    params: {
        rag_ids: ['kb1', 'kb2', 'kb3']
    },
    paramsSerializer: params => {
        return Object.entries(params)
            .flatMap(([key, values]) =>
                (Array.isArray(values) ? values : [values])
                    .map(v => `${key}=${encodeURIComponent(v)}`)
            )
            .join('&');
    }
});
```

### 返回格式

```json
{
  "status": "success",
  "rag_ids": ["kb1", "kb2"],
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "value": 5,
        "category": 0,
        "entity_type": "CONCEPT",
        "description": "计算机科学的一个重要分支",
        "rag_id": "kb1"
      },
      {
        "id": "机器学习",
        "name": "机器学习",
        "value": 3,
        "category": 0,
        "entity_type": "CONCEPT",
        "description": "人工智能的核心技术",
        "rag_id": "kb1"
      },
      {
        "id": "数据库",
        "name": "数据库",
        "value": 4,
        "category": 1,
        "entity_type": "TECHNOLOGY",
        "rag_id": "kb2"
      }
    ],
    "links": [
      {
        "source": "人工智能",
        "target": "机器学习",
        "description": "包含",
        "weight": 0.9,
        "rag_id": "kb1"
      },
      {
        "source": "数据库",
        "target": "图数据库",
        "description": "类型",
        "weight": 0.8,
        "rag_id": "kb2"
      }
    ],
    "categories": [
      {"name": "CONCEPT"},
      {"name": "TECHNOLOGY"}
    ]
  }
}
```

---

## 2. Top-K 节点查询 (/echarts/top-k)

获取一个或多个知识库中度数最高的 Top-K 个节点及其构成的子图。

### 接口信息

- **URL**: `/api/graph/echarts/top-k`
- **方法**: `GET`
- **说明**: 每个知识库分别取度数最高的 k 个节点，然后合并结果

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_ids | string[] | 是 | - | 知识库 ID 列表 |
| k | integer | 否 | 10 | 每个知识库返回的节点数量 |

### 调用示例

#### 单知识库 Top-5 查询

```bash
# cURL 示例
curl -X GET "http://localhost:8000/api/graph/echarts/top-k?rag_ids=kb1&k=5"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts/top-k",
    params={
        "rag_ids": "kb1",
        "k": 5
    }
)
print(response.json())
```

#### 多知识库 Top-10 查询

```bash
# cURL 示例
curl -X GET "http://localhost:8000/api/graph/echarts/top-k?rag_ids=kb1&rag_ids=kb2&k=10"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts/top-k",
    params={
        "rag_ids": ["kb1", "kb2"],
        "k": 10
    }
)
print(response.json())

# JavaScript/Fetch 示例
const params = new URLSearchParams();
['kb1', 'kb2'].forEach(id => params.append('rag_ids', id));
params.append('k', '10');

const response = await fetch(`/api/graph/echarts/top-k?${params}`);
const data = await response.json();
```

### 返回格式

```json
{
  "status": "success",
  "rag_ids": ["kb1", "kb2"],
  "k": 5,
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "value": 8,
        "category": 0,
        "entity_type": "CONCEPT",
        "symbolSize": 60,
        "rag_id": "kb1"
      },
      {
        "id": "机器学习",
        "name": "机器学习",
        "value": 6,
        "category": 0,
        "entity_type": "CONCEPT",
        "symbolSize": 50,
        "rag_id": "kb1"
      },
      {
        "id": "数据库",
        "name": "数据库",
        "value": 7,
        "category": 1,
        "entity_type": "TECHNOLOGY",
        "symbolSize": 55,
        "rag_id": "kb2"
      }
    ],
    "links": [
      {
        "source": "人工智能",
        "target": "机器学习",
        "value": "包含",
        "rag_id": "kb1"
      },
      {
        "source": "数据库",
        "target": "关系型数据库",
        "value": "类型",
        "rag_id": "kb2"
      }
    ],
    "categories": [
      {"name": "CONCEPT"},
      {"name": "TECHNOLOGY"}
    ]
  }
}
```

### 说明

- 每个知识库独立计算 Top-K 节点，因此返回的总节点数最多为 `k × len(rag_ids)`
- 节点按度数（连接的边数量）排序
- `value` 字段表示节点的度数

---

## 3. 邻居节点查询 (/echarts/neighbors)

获取指定节点在一个或多个知识库中的邻居节点构成的子图。

### 接口信息

- **URL**: `/api/graph/echarts/neighbors`
- **方法**: `GET`
- **说明**: 查询指定节点的直接邻居（一跳关系）

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| node_id | string | 是 | 中心节点的 ID（实体名称） |
| rag_ids | string[] | 是 | 知识库 ID 列表 |

### 调用示例

#### 单知识库邻居查询

```bash
# cURL 示例
curl -X GET "http://localhost:8000/api/graph/echarts/neighbors?node_id=人工智能&rag_ids=kb1"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts/neighbors",
    params={
        "node_id": "人工智能",
        "rag_ids": "kb1"
    }
)
print(response.json())
```

#### 多知识库邻居查询

```bash
# cURL 示例（注意中文需要 URL 编码）
curl -X GET "http://localhost:8000/api/graph/echarts/neighbors?node_id=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD&rag_ids=kb1&rag_ids=kb2"

# Python 示例
import requests

response = requests.get(
    "http://localhost:8000/api/graph/echarts/neighbors",
    params={
        "node_id": "人工智能",
        "rag_ids": ["kb1", "kb2"]
    }
)
print(response.json())

# JavaScript/URLSearchParams 示例
const params = new URLSearchParams({
    node_id: '人工智能'
});
['kb1', 'kb2'].forEach(id => params.append('rag_ids', id));

const response = await fetch(`/api/graph/echarts/neighbors?${params}`);
const data = await response.json();
```

### 返回格式

```json
{
  "status": "success",
  "node_id": "人工智能",
  "rag_ids": ["kb1", "kb2"],
  "data": {
    "nodes": [
      {
        "id": "人工智能",
        "name": "人工智能",
        "value": 5,
        "category": 0,
        "entity_type": "CONCEPT",
        "rag_id": "kb1"
      },
      {
        "id": "机器学习",
        "name": "机器学习",
        "value": 3,
        "category": 0,
        "entity_type": "CONCEPT",
        "rag_id": "kb1"
      },
      {
        "id": "深度学习",
        "name": "深度学习",
        "value": 2,
        "category": 0,
        "entity_type": "CONCEPT",
        "rag_id": "kb1"
      }
    ],
    "links": [
      {
        "source": "人工智能",
        "target": "机器学习",
        "description": "包含",
        "rag_id": "kb1"
      },
      {
        "source": "人工智能",
        "target": "深度学习",
        "description": "相关",
        "rag_id": "kb1"
      }
    ],
    "categories": [
      {"name": "CONCEPT"}
    ]
  }
}
```

### 说明

- 如果指定节点在某个知识库中不存在，该知识库会被跳过
- 返回的是一跳邻居（直接连接的节点）
- 中心节点也会包含在返回的节点列表中

---

## 4. POST 方式查询 (/echarts/multi)

使用 POST 请求查询多个知识库的完整图谱数据。

### 接口信息

- **URL**: `/api/graph/echarts/multi`
- **方法**: `POST`
- **说明**: 功能与 GET `/echarts` 相同，但使用 POST 请求体传递参数

### 请求参数

**Content-Type**: `application/json`

```json
{
  "rag_ids": ["kb1", "kb2", "kb3"]
}
```

### 调用示例

#### 单知识库查询

```bash
# cURL 示例
curl -X POST "http://localhost:8000/api/graph/echarts/multi" \
  -H "Content-Type: application/json" \
  -d '{"rag_ids": ["kb1"]}'

# Python 示例
import requests

response = requests.post(
    "http://localhost:8000/api/graph/echarts/multi",
    json={"rag_ids": ["kb1"]}
)
print(response.json())
```

#### 多知识库查询

```bash
# cURL 示例
curl -X POST "http://localhost:8000/api/graph/echarts/multi" \
  -H "Content-Type: application/json" \
  -d '{"rag_ids": ["kb1", "kb2", "kb3"]}'

# Python 示例
import requests

response = requests.post(
    "http://localhost:8000/api/graph/echarts/multi",
    json={"rag_ids": ["kb1", "kb2", "kb3"]}
)
print(response.json())

# JavaScript/Axios 示例
const response = await axios.post('/api/graph/echarts/multi', {
    rag_ids: ['kb1', 'kb2', 'kb3']
});
console.log(response.data);
```

### 返回格式

```json
{
  "status": "success",
  "rag_ids": ["kb1", "kb2"],
  "data": {
    "nodes": [
      {
        "id": "实体A@kb1",
        "name": "实体A",
        "value": 5,
        "category": 0,
        "entity_type": "CONCEPT",
        "rag_id": "kb1"
      },
      {
        "id": "实体B@kb2",
        "name": "实体B",
        "value": 3,
        "category": 1,
        "entity_type": "TECHNOLOGY",
        "rag_id": "kb2"
      }
    ],
    "links": [
      {
        "source": "实体A@kb1",
        "target": "实体C@kb1",
        "description": "关系描述",
        "rag_id": "kb1"
      }
    ],
    "categories": [
      {"name": "CONCEPT"},
      {"name": "TECHNOLOGY"}
    ]
  }
}
```

### 说明

- 此接口使用 `entity_name@rag_id` 格式作为节点 ID，与 GET `/echarts` 接口不同
- 适合需要传递大量知识库 ID 的场景
- 推荐在前端应用中使用 GET `/echarts` 接口，更符合 RESTful 规范

---

## 5. 返回数据说明

### 5.1 通用响应结构

所有接口返回的 JSON 格式都包含以下顶层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 请求状态，成功为 "success" |
| rag_ids | string[] | 实际查询成功的知识库 ID 列表 |
| data | object | ECharts 格式的图谱数据 |

### 5.2 节点 (nodes) 字段说明

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| id | string | 是 | 节点唯一标识（实体名称） |
| name | string | 是 | 节点显示名称 |
| value | number | 是 | 节点值（通常为度数） |
| category | number | 是 | 分类索引，对应 categories 数组 |
| entity_type | string | 是 | 实体类型（如 CONCEPT、PERSON 等） |
| rag_id | string | 是 | **来源知识库 ID** |
| description | string | 否 | 节点描述信息 |
| symbolSize | number | 否 | 节点大小（仅 top-k 接口） |

### 5.3 边 (links) 字段说明

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| source | string | 是 | 源节点 ID |
| target | string | 是 | 目标节点 ID |
| rag_id | string | 是 | **来源知识库 ID** |
| description | string | 否 | 关系描述 |
| weight | number | 否 | 关系权重 (0-1) |
| keywords | string | 否 | 关系关键词 |
| value | string | 否 | 关系类型（仅 top-k 接口） |

### 5.4 分类 (categories) 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 分类名称（实体类型） |

分类数组的索引与节点的 `category` 字段对应。

### 5.5 核心特性

#### ✅ 多知识库支持
- 所有接口都支持传入一个或多个知识库 ID
- 使用 `rag_id` 字段标识每个节点和边的来源

#### ✅ 数据合并
- 多知识库查询时，自动合并所有数据
- 使用 `(entity_name, rag_id)` 作为节点的唯一键
- 同名实体在不同知识库中被视为不同节点

#### ✅ 容错处理
- 自动跳过不存在或未初始化的知识库
- `rag_ids` 响应字段返回实际成功查询的知识库列表
- 如果所有知识库都失败，返回 404 错误

---

## 6. 错误响应

### 6.1 参数错误 (400)

```json
{
  "detail": "至少需要提供一个知识库 ID"
}
```

### 6.2 知识库不存在 (404)

```json
{
  "detail": "没有找到有效的知识库或所有知识库的 RAG 系统未初始化"
}
```

### 6.3 服务器错误 (500)

```json
{
  "detail": "获取图谱数据失败: <错误详情>"
}
```

---

## 7. 完整示例：Python 客户端

```python
import requests

class MultiKBGraphClient:
    """多知识库图谱查询客户端"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/graph"

    def get_full_graph(self, rag_ids):
        """获取完整图谱"""
        if isinstance(rag_ids, str):
            rag_ids = [rag_ids]

        response = requests.get(
            f"{self.base_url}{self.api_prefix}/echarts",
            params={"rag_ids": rag_ids}
        )
        response.raise_for_status()
        return response.json()

    def get_top_k(self, rag_ids, k=10):
        """获取 Top-K 节点"""
        if isinstance(rag_ids, str):
            rag_ids = [rag_ids]

        response = requests.get(
            f"{self.base_url}{self.api_prefix}/echarts/top-k",
            params={"rag_ids": rag_ids, "k": k}
        )
        response.raise_for_status()
        return response.json()

    def get_neighbors(self, node_id, rag_ids):
        """获取节点邻居"""
        if isinstance(rag_ids, str):
            rag_ids = [rag_ids]

        response = requests.get(
            f"{self.base_url}{self.api_prefix}/echarts/neighbors",
            params={"node_id": node_id, "rag_ids": rag_ids}
        )
        response.raise_for_status()
        return response.json()

# 使用示例
if __name__ == "__main__":
    client = MultiKBGraphClient()

    # 示例 1: 单知识库完整图谱
    result1 = client.get_full_graph("kb1")
    print(f"知识库 kb1 节点数: {len(result1['data']['nodes'])}")

    # 示例 2: 多知识库完整图谱
    result2 = client.get_full_graph(["kb1", "kb2", "kb3"])
    print(f"3个知识库合并节点数: {len(result2['data']['nodes'])}")

    # 示例 3: Top-5 节点查询
    result3 = client.get_top_k(["kb1", "kb2"], k=5)
    print(f"Top-5 查询节点数: {len(result3['data']['nodes'])}")

    # 示例 4: 邻居查询
    result4 = client.get_neighbors("人工智能", ["kb1", "kb2"])
    print(f"节点'人工智能'的邻居数: {len(result4['data']['nodes']) - 1}")

    # 示例 5: 统计各知识库数据
    for node in result2['data']['nodes']:
        print(f"节点: {node['name']}, 来源: {node['rag_id']}")
```

---

## 8. 前端集成示例：ECharts 可视化

```javascript
/**
 * 多知识库图谱可视化
 */
class MultiKBGraphVisualizer {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiPrefix = '/api/graph';
    }

    /**
     * 获取并渲染图谱
     */
    async renderGraph(containerId, ragIds, options = {}) {
        try {
            // 获取图谱数据
            const data = await this.getFullGraph(ragIds);

            // 初始化 ECharts
            const chart = echarts.init(document.getElementById(containerId));

            // 配置选项
            const option = {
                title: {
                    text: `知识图谱 (${data.rag_ids.join(', ')})`,
                    subtext: `节点: ${data.data.nodes.length}, 边: ${data.data.links.length}`
                },
                tooltip: {
                    formatter: (params) => {
                        if (params.dataType === 'node') {
                            return `
                                <strong>${params.data.name}</strong><br/>
                                类型: ${params.data.entity_type}<br/>
                                来源: ${params.data.rag_id}<br/>
                                连接数: ${params.data.value}
                            `;
                        } else {
                            return `
                                ${params.data.source} → ${params.data.target}<br/>
                                来源: ${params.data.rag_id}
                            `;
                        }
                    }
                },
                legend: [{
                    data: data.data.categories.map(c => c.name)
                }],
                series: [{
                    type: 'graph',
                    layout: 'force',
                    data: data.data.nodes,
                    links: data.data.links,
                    categories: data.data.categories,
                    roam: true,
                    label: {
                        show: true,
                        position: 'right'
                    },
                    force: {
                        repulsion: 100,
                        edgeLength: 150
                    }
                }]
            };

            chart.setOption(option);
            return chart;

        } catch (error) {
            console.error('渲染图谱失败:', error);
            throw error;
        }
    }

    /**
     * 获取完整图谱数据
     */
    async getFullGraph(ragIds) {
        const params = new URLSearchParams();
        (Array.isArray(ragIds) ? ragIds : [ragIds])
            .forEach(id => params.append('rag_ids', id));

        const response = await fetch(
            `${this.baseUrl}${this.apiPrefix}/echarts?${params}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }

    /**
     * 获取 Top-K 数据
     */
    async getTopK(ragIds, k = 10) {
        const params = new URLSearchParams({ k });
        (Array.isArray(ragIds) ? ragIds : [ragIds])
            .forEach(id => params.append('rag_ids', id));

        const response = await fetch(
            `${this.baseUrl}${this.apiPrefix}/echarts/top-k?${params}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        return await response.json();
    }
}

// 使用示例
const visualizer = new MultiKBGraphVisualizer();

// 渲染单知识库图谱
visualizer.renderGraph('chart1', 'kb1');

// 渲染多知识库合并图谱
visualizer.renderGraph('chart2', ['kb1', 'kb2', 'kb3']);

// 渲染 Top-10 节点
visualizer.getTopK(['kb1', 'kb2'], 10)
    .then(data => {
        // 自定义渲染逻辑
        console.log('Top-10 数据:', data);
    });
```

---

## 9. 接口对比总结

| 接口 | 方法 | 功能 | 节点 ID 格式 | 适用场景 |
|------|------|------|-------------|----------|
| `/echarts` | GET | 完整图谱 | `entity_name` | 推荐使用，RESTful |
| `/echarts/top-k` | GET | Top-K 子图 | `entity_name` | 大图谱概览 |
| `/echarts/neighbors` | GET | 邻居子图 | `entity_name` | 局部探索 |
| `/echarts/multi` | POST | 完整图谱 | `entity_name@rag_id` | 大量知识库查询 |

**推荐使用 GET 接口**，除非需要传递大量知识库 ID（超过 50 个）。

---

## 10. 常见问题

### Q1: 如何处理同名实体？

不同知识库中的同名实体会被视为不同节点，通过 `rag_id` 字段区分。

```json
{
  "nodes": [
    {"id": "Python", "rag_id": "programming_kb"},
    {"id": "Python", "rag_id": "animal_kb"}
  ]
}
```

### Q2: 返回的知识库数量与请求不一致？

部分知识库可能不存在或未初始化，会被自动跳过。检查响应中的 `rag_ids` 字段查看实际成功的知识库。

### Q3: 如何限制返回的数据量？

使用 `/echarts/top-k` 接口并设置合适的 `k` 值，而不是使用 `/echarts` 获取全量数据。

### Q4: 边的 source 和 target 必须在同一知识库吗？

目前设计中，边的 source 和 target 都来自同一知识库（通过 `rag_id` 标识）。跨知识库的关系需要应用层处理。

---

## 附录：版本历史

- **v1.0** (2026-01-10): 初始版本，支持多知识库图谱查询
  - 添加 GET `/echarts` 接口
  - 添加 GET `/echarts/top-k` 接口
  - 添加 GET `/echarts/neighbors` 接口
  - 改造 POST `/echarts/multi` 接口
  - 所有接口添加 `rag_id` 字段标注数据来源
