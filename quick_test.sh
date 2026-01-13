#!/bin/bash
# 多知识库查询接口快速测试脚本

echo "========================================"
echo "多知识库查询接口快速测试"
echo "========================================"
echo ""

BASE_URL="http://localhost:8000"

# 1. 检查服务器
echo "步骤 1: 检查服务器状态..."
if ! curl -s --max-time 5 $BASE_URL/docs > /dev/null 2>&1; then
    echo "✗ 服务器未运行！"
    echo ""
    echo "请先启动服务器："
    echo "  python app/main.py"
    echo ""
    echo "或者在后台运行："
    echo "  nohup python app/main.py > server.log 2>&1 &"
    echo ""
    exit 1
fi
echo "✓ 服务器正常运行"
echo ""

# 2. 创建测试知识库
echo "步骤 2: 创建测试知识库..."
echo ""

echo "创建 test_kb1..."
response=$(curl -s -X POST "$BASE_URL/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb1",
    "description": "测试知识库1",
    "workspace": "test_kb1",
    "working_dir": "./rag_storage"
  }')

if echo "$response" | grep -qi "success\|已存在\|创建成功"; then
    echo "✓ test_kb1 创建成功（或已存在）"
else
    echo "⚠ test_kb1 响应: $response"
fi

echo "创建 test_kb2..."
response=$(curl -s -X POST "$BASE_URL/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb2",
    "description": "测试知识库2",
    "workspace": "test_kb2",
    "working_dir": "./rag_storage"
  }')

if echo "$response" | grep -qi "success\|已存在\|创建成功"; then
    echo "✓ test_kb2 创建成功（或已存在）"
else
    echo "⚠ test_kb2 响应: $response"
fi

echo ""

# 3. 插入测试数据
echo "步骤 3: 插入测试数据..."
echo ""

if [ ! -f "test_doc1.txt" ] || [ ! -f "test_doc2.txt" ]; then
    echo "✗ 测试文档不存在！"
    exit 1
fi

echo "向 test_kb1 插入文档..."
response=$(curl -s -X POST "$BASE_URL/api/documents/upload" \
  -F "rag_id=test_kb1" \
  -F "file=@test_doc1.txt")

if echo "$response" | grep -qi "success\|成功"; then
    echo "✓ test_kb1: test_doc1.txt 插入成功"
else
    echo "⚠ 响应: $response"
fi

echo "向 test_kb2 插入文档..."
response=$(curl -s -X POST "$BASE_URL/api/documents/upload" \
  -F "rag_id=test_kb2" \
  -F "file=@test_doc2.txt")

if echo "$response" | grep -qi "success\|成功"; then
    echo "✓ test_kb2: test_doc2.txt 插入成功"
else
    echo "⚠ 响应: $response"
fi

echo ""

# 4. 等待处理
echo "步骤 4: 等待文档处理..."
echo "文档需要时间进行向量化和知识图谱提取，请等待 10-30 秒..."
echo ""
for i in {10..1}; do
    echo -ne "等待中... $i 秒\r"
    sleep 1
done
echo "等待完成！        "
echo ""

# 5. 运行测试
echo "步骤 5: 运行测试..."
echo ""

if [ -f "run_multi_kb_query_test.sh" ]; then
    ./run_multi_kb_query_test.sh
else
    python tests/test_multi_kb_query.py
fi
