#!/bin/bash
# 快速创建测试知识库脚本

BASE_URL="http://localhost:8000"

echo "========================================"
echo "创建测试知识库"
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

# 创建知识库 1
echo "创建知识库: test_kb1"
response=$(curl -s -X POST "$BASE_URL/api/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb1",
    "description": "测试知识库1",
    "workspace": "test_kb1",
    "working_dir": "./rag_storage"
  }')

if echo "$response" | grep -q "test_kb1"; then
    echo "✓ test_kb1 创建成功"
else
    if echo "$response" | grep -q "已存在"; then
        echo "⚠ test_kb1 已存在，跳过"
    else
        echo "✗ test_kb1 创建失败"
        echo "$response"
    fi
fi

echo ""

# 创建知识库 2
echo "创建知识库: test_kb2"
response=$(curl -s -X POST "$BASE_URL/api/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_kb2",
    "description": "测试知识库2",
    "workspace": "test_kb2",
    "working_dir": "./rag_storage"
  }')

if echo "$response" | grep -q "test_kb2"; then
    echo "✓ test_kb2 创建成功"
else
    if echo "$response" | grep -q "已存在"; then
        echo "⚠ test_kb2 已存在，跳过"
    else
        echo "✗ test_kb2 创建失败"
        echo "$response"
    fi
fi

echo ""
echo "========================================"
echo "测试知识库创建完成"
echo "========================================"
echo ""
echo "知识库列表:"
echo "  - test_kb1 (workspace: test_kb1)"
echo "  - test_kb2 (workspace: test_kb2)"
echo ""
echo "下一步:"
echo "  1. 为知识库插入测试文档（可选）"
echo "  2. 运行测试: ./run_multi_kb_query_test.sh"
echo ""
