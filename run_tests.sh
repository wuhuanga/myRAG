#!/bin/bash
# 在 conda lightrag 环境中运行 pytest

# 激活 conda 环境
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lightrag

# 确保安装了测试依赖
echo "检查测试依赖..."
pip install -q pytest pytest-asyncio requests 2>/dev/null || true

# 运行 pytest
echo "运行测试..."
python -m pytest "$@"
