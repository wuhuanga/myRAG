#!/bin/bash
# 多知识库图谱查询接口测试运行脚本

echo "========================================"
echo "多知识库图谱查询接口测试"
echo "========================================"
echo ""

# 激活 conda 环境（如果需要）
if [ -f ~/miniforge3/etc/profile.d/conda.sh ]; then
    source ~/miniforge3/etc/profile.d/conda.sh
    conda activate lightrag
    echo "✓ Conda 环境已激活: lightrag"
fi

# 检查服务器是否运行
echo "检查服务器状态..."
if ! curl -s --max-time 5 http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✗ 服务器未运行！"
    echo "请先启动服务器: python app/main.py"
    exit 1
fi
echo "✓ 服务器正常运行"
echo ""

# 运行测试
echo "开始运行测试..."
echo "========================================"
python -m pytest tests/test_multi_kb_graph.py -v -s

# 输出测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✓ 所有测试通过"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "✗ 部分测试失败"
    echo "========================================"
    exit 1
fi
