# NebulaGraph Schema 设计与实现详解

## 目录

- [架构概览](#架构概览)
- [Schema 定义](#schema-定义)
- [实体（节点）字段](#实体节点字段)
- [关系（边）字段](#关系边字段)
- [关联规则](#关联规则)
- [数据流程](#数据流程)
- [查询优化](#查询优化)

---

## 架构概览

### 多租户隔离设计

xwRAG 使用 **workspace → Space** 的方式实现完全的多租户隔离：

```
┌─────────────────────────────────────────────┐
│        NebulaGraph 集群                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  workspace: "base"  → Space: "base"  │  │
│  │    Tag: entity                       │  │
│  │    Edge: relationship                │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  workspace: "project1" → Space: "project1"│
│  │    Tag: entity                       │  │
│  │    Edge: relationship                │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  workspace: "project2" → Space: "project2"│
│  │    Tag: entity                       │  │
│  │    Edge: relationship                │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**设计优势**：
- ✅ **完全隔离**：每个 workspace 有独立的 Space，数据互不干扰
- ✅ **性能更好**：查询只在自己的 Space 中，减少数据扫描
- ✅ **管理简单**：删除 workspace 直接 `DROP SPACE`
- ✅ **统一 Schema**：所有 Space 使用相同的 Tag 和 Edge 定义

---

## Schema 定义

### Space 创建

```cypher
-- 创建 Space（每个 workspace 一个）
CREATE SPACE IF NOT EXISTS base (
  partition_num=10,           -- 分区数量
  replica_factor=1,           -- 副本因子
  vid_type=FIXED_STRING(256)  -- 节点 ID 类型
);

USE base;
```

**参数说明**：
- `partition_num=10`: 数据分区数，影响分布式性能
- `replica_factor=1`: 副本数量，生产环境建议 3
- `vid_type=FIXED_STRING(256)`: 节点 ID 使用定长字符串

### Tag 定义（实体节点）

```cypher
-- 创建固定的 Tag "entity"（所有实体节点都使用这个 Tag）
CREATE TAG IF NOT EXISTS entity (
  entity_id string,      -- 实体唯一标识
  entity_type string,    -- 实体类型（Person, Organization, Concept 等）
  description string,    -- 实体描述
  source_id string,      -- 来源 chunk ID
  file_path string,      -- 文件路径
  created_at int         -- 创建时间戳
);
```

### Edge 定义（关系）

```cypher
-- 创建 Edge type "relationship"（所有关系都使用这个类型）
CREATE EDGE IF NOT EXISTS relationship (
  weight double,        -- 关系权重（重要性）
  description string,   -- 关系描述
  keywords string,      -- 关键词
  source_id string      -- 来源 chunk ID
);
```

### 索引创建

```cypher
-- 创建 entity_id 索引（用于主键查询）
CREATE TAG INDEX IF NOT EXISTS idx_entity_id ON entity(entity_id(256));

-- 创建 source_id 索引（用于按 chunk 过滤）
CREATE TAG INDEX IF NOT EXISTS idx_source_id ON entity(source_id(256));

-- 等待索引构建完成
SHOW TAG INDEX STATUS;
REBUILD TAG INDEX idx_entity_id;
REBUILD TAG INDEX idx_source_id;
```

---

## 实体（节点）字段

### 字段详解

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **entity_id** | string | 实体唯一标识符，用作节点 VID | `"人工智能"` |
| **entity_type** | string | 实体类型 | `"Concept"`, `"Person"`, `"Organization"` |
| **description** | string | 实体的详细描述 | `"人工智能是计算机科学的一个分支..."` |
| **source_id** | string | 提取该实体的源 chunk ID | `"chunk_abc123"` |
| **file_path** | string | 源文件路径 | `"docs/ai_overview.pdf"` |
| **created_at** | int | 创建时间戳（Unix 时间） | `1701234567` |

### 实体类型

默认支持的实体类型（可在 `.env` 中配置 `ENTITY_TYPES`）：

```python
DEFAULT_ENTITY_TYPES = [
    "Person",          # 人物
    "Creature",        # 生物
    "Organization",    # 组织机构
    "Location",        # 地点
    "Event",           # 事件
    "Concept",         # 概念
    "Method",          # 方法
    "Content",         # 内容
    "Data",            # 数据
    "Artifact",        # 人工制品
    "NaturalObject",   # 自然物体
]
```

### 插入实体示例

```cypher
-- 插入单个实体
INSERT VERTEX IF NOT EXISTS entity(entity_id, entity_type, description, source_id, file_path, created_at)
VALUES "人工智能": (
  "人工智能",
  "Concept",
  "人工智能是计算机科学的一个分支，致力于创建能够执行需要人类智能的任务的系统",
  "chunk_abc123",
  "docs/ai_overview.pdf",
  1701234567
);

-- 批量插入实体
INSERT VERTEX IF NOT EXISTS entity(entity_id, entity_type, description, source_id, file_path, created_at)
VALUES
  "机器学习": ("机器学习", "Concept", "...", "chunk_abc123", "docs/ai_overview.pdf", 1701234567),
  "深度学习": ("深度学习", "Concept", "...", "chunk_abc123", "docs/ai_overview.pdf", 1701234567),
  "神经网络": ("神经网络", "Concept", "...", "chunk_abc123", "docs/ai_overview.pdf", 1701234567);
```

### Python 代码中的实体创建

```python
# 在 nebula_impl.py 的 upsert_node 方法中
async def upsert_node(self, node_id: str, node_data: Dict[str, Any]) -> Dict[str, str]:
    """插入或更新节点"""
    if "entity_id" not in node_data:
        node_data["entity_id"] = node_id

    # 格式化属性
    props_str = self._format_properties(node_data)
    tag = self._tag_name  # "entity"

    # 构建查询
    query = (
        f'INSERT VERTEX IF NOT EXISTS {tag}(entity_id, entity_type, description, source_id, file_path, created_at) '
        f'VALUES "{self._escape_string(node_id)}": ({props_str})'
    )

    await self._execute_query(query)
    return {"status": "success", "message": "node upserted"}
```

---

## 关系（边）字段

### 字段详解

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **weight** | double | 关系权重，表示关系的重要性 | `1.5`, `2.0` |
| **description** | string | 关系描述 | `"是...的一个子领域"`, `"用于..."` |
| **keywords** | string | 关系关键词（逗号分隔） | `"subset, subcategory"` |
| **source_id** | string | 提取该关系的源 chunk ID | `"chunk_abc123"` |

### 关系方向

NebulaGraph 的边是**有向的**：

```
源实体 (source) ----[relationship]----> 目标实体 (target)
```

**示例**：
```cypher
-- "机器学习" 是 "人工智能" 的子领域
"机器学习" ----[relationship]----> "人工智能"

-- 关系方向表示：机器学习 → 人工智能（从属关系）
```

### 插入关系示例

```cypher
-- 插入单个关系
INSERT EDGE relationship(weight, description, keywords, source_id)
VALUES "机器学习" -> "人工智能": (
  1.5,                                    -- 权重
  "机器学习是人工智能的一个重要子领域",    -- 描述
  "subset,subcategory",                  -- 关键词
  "chunk_abc123"                         -- 来源
);

-- 批量插入关系（在同一个 chunk 中提取的）
INSERT EDGE relationship(weight, description, keywords, source_id)
VALUES
  "机器学习" -> "人工智能": (1.5, "...", "subset", "chunk_abc123"),
  "深度学习" -> "机器学习": (1.5, "...", "subset", "chunk_abc123"),
  "神经网络" -> "深度学习": (1.5, "...", "basis", "chunk_abc123");
```

### Python 代码中的关系创建

```python
# 在 nebula_impl.py 的 upsert_edge 方法中
async def upsert_edge(self, source_node_id: str, target_node_id: str, edge_data: Dict[str, Any]) -> Dict[str, str]:
    """插入或更新边"""
    weight = edge_data.get("weight", 1.0)
    description = self._escape_string(edge_data.get("description", ""))
    keywords = self._escape_string(edge_data.get("keywords", ""))
    source_id = self._escape_string(edge_data.get("source_id", ""))

    # INSERT EDGE 是幂等的，重复插入会更新
    query = (
        f'INSERT EDGE relationship(weight, description, keywords, source_id) VALUES '
        f'"{self._escape_string(source_node_id)}" -> "{self._escape_string(target_node_id)}": '
        f'({weight}, "{description}", "{keywords}", "{source_id}")'
    )

    await self._execute_query(query)
    return {"status": "success", "message": "edge upserted"}
```

---

## 关联规则

### 1. 实体提取规则

实体从文档 chunks 中通过 LLM 提取，遵循以下规则：

#### 提取格式

```python
# LLM 输出格式（在 operate.py 中定义）
# 格式：(entity|<entity_name>|<entity_type>|<entity_description>)
"""
(entity|人工智能|Concept|人工智能是计算机科学的一个分支)
(entity|机器学习|Concept|机器学习是实现人工智能的一种方法)
(entity|深度学习|Concept|深度学习是机器学习的一个子领域)
"""
```

#### 处理流程（_handle_single_entity_extraction）

```python
async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    timestamp: int,
    file_path: str = "unknown_source",
):
    # 1. 验证格式（必须有 4 个字段）
    if len(record_attributes) != 4 or "entity" not in record_attributes[0]:
        return None

    # 2. 清理实体名称
    entity_name = sanitize_and_normalize_extracted_text(
        record_attributes[1], remove_inner_quotes=True
    )

    # 3. 验证非空
    if not entity_name or not entity_name.strip():
        return None

    # 4. 清理实体类型
    entity_type = sanitize_and_normalize_extracted_text(
        record_attributes[2], remove_inner_quotes=True
    )

    # 5. 清理描述
    entity_description = sanitize_and_normalize_extracted_text(
        record_attributes[3], remove_inner_quotes=False
    )

    # 6. 返回实体数据
    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "description": entity_description,
        "source_id": chunk_key,
        "file_path": file_path,
    }
```

### 2. 关系提取规则

关系同样从文档 chunks 中通过 LLM 提取：

#### 提取格式

```python
# LLM 输出格式
# 格式：(relation|<source_entity>|<target_entity>|<description>|<keywords>)
"""
(relation|机器学习|人工智能|机器学习是人工智能的一个子领域|subset,subcategory)
(relation|深度学习|机器学习|深度学习是机器学习的一种方法|method,approach)
(relation|神经网络|深度学习|神经网络是深度学习的基础|basis,foundation)
"""
```

#### 处理流程（_handle_single_relationship_extraction）

```python
async def _handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
    timestamp: int,
    file_path: str = "unknown_source",
):
    # 1. 验证格式（必须有 5 个字段）
    if len(record_attributes) != 5 or "relation" not in record_attributes[0]:
        return None

    # 2. 清理源实体和目标实体
    source = sanitize_and_normalize_extracted_text(
        record_attributes[1], remove_inner_quotes=True
    )
    target = sanitize_and_normalize_extracted_text(
        record_attributes[2], remove_inner_quotes=True
    )

    # 3. 验证实体名称非空
    if not source or not target:
        return None

    # 4. 清理描述和关键词
    description = sanitize_and_normalize_extracted_text(
        record_attributes[3], remove_inner_quotes=False
    )
    keywords = sanitize_and_normalize_extracted_text(
        record_attributes[4], remove_inner_quotes=True
    )

    # 5. 计算权重（默认为 1.0）
    weight = 1.0

    # 6. 返回关系数据
    return {
        "src_id": source,
        "tgt_id": target,
        "description": description,
        "keywords": keywords,
        "weight": weight,
        "source_id": chunk_key,
    }
```

### 3. 关联建立规则

#### 规则 1: 同名实体合并

如果两个 chunk 中提取了相同名称的实体，它们会被合并为一个节点：

```python
# 节点 ID = 实体名称（规范化后）
node_id = entity_name  # 例如："人工智能"

# 使用 INSERT VERTEX IF NOT EXISTS 确保幂等性
# 如果节点已存在，只更新描述（合并描述）
```

**示例**：

```
Chunk 1: "人工智能是计算机科学的分支"
  → 提取实体: (entity|人工智能|Concept|计算机科学的分支)

Chunk 2: "人工智能用于解决复杂问题"
  → 提取实体: (entity|人工智能|Concept|用于解决复杂问题)

合并后:
  节点 ID: "人工智能"
  描述: 合并后的描述（包含多个来源）
```

#### 规则 2: 关系基于实体名称

关系通过**实体名称**建立连接，而不是实体 ID：

```python
# 关系定义
source_entity = "机器学习"   # 源实体名称
target_entity = "人工智能"   # 目标实体名称

# 创建边
INSERT EDGE relationship(...)
VALUES "机器学习" -> "人工智能": (...)
```

**这意味着**：
- ✅ 只要实体名称匹配，就能建立关系
- ✅ 跨 chunk 的实体可以自动关联
- ✅ 支持传递性关系（A→B, B→C => A→B→C）

#### 规则 3: 权重计算

关系权重影响检索时的排序：

```python
# 默认权重
weight = 1.0

# 权重可以基于多种因素调整：
# - 关系在多个 chunk 中重复出现 → 权重增加
# - 关系描述更详细 → 权重增加
# - 实体共现频率高 → 权重增加
```

#### 规则 4: 来源追踪

每个实体和关系都保留 `source_id` 和 `file_path`，用于：

- 📍 **溯源**：追踪信息来源
- 📍 **过滤**：按文档或 chunk 过滤
- 📍 **更新**：删除特定文档时清理相关数据

```cypher
-- 查询来自特定 chunk 的所有实体
MATCH (v:entity)
WHERE v.source_id == "chunk_abc123"
RETURN v;

-- 查询来自特定文件的所有关系
MATCH (v1)-[e:relationship]->(v2)
WHERE e.source_id CONTAINS "ai_overview.pdf"
RETURN v1, e, v2;
```

---

## 数据流程

### 完整的数据处理流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 文档输入                                                   │
│    - PDF、DOCX、TXT 等                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. 文档分块 (Chunking)                                       │
│    - 按 token 大小分块（默认 1200 tokens）                   │
│    - 重叠 100 tokens                                         │
│    - 生成 chunk_id (MD5 hash)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. LLM 实体和关系提取 (extract_entities)                     │
│    - 输入: text chunks                                       │
│    - Prompt: "从文本中提取实体和关系..."                      │
│    - 输出: (entity|...) 和 (relation|...) 记录                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. 解析和清理 (_process_extraction_result)                   │
│    - 按行分割 LLM 输出                                        │
│    - 解析每条记录                                            │
│    - 清理和规范化文本                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼──────────┐  ┌─────────▼──────────┐
│ 5a. 实体处理      │  │ 5b. 关系处理        │
│ (upsert_node)     │  │ (upsert_edge)       │
└────────┬──────────┘  └─────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. 存储到 NebulaGraph                                         │
│    - INSERT VERTEX IF NOT EXISTS entity(...)                 │
│    - INSERT EDGE relationship(...)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 7. 索引和优化                                                 │
│    - 索引自动用于查询优化                                      │
│    - 批量操作提升性能                                         │
└─────────────────────────────────────────────────────────────┘
```

### 代码示例：完整流程

```python
# 1. 输入文档
text = "人工智能是计算机科学的一个分支。机器学习是实现人工智能的方法。"

# 2. 分块
chunks = chunking_by_token_size(
    tokenizer=tokenizer,
    content=text,
    max_token_size=1200,
    overlap_token_size=100
)
# chunks = {
#   "chunk_abc123": {"content": "人工智能是计算机科学...", ...}
# }

# 3. LLM 提取
extraction_results = await extract_entities(
    chunks=chunks,
    global_config=config,
    llm_response_cache=cache,
    text_chunks_storage=storage
)
# LLM 输出:
# (entity|人工智能|Concept|计算机科学的一个分支)
# (entity|机器学习|Method|实现人工智能的方法)
# (relation|机器学习|人工智能|机器学习用于实现人工智能|implementation)

# 4. 解析
nodes, edges = await _process_extraction_result(
    result=llm_output,
    chunk_key="chunk_abc123",
    timestamp=timestamp,
    file_path="ai_overview.pdf"
)
# nodes = {
#   "人工智能": {"entity_type": "Concept", "description": "...", ...},
#   "机器学习": {"entity_type": "Method", "description": "...", ...}
# }
# edges = {
#   ("机器学习", "人工智能"): {"description": "...", "weight": 1.0, ...}
# }

# 5. 存储到 NebulaGraph
for node_id, node_data in nodes.items():
    await graph_storage.upsert_node(node_id, node_data)

for (src, tgt), edge_data in edges.items():
    await graph_storage.upsert_edge(src, tgt, edge_data)
```

---

## 查询优化

### 1. 索引优化

NebulaGraph 使用两个关键索引：

```cypher
-- entity_id 索引：用于精确匹配
CREATE TAG INDEX idx_entity_id ON entity(entity_id(256));

-- source_id 索引：用于按来源过滤
CREATE TAG INDEX idx_source_id ON entity(source_id(256));
```

**使用场景**：

```cypher
-- 场景 1: 查找特定实体（使用 entity_id 索引）
MATCH (v:entity)
WHERE v.entity_id == "人工智能"
RETURN v;

-- 场景 2: 查找来自特定文档的实体（使用 source_id 索引）
MATCH (v:entity)
WHERE v.source_id STARTS WITH "ai_overview"
RETURN v;
```

### 2. 批量查询优化（40 倍性能提升）

项目实现了批量边查询优化：

```python
# ❌ 低效方式：循环查询（N 次网络往返）
for entity_id in entity_ids:
    edges = await get_edges_for_entity(entity_id)

# ✅ 高效方式：批量查询（1 次网络往返）
edges = await get_edges_batch(entity_ids)
```

**实现原理**：

```cypher
-- 批量查询所有实体的出边和入边
MATCH (v:entity)-[e:relationship]-(v2:entity)
WHERE id(v) IN ["实体1", "实体2", "实体3", ...]
RETURN id(v) AS entity_id, e, id(v2) AS neighbor_id;
```

**性能对比**：
- 单次查询：100 个实体 → 100 次往返 → ~5000ms
- 批量查询：100 个实体 → 1 次往返 → ~125ms
- **性能提升**: 40 倍 🚀

### 3. 查询模式示例

#### 3.1 一度邻居查询

```cypher
-- 查找"人工智能"的所有邻居
MATCH (v:entity)-[e:relationship]-(v2:entity)
WHERE v.entity_id == "人工智能"
RETURN v2.entity_id, e.description, e.weight
ORDER BY e.weight DESC
LIMIT 20;
```

#### 3.2 多跳路径查询

```cypher
-- 查找"机器学习"到"神经科学"的路径（最多 3 跳）
MATCH path = (v1:entity)-[e:relationship*1..3]-(v2:entity)
WHERE v1.entity_id == "机器学习" AND v2.entity_id == "神经科学"
RETURN path
ORDER BY reduce(weight = 0.0, r in relationships(path) | weight + r.weight) DESC
LIMIT 5;
```

#### 3.3 子图查询

```cypher
-- 查找以"深度学习"为中心的 2 度子图
MATCH (center:entity)-[e1:relationship*1..2]-(neighbor:entity)
WHERE center.entity_id == "深度学习"
RETURN center, e1, neighbor;
```

#### 3.4 聚合统计

```cypher
-- 统计每个实体类型的数量
MATCH (v:entity)
RETURN v.entity_type, count(*) AS count
ORDER BY count DESC;

-- 统计关系权重分布
MATCH ()-[e:relationship]->()
RETURN
  floor(e.weight) AS weight_range,
  count(*) AS count
ORDER BY weight_range;
```

### 4. 查询性能优化建议

#### 使用 LIMIT 限制结果

```cypher
-- ❌ 不推荐：返回所有结果
MATCH (v:entity) RETURN v;

-- ✅ 推荐：限制返回数量
MATCH (v:entity) RETURN v LIMIT 100;
```

#### 使用索引字段过滤

```cypher
-- ✅ 使用索引字段（entity_id）
MATCH (v:entity)
WHERE v.entity_id == "人工智能"
RETURN v;

-- ⚠️ 非索引字段扫描较慢
MATCH (v:entity)
WHERE v.description CONTAINS "深度学习"
RETURN v;
```

#### 避免全图扫描

```cypher
-- ❌ 全图扫描（慢）
MATCH (v1)-[e]->(v2)
RETURN v1, e, v2;

-- ✅ 从特定节点开始（快）
MATCH (v1:entity {entity_id: "人工智能"})-[e]->(v2)
RETURN v1, e, v2;
```

---

## 总结

### 核心设计特点

1. **简化的 Schema**:
   - 固定 Tag "entity"
   - 固定 Edge "relationship"
   - 通过属性字段实现灵活性

2. **多租户隔离**:
   - workspace → Space 映射
   - 完全的数据隔离

3. **性能优化**:
   - 批量操作
   - 索引优化
   - 40 倍查询性能提升

4. **可追溯性**:
   - source_id 追踪来源
   - file_path 记录文件
   - created_at 时间戳

5. **关联规则**:
   - 基于实体名称建立关系
   - 跨 chunk 自动关联
   - 权重表示重要性

### 数据关系示意图

```
                    ┌──────────────┐
                    │  人工智能     │
                    │ (Concept)    │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ relationship  │
                    │ weight: 1.5   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  机器学习     │
                    │ (Method)     │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ relationship  │
                    │ weight: 1.5   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  深度学习     │
                    │ (Method)     │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ relationship  │
                    │ weight: 2.0   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  神经网络     │
                    │ (Artifact)   │
                    └──────────────┘
```

---

## 参考资源

- **NebulaGraph 文档**: https://docs.nebula-graph.io/
- **项目源码**: `xwrag/kg/nebula_impl.py`
- **类型定义**: `xwrag/types.py`
- **提取逻辑**: `xwrag/operate.py`
