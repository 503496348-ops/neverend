#!/usr/bin/env bash
#
# 无限循环 Neverend — 安装脚本
# 支持两种模式：
#   1. 交互式: curl -fsSL .../install.sh | bash
#   2. 无交互: curl -fsSL .../install.sh | bash -s -- --domain example.com --password xxx
#

set -e

# ── 参数解析 ──
DOMAIN=""
PORT=""
COUCHDB_PASSWORD=""
NEVEREND_PASSWORD=""
E2EE_PASSPHRASE=""
NON_INTERACTIVE=false
INSTALL_DIR="$HOME/neverend"

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)       DOMAIN="$2"; NON_INTERACTIVE=true; shift 2 ;;
        --port)         PORT="$2"; shift 2 ;;
        --password)     COUCHDB_PASSWORD="$2"; NON_INTERACTIVE=true; shift 2 ;;
        --sync-password) NEVEREND_PASSWORD="$2"; shift 2 ;;
        --e2ee)         E2EE_PASSPHRASE="$2"; shift 2 ;;
        --dir)          INSTALL_DIR="$2"; shift 2 ;;
        --auto)         NON_INTERACTIVE=true; shift ;;
        -h|--help)
            echo "用法: install.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --domain DOMAIN        域名（默认 localhost）"
            echo "  --port PORT            公网端口（默认 80，80/443 被占用时用 18080）"
            echo "  --password PASSWORD    CouchDB 管理员密码（默认自动生成）"
            echo "  --sync-password PASS   同步用户密码（默认自动生成）"
            echo "  --e2ee PASSPHRASE      端到端加密口令（默认自动生成）"
            echo "  --dir PATH             安装目录（默认 ~/neverend）"
            echo "  --auto                 全自动模式，所有参数使用默认值"
            echo ""
            echo "示例:"
            echo "  # 交互式安装"
            echo "  curl -fsSL .../install.sh | bash"
            echo ""
            echo "  # 无交互安装（智能体/脚本用）"
            echo "  curl -fsSL .../install.sh | bash -s -- --domain notes.example.com --auto"
            echo ""
            echo "  # 无域名，使用 IP:端口"
            echo "  curl -fsSL .../install.sh | bash -s -- --port 18080 --auto"
            exit 0
            ;;
        *) shift ;;
    esac
done

# ── 颜色 ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${BLUE}ℹ️  $*${NC}"; }
ok()    { echo -e "${GREEN}✅ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail()  { echo -e "${RED}❌ $*${NC}"; exit 1; }

banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   🔄 无限循环 Neverend — 安装           ║${NC}"
    echo -e "${CYAN}║   Obsidian 免费跨设备同步                ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

gen_password() {
    openssl rand -base64 16 2>/dev/null | tr -d '/+=' | head -c 16 || head -c 16 < /dev/urandom | base64 | tr -d '/+=' | head -c 16
}

gen_passphrase() {
    local adjectives=("autumn" "hidden" "bitter" "misty" "silent" "empty" "dark" "summer" "icy" "quiet" "white" "cool" "spring" "patient" "twilight" "dawn" "crimson" "blue" "frosty" "green" "bold" "wild" "ancient" "purple" "lively")
    local nouns=("waterfall" "river" "breeze" "moon" "rain" "wind" "sea" "snow" "lake" "sunset" "pine" "shadow" "leaf" "dawn" "forest" "hill" "cloud" "meadow" "sun" "bird" "field" "fire" "flower" "mountain" "night" "star" "sky" "wave" "dream" "tree")
    echo "${adjectives[$RANDOM % ${#adjectives[@]}]}-${nouns[$RANDOM % ${#nouns[@]}]}"
}

# ── Banner ──
banner

# ── Step 1: Docker ──
info "检查 Docker..."
if ! command -v docker &> /dev/null; then
    if [[ "$NON_INTERACTIVE" == "true" ]]; then
        fail "Docker 未安装。请先安装 Docker: https://docs.docker.com/get-docker/"
    fi
    warn "Docker 未安装，正在自动安装..."
    curl -fsSL https://get.docker.com | sh
    ok "Docker 安装完成"
fi
ok "Docker: $(docker --version | head -1)"

if ! docker compose version &> /dev/null; then
    fail "Docker Compose 不可用，请升级 Docker"
fi
ok "Docker Compose 可用"

# ── Step 2: 配置 ──
DOMAIN=${DOMAIN:-localhost}
PORT=${PORT:-80}
COUCHDB_USER="admin"
COUCHDB_PASSWORD=${COUCHDB_PASSWORD:-$(gen_password)}
NEVEREND_USER="obsidian"
NEVEREND_PASSWORD=${NEVEREND_PASSWORD:-$(gen_password)}

if [[ -z "$E2EE_PASSPHRASE" ]]; then
    E2EE_PASSPHRASE=$(gen_passphrase)
fi

if [[ "$NON_INTERACTIVE" != "true" ]]; then
    # 交互式确认
    echo ""
    echo -e "${CYAN}── 配置确认 ──${NC}"
    echo "  域名:     $DOMAIN"
    echo "  管理员:   $COUCHDB_USER / $COUCHDB_PASSWORD"
    echo "  同步用户: $NEVEREND_USER / $NEVEREND_PASSWORD"
    echo "  加密口令: $E2EE_PASSPHRASE"
    echo ""
    read -p "  确认启动？(Y/n) [Y]: " confirm
    if [[ "$confirm" =~ ^[Nn] ]]; then
        info "已取消"
        exit 0
    fi
fi

# ── Step 3: 克隆/更新 ──
if [ -d "$INSTALL_DIR" ]; then
    info "更新 $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull --quiet 2>/dev/null || true
else
    info "克隆到 $INSTALL_DIR..."
    git clone --depth 1 https://github.com/503496348-ops/neverend.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
ok "仓库就绪"

# ── Step 4: 生成 .env ──
cat > .env << EOF
# Neverend 配置 — 自动生成
DOMAIN=$DOMAIN
NEVEREND_PORT=$PORT
COUCHDB_USER=$COUCHDB_USER
COUCHDB_PASSWORD=$COUCHDB_PASSWORD
COUCHDB_DBNAME=obsidian-livesync
E2EE_PASSPHRASE=$E2EE_PASSPHRASE
NEVEREND_USER=$NEVEREND_USER
NEVEREND_PASSWORD=$NEVEREND_PASSWORD
EOF
ok "配置已写入 .env"

# ── Step 5: 启动 ──
info "启动服务..."
docker compose up -d

info "等待初始化（最多 120 秒）..."
for i in $(seq 1 60); do
    if docker logs neverend-init 2>&1 | grep -q "部署完成"; then
        break
    fi
    sleep 2
done

# ── Step 6: 提取结果 ──
SETUP_URI=$(docker logs neverend-init 2>&1 | grep "obsidian://setuplivesync" | head -1 || true)
URI_PASS=$(docker logs neverend-init 2>&1 | grep "Setup URI 口令" | sed 's/.*：//' || true)
E2EE_PASS=$(docker logs neverend-init 2>&1 | grep "端到端加密口令" | sed 's/.*：//' || true)

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🔄 Neverend 安装完成！                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$SETUP_URI" ]; then
    echo -e "${CYAN}📋 Obsidian 配置步骤:${NC}"
    echo "  1. 安装插件 \"Self-hosted LiveSync\""
    echo "  2. 命令面板 → \"Use the copied setup URI\""
    echo "  3. 粘贴下方 URI → 输入口令"
    echo ""
    echo -e "${YELLOW}🔗 Setup URI:${NC}"
    echo "$SETUP_URI"
    echo ""
    echo -e "${YELLOW}🔑 口令:${NC} $URI_PASS"
    [ -n "$E2EE_PASS" ] && echo -e "${YELLOW}🔐 加密口令:${NC} $E2EE_PASS"
else
    warn "Setup URI 未生成，请查看日志: docker logs neverend-init"
fi

echo ""
echo -e "${CYAN}📝 账号:${NC} $COUCHDB_USER / $COUCHDB_PASSWORD"
echo -e "${CYAN}📁 目录:${NC} $INSTALL_DIR"
echo ""

# ── 输出结构化数据（供智能体解析）──
if [[ "$NON_INTERACTIVE" == "true" ]]; then
    echo "---NEVEREND_OUTPUT_START---"
    echo "DOMAIN=$DOMAIN"
    echo "PORT=$PORT"
    echo "SETUP_URI=$SETUP_URI"
    echo "URI_PASSPHRASE=$URI_PASS"
    echo "E2EE_PASSPHRASE=$E2EE_PASS"
    echo "COUCHDB_USER=$COUCHDB_USER"
    echo "COUCHDB_PASSWORD=$COUCHDB_PASSWORD"
    echo "NEVEREND_USER=$NEVEREND_USER"
    echo "NEVEREND_PASSWORD=$NEVEREND_PASSWORD"
    echo "INSTALL_DIR=$INSTALL_DIR"
    echo "---NEVEREND_OUTPUT_END---"
fi
