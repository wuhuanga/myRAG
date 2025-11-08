# 删除实例逻辑分析

## 当前实现

### 删除逻辑
```python
def delete_instance(self, rag_id: str) -> bool:
    if rag_id in self.instances:
        processor = self.instances[rag_id]

        # 获取工作目录路径
        working_dir = processor.working_dir

        # 删除整个 working_dir
        shutil.rmtree(working_dir)
```

### 创建逻辑
```python
# 所有实例使用相同的 working_dir
payload = {
    "rag_id": "satellite_project",
    "workspace": "satellite_project_workspace",
    "working_dir": "./rag_storage"  # ← 共享的 working_dir
}
```

## ⚠️ 潜在问题

### 场景说明

**创建两个实例**：
```python
实例1:
  rag_id: "satellite_project"
  working_dir: "./rag_storage"
  workspace: "satellite_project_workspace"

实例2:
  rag_id: "tender_docs"
  working_dir: "./rag_storage"
  workspace: "tender_docs_workspace"
```

**问题**：
```python
# 删除实例1
DELETE /api/admin/rag_instances/satellite_project

# 实际删除的是：
shutil.rmtree("./rag_storage")  # ← 删除整个目录！

# 结果：
❌ 实例2的数据也被删除了！
❌ 所有共享 ./rag_storage 的实例数据都没了！
```

## 🔍 xwrag 内部如何使用 workspace？

根据 xwrag 的设计，workspace 参数用于：

1. **数据隔离**：不同 workspace 的数据存储在不同位置
2. **目录结构**：
   ```
   working_dir/
   └── {workspace}/          ← xwrag 内部创建
       ├── faiss_index/
       ├── neo4j/
       ├── kv_storage/
       └── ...
   ```

或者（取决于 xwrag 的具体实现）：
```
working_dir/
├── faiss_{workspace}/
├── neo4j_{workspace}/
├── kv_{workspace}/
└── ...
```

## ✅ 正确的解决方案

### 方案1：修改创建逻辑（推荐）

**让每个实例有独立的 working_dir**：

```python
# 修改创建逻辑
payload = {
    "rag_id": "satellite_project",
    "workspace": "satellite_project_workspace",
    "working_dir": f"./rag_storage/{workspace}"  # ← 独立目录
}

# 目录结构：
./rag_storage/
├── satellite_project_workspace/   ← 实例1的完整目录
│   ├── faiss_index/
│   ├── neo4j/
│   └── ...
└── tender_docs_workspace/         ← 实例2的完整目录
    ├── faiss_index/
    ├── neo4j/
    └── ...

# 删除时：
shutil.rmtree("./rag_storage/satellite_project_workspace")  # ✅ 只删除实例1
```

**优点**：
- ✅ 完全隔离，安全可靠
- ✅ 删除逻辑简单（直接删除 working_dir）
- ✅ 目录结构清晰
- ✅ 无需修改删除逻辑

**缺点**：
- ⚠️ 需要修改创建逻辑
- ⚠️ 与现有测试代码不兼容（需要更新）

### 方案2：修改删除逻辑

**删除 workspace 子目录而不是整个 working_dir**：

```python
def delete_instance(self, rag_id: str) -> bool:
    if rag_id in self.instances:
        processor = self.instances[rag_id]

        # 构建 workspace 目录路径
        workspace_dir = processor.working_dir / processor.workspace

        # 只删除 workspace 子目录
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)
```

**问题**：
- ❓ 依赖于 xwrag 的内部实现（workspace 是否作为子目录）
- ❓ 如果 xwrag 使用前缀命名（如 faiss_{workspace}），此方案无效
- ❓ 可能无法完全清理所有数据

### 方案3：查询 xwrag 的实际存储路径

**通过 xwrag 获取数据存储路径**：

```python
def delete_instance(self, rag_id: str) -> bool:
    if rag_id in self.instances:
        processor = self.instances[rag_id]

        # 假设 xwrag 提供了获取数据路径的方法
        data_paths = processor.rag.get_data_paths()

        # 删除所有数据文件/目录
        for path in data_paths:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
```

**问题**：
- ❓ xwrag 可能不提供这样的API
- ❓ 实现复杂

## 🎯 推荐方案

### 采用方案1：独立 working_dir

**原因**：
1. **最安全**：完全避免误删其他实例数据
2. **最清晰**：每个实例有自己的完整目录
3. **最简单**：删除逻辑保持不变

**实施步骤**：

1. **修改 RAGInstanceManager.create_instance**：
   ```python
   # 自动为每个实例创建独立的 working_dir
   working_dir = Path(config.working_dir) / config.workspace

   processor = xwragProcessor(
       working_dir=str(working_dir),  # 使用独立目录
       workspace=config.workspace,
       ...
   )
   ```

2. **更新默认配置**：
   ```python
   # models.py 中的默认值
   class RAGInstanceCreate(BaseModel):
       working_dir: str = "./rag_storage"  # 基础目录
       # 实际使用时会自动拼接 workspace
   ```

3. **测试验证**：
   ```bash
   # 创建实例1
   POST /api/admin/rag_instances/create
   {
     "rag_id": "test1",
     "workspace": "ws1",
     "working_dir": "./rag_storage"
   }
   # 实际创建：./rag_storage/ws1/

   # 创建实例2
   POST /api/admin/rag_instances/create
   {
     "rag_id": "test2",
     "workspace": "ws2",
     "working_dir": "./rag_storage"
   }
   # 实际创建：./rag_storage/ws2/

   # 删除实例1
   DELETE /api/admin/rag_instances/test1
   # 只删除：./rag_storage/ws1/
   # 保留：./rag_storage/ws2/  ✅
   ```

## 📊 当前状态评估

**严重程度**：🔴 **高**

**影响**：
- 在多实例共享 working_dir 的情况下，删除一个实例会**误删所有实例的数据**
- 并发测试中可能出现此问题（如果实例没有及时清理）

**紧急性**：
- 测试环境：🟡 中（测试脚本在每次测试前都会删除所有实例）
- 生产环境：🔴 高（如果用户创建多个实例并删除其中一个）

## 🔧 临时缓解措施

在实施完整方案之前：

1. **文档警告**：
   ```
   ⚠️ 注意：当前版本中，删除实例会删除整个 working_dir。
   如果多个实例共享同一 working_dir，删除任一实例会影响所有实例。
   建议：为每个实例使用不同的 working_dir。
   ```

2. **创建时使用唯一 working_dir**：
   ```python
   # 用户手动指定
   {
     "rag_id": "instance1",
     "workspace": "ws1",
     "working_dir": "./rag_storage/instance1"  # ← 唯一路径
   }
   ```

3. **验证检查**：
   ```python
   # 删除前检查是否有其他实例使用相同 working_dir
   def delete_instance(self, rag_id: str) -> bool:
       processor = self.instances[rag_id]
       working_dir = processor.working_dir

       # 检查是否有其他实例使用相同目录
       for other_id, other_proc in self.instances.items():
           if other_id != rag_id and other_proc.working_dir == working_dir:
               raise ValueError(
                   f"无法删除：实例 '{other_id}' 使用相同的 working_dir。"
                   f"删除会影响其他实例的数据。"
               )

       # 安全删除
       del self.instances[rag_id]
       shutil.rmtree(working_dir)
       return True
   ```

## 下一步行动

1. [ ] 确认 xwrag 内部如何使用 workspace 参数
2. [ ] 实施方案1（独立 working_dir）
3. [ ] 更新所有测试脚本
4. [ ] 更新文档和示例
5. [ ] 添加单元测试验证删除逻辑
