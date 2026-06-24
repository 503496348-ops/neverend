#!/usr/bin/env bash
#
# 无限循环 Neverend — 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash
#
# 自动完成：
# 1. 安装 Docker（如果没有）
# 2. 配置 .env
# 3. 启动服务
# 4. 输出 Setup URI
#

set -e

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── 工具函数 ──
info()  { echo -e "${BLUE}ℹ️  $*${NC}"; }
ok()    { echo -e "${GREEN}✅ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail()  { echo -e "${RED}❌ $*${NC}"; exit 1; }

banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   🔄 无限循环 Neverend — 一键安装       ║${NC}"
    echo -e "${CYAN}║   Obsidian 免费跨设备同步                ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 生成随机密码 ──
gen_password() {
    openssl rand -base64 16 2>/dev/null | tr -d '/+=' | head -c 16
}

# ── 生成友好口令 ──
gen_passphrase() {
    local adjectives=("autumn" "hidden" "bitter" "misty" "silent" "empty" "dark" "summer" "icy" "quiet" "white" "cool" "spring" "patient" "twilight" "dawn" "crimson" "blue" "broken" "cold" "frosty" "green" "bold" "little" "morning" "wild" "ancient" "purple" "lively" "nameless")
    local nouns=("waterfall" "river" "breeze" "moon" "rain" "wind" "sea" "morning" "snow" "lake" "sunset" "pine" "shadow" "leaf" "dawn" "glitter" "forest" "hill" "cloud" "meadow" "sun" "bird" "brook" "butterfly" "bush" "dew" "field" "fire" "flower" "grass" "haze" "mountain" "night" "pond" "star" "sky" "wave" "dream" "cherry" "tree" "fog" "voice")
    local adj=${adjectives[$RANDOM % ${#adjectives[@]}]}
    local noun=${nouns[$RANDOM % ${#nouns[@]}]}
    echo "${adj}-${noun}"
}

# ── Step 0: Banner ──
banner

# ── Step 1: 检查/安装 Docker ──
info "检查 Docker 环境..."

if command -v docker &> /dev/null; then
    ok "Docker 已安装: $(docker --version | head -1)"
else
    warn "Docker 未安装，正在自动安装..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux 自动安装
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        ok "Docker 安装完成"
        warn "你可能需要重新登录才能使用 docker（或用 sudo）"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        fail "macOS 请先安装 Docker Desktop: https://docker.com/products/docker-desktop"
    else
        fail "请先手动安装 Docker: https://docs.docker.com/get-docker/"
    fi
fi

# 检查 docker compose
if docker compose version &> /dev/null; then
    ok "Docker Compose 可用"
else
    fail "Docker Compose 不可用。请升级 Docker 到最新版本。"
fi

# ── Step 2: 克隆仓库 ──
INSTALL_DIR="$HOME/neverend"

if [ -d "$INSTALL_DIR" ]; then
    warn "目录 $INSTALL_DIR 已存在，正在更新..."
    cd "$INSTALL_DIR"
    git pull --quiet 2>/dev/null || true
else
    info "正在下载 Neverend..."
    git clone --depth 1 https://github.com/503496348-ops/neverend.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    ok "下载完成: $INSTALL_DIR"
fi

# ── Step 3: 交互式配置 ──
echo ""
info "开始配置（直接回车使用默认值）"
echo ""

# 域名
echo -e "${CYAN}── 域名配置 ──${NC}"
echo "  手机访问需要域名 + 公网 IP"
echo "  仅桌面/内网使用直接回车"
read -p "  域名 [localhost]: " DOMAIN
DOMAIN=${DOMAIN:-localhost}

# 管理员密码
COUCHDB_USER="admin"
COUCHDB_PASSWORD=$(gen_password)
echo ""
echo -e "${CYAN}── 数据库账号 ──${NC}"
echo "  管理员: $COUCHDB_USER"
echo "  密码:   $COUCHDB_PASSWORD"
echo ""
read -p "  使用此密码？(Y/n) [Y]: " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
    read -p "  自定义密码: " COUCHDB_PASSWORD
fi

# 同步用户
NEVEREND_USER="obsidian"
NEVEREND_PASSWORD=$(gen_password)
echo ""
echo -e "${CYAN}── 同步账号 ──${NC}"
echo "  用户名: $NEVEREND_USER"
echo "  密码:   $NEVEREND_PASSWORD"
echo ""
read -p "  使用此账号？(Y/n) [Y]: " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
    read -p "  自定义用户名: " NEVEREND_USER
    read -p "  自定义密码: " NEVEREND_PASSWORD
fi

# E2E 加密
E2EE_PASSPHRASE=$(gen_passphrase)
echo ""
echo -e "${CYAN}── 端到端加密 ──${NC}"
echo "  启用后笔记在传输过程中全程加密"
echo "  加密口令: $E2EE_PASSPHRASE"
echo ""
read -p "  启用加密？(Y/n) [Y]: " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
    E2EE_PASSPHRASE=""
    warn "未启用加密，笔记将以明文传输"
fi

# ── Step 4: 生成 .env ──
echo ""
info "生成配置文件..."

cat > .env << EOF
# 无限循环 Neverend 配置
# 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')

DOMAIN=$DOMAIN
COUCHDB_USER=$COUCHDB_USER
COUCHDB_PASSWORD=$COUCHDB_PASSWORD
COUCHDB_DBNAME=obsidian-livesync
E2EE_PASSPHRASE=$E2EE_PASSPHRASE
NEVEREND_USER=$NEVEREND_USER
NEVEREND_PASSWORD=$NEVEREND_PASSWORD
EOF

ok "配置已保存到 $INSTALL_DIR/.env"

# ── Step 5: 启动服务 ──
echo ""
info "正在启动服务（首次可能需要 1-2 分钟下载镜像）..."
echo ""

docker compose up -d

# 等待 init 容器完成
info "等待初始化完成..."
for i in $(seq 1 60); do
    if docker logs neverend-init 2>&1 | grep -q "部署完成"; then
        break
    fi
    sleep 2
done

# ── Step 6: 输出结果 ──
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🔄 无限循环 Neverend — 安装完成！     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 提取 Setup URI
SETUP_URI=$(docker logs neverend-init 2>&1 | grep "obsidian://setuplivesync" | head -1)
URI_PASS=$(docker logs neverend-init 2>&1 | grep "Setup URI 口令" | sed 's/.*：//')
E2EE_PASS=$(docker logs neverend-init 2>&1 | grep "端到端加密口令" | sed 's/.*：//')

echo -e "${CYAN}📋 在 Obsidian 中使用：${NC}"
echo ""
echo "  1. 打开 Obsidian → 设置 → 第三方插件 → 浏览"
echo "  2. 搜索 \"Self-hosted LiveSync\" → 安装 → 启用"
echo "  3. Ctrl/Cmd+P → 输入 \"Use the copied setup URI\""
echo "  4. 粘贴下面的 Setup URI"
echo ""

if [ -n "$SETUP_URI" ]; then
    echo -e "${YELLOW}🔗 Setup URI:${NC}"
    echo "$SETUP_URI"
    echo ""
    echo -e "${YELLOW}🔑 Setup URI 口令:${NC} $URI_PASS"
    if [ -n "$E2EE_PASS" ]; then
        echo -e "${YELLOW}🔐 端到端加密口令:${NC} $E2EE_PASS"
    fi
else
    warn "未能自动提取 Setup URI，请手动查看:"
    echo "  docker logs neverend-init"
fi

echo ""
echo -e "${CYAN}📝 账号信息（请妥善保管）:${NC}"
echo "  管理员:  $COUCHDB_USER / $COUCHDB_PASSWORD"
echo "  同步用户: $NEVEREND_USER / $NEVEREND_PASSWORD"
echo "  安装目录: $INSTALL_DIR"
echo ""

if [ "$DOMAIN" = "localhost" ]; then
    warn "当前配置为 localhost，仅限本机使用"
    echo "  如需手机访问，请修改 .env 中的 DOMAIN 为你的域名"
    echo "  然后运行: cd $INSTALL_DIR && docker compose restart"
fi

echo -e "${GREEN}🎉 完成！在 Obsidian 中粘贴 Setup URI 即可开始同步。${NC}"
echo ""
