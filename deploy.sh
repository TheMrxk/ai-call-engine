#!/bin/bash

# ============================================================
# Bank AI Call Engine - 一键部署脚本
# ============================================================
# 用途：快速部署 AI 通话引擎
# 系统要求：Ubuntu 20.04+, Debian 11+, CentOS 8+
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以 root 运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查系统
check_system() {
    log_info "检查系统..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        log_info "检测到系统：$OS $VERSION_ID"
    else
        log_error "无法识别操作系统"
        exit 1
    fi
}

# 安装 Docker
install_docker() {
    log_info "检查 Docker 是否已安装..."

    if command -v docker &> /dev/null; then
        log_success "Docker 已安装：$(docker --version)"
        return
    fi

    log_info "正在安装 Docker..."

    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        centos|rhel|fedora)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            log_error "不支持的系统：$OS"
            exit 1
            ;;
    esac

    log_success "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    log_info "检查 Docker Compose 是否已安装..."

    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
        log_success "Docker Compose 已安装"
        return
    fi

    log_info "正在安装 Docker Compose..."

    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    log_success "Docker Compose 安装完成"
}

# 配置环境变量
setup_env() {
    log_info "配置环境变量..."

    if [ -f ".env" ]; then
        log_warning ".env 文件已存在，跳过配置"
        read -p "是否要重新配置？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    # 复制模板
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "已创建 .env 文件"
    fi

    # 引导用户配置
    echo ""
    log_info "请配置以下必要的 API Key："
    echo ""

    # 配置 LLM API Key
    read -p "请输入阿里云百炼 API Key (LLM_API_KEY): " llm_key
    if [ -n "$llm_key" ]; then
        sed -i "s/LLM_API_KEY=.*/LLM_API_KEY=$llm_key/" .env
    fi

    # 配置 TTS Token
    read -p "请输入火山引擎访问令牌 (DOUBAO_ACCESS_TOKEN): " doubao_token
    if [ -n "$doubao_token" ]; then
        sed -i "s/DOUBAO_ACCESS_TOKEN=.*/DOUBAO_ACCESS_TOKEN=$doubao_token/" .env
    fi

    log_success "环境变量配置完成"
}

# 创建日志目录
setup_directories() {
    log_info "创建必要的目录..."

    mkdir -p logs tts_cache ssl

    log_success "目录创建完成"
}

# 启动服务
start_services() {
    log_info "启动 AI 通话引擎..."

    docker-compose -f docker-compose.ai-engine.yml up -d --build

    log_success "服务启动完成"
}

# 验证服务
verify_service() {
    log_info "等待服务启动..."
    sleep 10

    log_info "验证服务状态..."

    # 检查容器状态
    if docker ps | grep -q ai-call-engine; then
        log_success "AI 通话引擎容器运行正常"
    else
        log_error "AI 通话引擎容器未运行"
        docker-compose -f docker-compose.ai-engine.yml logs
        exit 1
    fi

    # 健康检查
    if curl -s http://localhost:5001/api/health | grep -q '"status":"ok"'; then
        log_success "健康检查通过"
    else
        log_warning "健康检查失败，请稍后手动检查：curl http://localhost:5001/api/health"
    fi
}

# 显示完成信息
show_complete() {
    echo ""
    echo "============================================================"
    log_success "Bank AI Call Engine 部署完成！"
    echo "============================================================"
    echo ""
    echo "服务地址：http://localhost:5001"
    echo "健康检查：curl http://localhost:5001/api/health"
    echo "查看日志：docker-compose logs -f ai-call-engine"
    echo "停止服务：docker-compose down"
    echo ""
    echo "API 文档：请参阅 AI_CALL_ENGINE_API.md"
    echo "============================================================"
}

# 主函数
main() {
    echo ""
    echo "============================================================"
    echo "  Bank AI Call Engine - 一键部署脚本"
    echo "============================================================"
    echo ""

    check_root
    check_system
    install_docker
    install_docker_compose
    setup_directories
    setup_env
    start_services
    verify_service
    show_complete
}

# 运行主函数
main
