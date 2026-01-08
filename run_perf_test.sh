#!/bin/bash
# 性能测试运行脚本

set -e

echo "========================================"
echo "  RAG 系统性能测试"
echo "========================================"
echo ""

# 激活 conda 环境
if [ -f ~/miniforge3/etc/profile.d/conda.sh ]; then
    source ~/miniforge3/etc/profile.d/conda.sh
    conda activate lightrag
elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
    conda activate lightrag
fi

# 检查服务器
echo "检查 FastAPI 服务器状态..."
if curl -s --max-time 5 http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✓ FastAPI 服务器正在运行"
else
    echo ""
    echo "❌ 错误：FastAPI 服务器未运行！"
    echo ""
    echo "请先启动服务器："
    echo "  python -m xwrag.api.xwrag_server"
    echo ""
    exit 1
fi

echo ""
echo "开始性能测试..."
echo ""

# 运行性能测试
python test_performance.py

echo ""
echo "性能测试完成"
