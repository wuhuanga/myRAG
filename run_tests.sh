#!/bin/bash
# RAG 后端 API 测试运行脚本

echo "=================================="
echo "RAG 后端 API 测试"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端是否运行
echo "检查后端服务..."
if curl -s http://localhost:8000/api/admin/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务正在运行${NC}"
else
    echo -e "${RED}✗ 后端服务未运行${NC}"
    echo ""
    echo "请先启动后端服务："
    echo "  ./start_backend.sh"
    echo ""
    echo "或者："
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    exit 1
fi

echo ""
echo "选择测试类型："
echo "  1) 快速测试 (推荐，约1-2分钟)"
echo "  2) 全面测试 (完整测试，约5-10分钟)"
echo "  3) 退出"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}运行快速测试...${NC}"
        echo ""
        python3 test_quick.py
        ;;
    2)
        echo ""
        echo -e "${GREEN}运行全面测试...${NC}"
        echo ""
        python3 test_backend_api.py
        ;;
    3)
        echo "退出"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo "测试完成"
echo "=================================="
