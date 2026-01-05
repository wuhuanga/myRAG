# 逻辑隔离模式测试指南

## 📋 测试脚本说明

`test_logical_isolation.py` 是一个自动化测试脚本，用于验证 Nebula 和 Milvus 逻辑隔离模式下的删除功能是否正常工作。

## 🎯 测试目标

验证删除一个 RAG 实例时：
- ✅ 该实例在 Nebula 中的图数据被正确删除
- ✅ 该实例在 Milvus 中的向量数据被正确删除
- ✅ 其他实例的数据完全不受影响
- ✅ 实现了真正的逻辑隔离

## 🚀 快速开始

### 1. 确保服务运行

```bash
# 确保后端服务正在运行
# 默认地址: http://localhost:8000

# 检查服务状态
curl http://localhost:8000/admin/health
```

### 2. 运行测试

```bash
# 基本用法
python test_logical_isolation.py

# 指定自定义 URL
python test_logical_isolation.py --base-url http://localhost:8000

# 只清理测试数据（不运行测试）
python test_logical_isolation.py --cleanup-only
```

## 📝 测试流程

测试脚本会自动执行以下步骤：

### 步骤 1: 创建 3 个 RAG 实例
- `tech_docs` (workspace: tech) - 技术文档知识库
- `legal_docs` (workspace: legal) - 法律文档知识库
- `medical_docs` (workspace: medical) - 医疗文档知识库

### 步骤 2: 验证实例列表
- 确认 3 个实例都已创建
- 验证每个实例的 workspace 正确

### 步骤 3: 插入测试文档
- tech_docs: Python 编程语言介绍
- legal_docs: 合同法基础知识
- medical_docs: 糖尿病医疗指南

### 步骤 4: 验证查询功能（删除前）
- 测试每个实例的查询功能
- 确认都能正常返回结果

### 步骤 5: 🔥 删除 tech 实例
- 调用完全删除 API
- 验证返回状态
- 检查清理的资源列表

### 步骤 6: 验证删除效果
- ✅ 实例列表只剩 2 个（legal, medical）
- ✅ tech_docs 查询返回 404
- ✅ legal_docs 查询仍然正常
- ✅ medical_docs 查询仍然正常

## 📊 测试输出示例

```
=============================================================
[14:30:15] 🧪 开始逻辑隔离模式测试
=============================================================

=============================================================
[14:30:15] 步骤 1: 创建 3 个 RAG 实例
=============================================================
[14:30:16]   创建实例: tech_docs (workspace: tech)
[14:30:16] ✅ 创建实例 tech_docs
[14:30:18]   创建实例: legal_docs (workspace: legal)
[14:30:18] ✅ 创建实例 legal_docs
[14:30:20]   创建实例: medical_docs (workspace: medical)
[14:30:20] ✅ 创建实例 medical_docs

=============================================================
[14:30:22] 步骤 2: 验证实例列表
=============================================================
[14:30:22] ✅ 实例数量正确 (预期: 3, 实际: 3)
[14:30:22] ✅ tech_docs 实例存在
[14:30:22] ✅ legal_docs 实例存在
[14:30:22] ✅ medical_docs 实例存在

...（中间步骤省略）...

=============================================================
[14:31:45] 步骤 6: 验证删除效果
=============================================================
[14:31:45] ✅ 实例数量正确 (预期: 2, 实际: 2)
[14:31:45] ✅ tech_docs 实例已删除
[14:31:45] ✅ legal_docs 实例仍然存在
[14:31:45] ✅ medical_docs 实例仍然存在

  验证 tech_docs 查询失败（预期 404）:
[14:31:46]   查询正确失败: tech_docs (实例不存在)
[14:31:46] ✅ tech_docs 查询正确失败 (404)

  验证其他实例查询仍然正常:
[14:31:48]   查询成功: legal_docs - 返回 512 字符
[14:31:48] ✅ legal_docs 查询仍然正常
[14:31:50]   查询成功: medical_docs - 返回 498 字符
[14:31:50] ✅ medical_docs 查询仍然正常

=============================================================
[14:31:50] 📊 测试总结
=============================================================
[14:31:50] 总测试数: 20
[14:31:50] 通过: 20
[14:31:50] 失败: 0
[14:31:50] 通过率: 100.0%

=============================================================
[14:31:50] 🎉 所有测试通过！逻辑隔离模式工作正常！
=============================================================
```

## 🔍 手动验证数据库

### 检查 Nebula

```bash
# 连接到 NebulaGraph
docker exec -it nebula-graphd /bin/bash
/usr/local/nebula/bin/nebula-console -addr graphd -port 9669 -u root -p nebula

# 查询统一 Space 中的数据
USE xwrag;

# 检查各个 workspace 的节点数量
MATCH (n:entity) WHERE n.workspace == "tech" RETURN count(n);
# 预期: 0 (tech 已删除)

MATCH (n:entity) WHERE n.workspace == "legal" RETURN count(n);
# 预期: > 0 (legal 仍然存在)

MATCH (n:entity) WHERE n.workspace == "medical" RETURN count(n);
# 预期: > 0 (medical 仍然存在)

# 查看所有 workspace 的分布
MATCH (n:entity) RETURN n.workspace, count(n);
```

### 检查 Milvus

```python
from pymilvus import connections, utility

# 连接到 Milvus
connections.connect(host="localhost", port="19530")

# 切换到统一 database
utility.using_database("default")  # 或你配置的 database 名称

# 列出所有 collections
collections = utility.list_collections()

# 检查 workspace 前缀的 collections
tech_colls = [c for c in collections if c.startswith("tech_")]
legal_colls = [c for c in collections if c.startswith("legal_")]
medical_colls = [c for c in collections if c.startswith("medical_")]

print(f"Tech collections: {tech_colls}")      # 预期: []
print(f"Legal collections: {legal_colls}")    # 预期: ['legal_entities', 'legal_chunks', ...]
print(f"Medical collections: {medical_colls}")  # 预期: ['medical_entities', 'medical_chunks', ...]
```

## ⚠️ 注意事项

1. **服务运行**: 确保后端服务已启动并监听在正确的端口
2. **依赖安装**: 需要安装 `requests` 库：`pip install requests`
3. **数据清理**: 测试完成后会询问是否清理测试数据
4. **网络超时**: 如果服务响应慢，可能需要调整脚本中的 timeout 参数

## 🐛 故障排除

### 问题 1: 连接失败
```
错误: Connection refused
解决: 检查后端服务是否运行，端口是否正确
```

### 问题 2: 插入文档超时
```
错误: Timeout waiting for response
解决: 增加等待时间，或检查 LLM 和 Embedding 服务是否正常
```

### 问题 3: 查询返回空结果
```
原因: 索引可能还未完成
解决: 增加插入后的等待时间 (脚本中已设置 10 秒)
```

## 📚 相关文档

- [Nebula 逻辑隔离实现](xwrag/kg/nebula_impl.py)
- [Milvus 逻辑隔离实现](xwrag/kg/milvus_impl.py)
- [App 删除逻辑](app/dependencies_concurrent.py)
- [API 文档](app/internal/admin.py)

## 🎯 测试检查清单

- [ ] 创建 3 个实例成功
- [ ] 实例列表正确（3 个）
- [ ] 插入文档成功
- [ ] 删除前查询正常（3 个实例都能查）
- [ ] 删除 tech 实例成功
- [ ] 删除后实例列表正确（2 个）
- [ ] tech 查询失败（404）
- [ ] legal 查询仍正常
- [ ] medical 查询仍正常
- [ ] Nebula 中 tech 数据为空
- [ ] Milvus 中 tech collections 不存在
- [ ] Nebula 中 legal/medical 数据完整
- [ ] Milvus 中 legal/medical collections 存在
