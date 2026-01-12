#!/bin/bash
# 为测试知识库插入测试数据

BASE_URL="http://localhost:8000"

echo "========================================"
echo "为测试知识库插入数据"
echo "========================================"
echo ""

# 检查服务器是否运行
echo "检查服务器状态..."
if ! curl -s --max-time 5 $BASE_URL/docs > /dev/null 2>&1; then
    echo "✗ 服务器未运行！"
    echo "请先启动服务器: python app/main.py"
    exit 1
fi
echo "✓ 服务器正常运行"
echo ""

# 检查测试文档是否存在
if [ ! -f "test_doc1.txt" ] || [ ! -f "test_doc2.txt" ]; then
    echo "✗ 测试文档不存在！"
    echo "请确保 test_doc1.txt 和 test_doc2.txt 存在"
    exit 1
fi

# 插入文档到 test_kb1
echo "正在向 test_kb1 插入文档..."
response=$(curl -s -X POST "$BASE_URL/api/documents/upload" \
  -F "rag_id=test_kb1" \
  -F "file=@test_doc1.txt")

if echo "$response" | grep -q "success\|成功"; then
    echo "✓ test_kb1: test_doc1.txt 插入成功"
else
    echo "✗ test_kb1: test_doc1.txt 插入失败"
    echo "$response"
fi

echo ""

# 插入文档到 test_kb2
echo "正在向 test_kb2 插入文档..."
response=$(curl -s -X POST "$BASE_URL/api/documents/upload" \
  -F "rag_id=test_kb2" \
  -F "file=@test_doc2.txt")

if echo "$response" | grep -q "success\|成功"; then
    echo "✓ test_kb2: test_doc2.txt 插入成功"
else
    echo "✗ test_kb2: test_doc2.txt 插入失败"
    echo "$response"
fi

echo ""
echo "========================================"
echo "数据插入完成"
echo "========================================"
echo ""
echo "插入的文档:"
echo "  - test_kb1: test_doc1.txt (RAG 技术介绍)"
echo "  - test_kb2: test_doc2.txt (向量数据库详解)"
echo ""
echo "等待几秒让文档处理完成，然后运行测试:"
echo "  ./run_multi_kb_query_test.sh"
echo ""
