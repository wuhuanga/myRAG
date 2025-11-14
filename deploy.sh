#!/bin/bash

# RAG Docker 部署管理脚本
# 使用方法: ./deploy.sh [命令]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数定义
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查 Docker 和 Docker Compose
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "Docker 和 Docker Compose 已安装"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env 文件不存在，正在从 .env.example 复制..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_info "请编辑 .env 文件并填入真实的配置信息，特别是 LITELLM_KEY 和 NEO4J_PASSWORD"
        echo ""
        print_warning "编辑 .env 文件："
        print_warning "  LITELLM_KEY=sk-your-actual-key"
        print_warning "  NEO4J_PASSWORD=your-secure-password"
        return 1
    fi
    print_success ".env 文件已存在"
    return 0
}

# 构建镜像
build() {
    print_info "开始构建 Docker 镜像..."
    docker-compose build
    print_success "镜像构建完成"
}

# 启动服务
start() {
    if ! check_env_file; then
        exit 1
    fi
    
    print_info "启动服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_success "服务已启动"
        print_info "FastAPI 文档: http://localhost:8000/docs"
        print_info "Neo4j 控制台: http://localhost:7474"
    else
        print_error "服务启动失败，查看日志:"
        docker-compose logs
        return 1
    fi
}

# 停止服务
stop() {
    print_info "停止服务..."
    docker-compose stop
    print_success "服务已停止"
}

# 重启服务
restart() {
    print_info "重启服务..."
    docker-compose restart
    print_success "服务已重启"
}

# 查看日志
logs() {
    SERVICE="${1:-rag-api}"
    print_info "显示 $SERVICE 的实时日志 (Ctrl+C 退出)..."
    docker-compose logs -f "$SERVICE"
}

# 查看状态
status() {
    print_info "容器状态："
    docker-compose ps
    echo ""
    print_info "容器详情："
    docker-compose ps -a
}

# 进入容器
exec_container() {
    SERVICE="${1:-rag-api}"
    COMMAND="${2:-bash}"
    print_info "进入 $SERVICE 容器..."
    docker-compose exec "$SERVICE" $COMMAND
}

# 清理资源
clean() {
    print_warning "即将删除所有容器和关联的卷..."
    read -p "确认删除？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "清理资源..."
        docker-compose down -v
        print_success "资源已清理"
    else
        print_info "取消清理"
    fi
}

# 完整重建
rebuild() {
    print_warning "即将完整重建（删除镜像和容器）..."
    read -p "确认重建？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "停止服务..."
        docker-compose down
        
        print_info "删除旧镜像..."
        docker-compose build --no-cache
        
        print_info "重新启动..."
        start
    else
        print_info "取消重建"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
${GREEN}RAG Docker 部署管理脚本${NC}

使用方法: ./deploy.sh [命令]

可用命令:
    ${BLUE}build${NC}       - 构建 Docker 镜像
    ${BLUE}start${NC}       - 启动服务（首次使用或停止后）
    ${BLUE}stop${NC}        - 停止服务
    ${BLUE}restart${NC}     - 重启服务
    ${BLUE}status${NC}      - 查看容器状态
    ${BLUE}logs${NC}        - 查看 API 服务日志 (实时)
    ${BLUE}logs neo4j${NC}  - 查看 Neo4j 日志 (实时)
    ${BLUE}exec${NC}        - 进入 API 容器执行命令
    ${BLUE}exec bash${NC}   - 进入 API 容器交互 shell
    ${BLUE}clean${NC}       - 清理所有容器和卷（谨慎！会删除数据）
    ${BLUE}rebuild${NC}     - 完整重建（删除镜像和容器）
    ${BLUE}help${NC}        - 显示此帮助信息

示例:
    ./deploy.sh start          # 启动服务
    ./deploy.sh logs           # 查看 API 日志
    ./deploy.sh exec bash      # 进入容器
    ./deploy.sh restart        # 重启所有服务

更多信息请参考 DOCKER_DEPLOYMENT_GUIDE.md
EOF
}

# 主逻辑
COMMAND="${1:-help}"

case "$COMMAND" in
    build)
        check_prerequisites
        build
        ;;
    start)
        check_prerequisites
        start
        ;;
    stop)
        check_prerequisites
        stop
        ;;
    restart)
        check_prerequisites
        restart
        ;;
    status)
        check_prerequisites
        status
        ;;
    logs)
        check_prerequisites
        logs "$2"
        ;;
    exec)
        check_prerequisites
        exec_container "$2" "$3"
        ;;
    clean)
        check_prerequisites
        clean
        ;;
    rebuild)
        check_prerequisites
        rebuild
        ;;
    help)
        show_help
        ;;
    *)
        print_error "未知命令: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
