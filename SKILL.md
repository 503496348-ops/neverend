---
name: neverend
version: 1.1.0
description: "无限循环——Obsidian一键自托管同步。docker compose up -d 即可拥有免费的跨设备笔记同步，替代Obsidian Sync($8/月)。"
author: AtomCollide-智械工坊团队
license: Apache-2.0
triggers:
  - Obsidian同步
  - Obsidian自托管
  - 笔记同步
  - LiveSync部署
  - CouchDB部署
  - Obsidian Sync替代
  - 免费笔记同步
  - 跨设备同步
  - 无限循环
  - neverend
  - obsidian deploy
  - self-hosted sync
metadata:
  hermes:
    author: AtomCollide-智械工坊团队
    created: 2026-06-24
    updated: 2026-06-25
    maturity: production
    category: productivity
    tags:
      - Obsidian
      - LiveSync
      - CouchDB
      - 自托管
      - 笔记同步
      - Docker
      - 知识管理
      - PKM
scripts:
  init: scripts/init_and_generate.py
---

# 无限循环 Neverend

**Obsidian 一键自托管同步——替代 $8/月的 Obsidian Sync**

## When to Use

- 用户想要跨设备同步 Obsidian 笔记
- 用户不想付费 Obsidian Sync
- 用户有自己的服务器/NAS/云主机
- 用户想要笔记数据完全自控

## Agent Workflow（智能体专用）

**核心原则：用户只需要提供域名和密码，其余全部自动完成。**

当用户说"帮我部署 Obsidian 同步"或类似意图时，按以下步骤执行：

### Step 1: 收集信息（只需问 2-3 个问题）

向用户确认：
1. **域名**：是否有域名？（有→问域名；没有→用 IP:端口）
2. **端口**：80/443 是否可用？（不确定→默认 18080，已验证国内可访问）
3. **密码偏好**：自动生成还是自定义？

### Step 2: 一键部署

```bash
# 有域名（推荐）
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash -s -- --domain 用户的域名 --auto

# 无域名，使用 IP:端口（如 18080）
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash -s -- --port 18080 --auto
```

### Step 3: 提取结果

脚本输出包含 `---NEVEREND_OUTPUT_START---` 到 `---NEVEREND_OUTPUT_END---` 之间的结构化数据：
```
SETUP_URI=obsidian://setuplivesync?settings=...
URI_PASSPHRASE=patient-haze
E2EE_PASSPHRASE=icy-snow
COUCHDB_PASSWORD=xxx
```

**⚠️ 关键：Setup URI 中的 localhost:5984 必须替换为实际的 IP:端口！**

### Step 4: 告知用户

向用户展示（不要展示技术细节）：
1. **手动配置表**（推荐，比 Setup URI 更稳）
2. **口令**（2-3 个英文单词）
3. **Obsidian 操作步骤**（3 步）

**手动配置表（推荐发给用户）：**

| 字段 | 值 |
|------|-----|
| Remote Database URI | `http://IP:端口` |
| Username | `user` |
| Password | `（生成的密码）` |
| Database Name | `obsidian-livesync` |
| End-to-End Encryption | `true` |
| Passphrase | `（生成的 E2EE 口令）` |

**不要展示给用户的内容：**
- Docker 命令
- .env 文件内容
- CouchDB 配置
- 任何技术术语

### 脚本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--domain DOMAIN` | 域名 | — |
| `--port PORT` | 公网端口 | 80（有域名）/ 18080（无域名） |
| `--password PASS` | CouchDB 管理员密码 | 自动生成 |
| `--sync-password PASS` | 同步用户密码 | 自动生成 |
| `--e2ee PASSPHRASE` | 端到端加密口令 | 自动生成 |
| `--auto` | 全自动，不弹确认 | — |

## Quick Start

**一条命令安装（推荐）：**

```bash
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash
```

脚本会自动完成：
1. ✅ 检查/安装 Docker
2. ✅ 克隆仓库
3. ✅ 交互式配置（回车用默认值）
4. ✅ 启动服务
5. ✅ 输出 Setup URI

**手动安装（进阶用户）：**

```bash
# 1. 克隆仓库
git clone https://github.com/503496348-ops/neverend.git
cd neverend

# 2. 配置（修改域名和密码）
cp .env.example .env
nano .env

# 3. 一键启动
docker compose up -d

# 4. 查看 Setup URI
docker logs neverend-init
```

然后在 Obsidian 中：
1. 安装插件 **Self-hosted LiveSync**
2. 命令面板 → "Use the copied setup URI"
3. 粘贴 URI → 输入口令 → 完成

## 工作流

### Step 1: 环境准备

需要：
- Docker + Docker Compose（V2）
- 域名（手机访问必须，桌面可用 IP:端口）
- 公网 IP 或 Cloudflare Tunnel

### Step 2: 配置

```bash
cp .env.example .env
```

必填配置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DOMAIN` | 你的域名（或 IP） | `notes.example.com` 或 `1.2.3.4` |
| `COUCHDB_USER` | 管理员用户名 | `admin` |
| `COUCHDB_PASSWORD` | 管理员密码 | `your-secure-password` |

可选配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `COUCHDB_DBNAME` | 数据库名 | `obsidian-livesync` |
| `E2EE_PASSPHRASE` | 端到端加密口令 | 自动生成 |
| `NEVEREND_USER` | 同步用户名 | `user` |
| `NEVEREND_PASSWORD` | 同步密码 | `password` |
| `NEVEREND_PORT` | 公网端口 | `80` |

### Step 3: 启动

```bash
docker compose up -d
```

首次启动自动完成：
1. CouchDB 单节点配置
2. CORS 设置
3. 数据库创建
4. 用户创建
5. Setup URI 生成

### Step 4: 查看 Setup URI

```bash
docker logs neverend-init
```

输出示例：
```
🔄 无限循环 Neverend — 部署完成！

🔗 Setup URI：
obsidian://setuplivesync?settings=...

🔑 Setup URI 口令：patient-haze
🔐 端到端加密口令：auto-generated-passphrase
```

**⚠️ 重要：Setup URI 中的 localhost:5984 必须替换为实际地址！**

### Step 5: Obsidian 客户端配置

**方法 A：手动配置（推荐，更稳）**

1. 打开 Obsidian → 设置 → 第三方插件 → 浏览
2. 搜索 "Self-hosted LiveSync" → 安装 → 启用
3. 打开插件设置，填写以下字段：

| 字段 | 值 |
|------|-----|
| Remote Database URI | `http://你的IP:端口` |
| Username | `user` |
| Password | `（密码）` |
| Database Name | `obsidian-livesync` |
| End-to-End Encryption | `true` |
| Passphrase | `（E2EE 口令）` |

4. 点击 "Test" 验证连接
5. 选择 "Join"（加入已有服务器，不要选 Primary）

**方法 B：Setup URI**

1. Ctrl/Cmd+P → 输入 "Use the copied setup URI"
2. 粘贴 Setup URI（必须整行，不能截断）
3. 输入 Setup URI 口令
4. 选择 "Set it up as secondary device"
5. 等待同步开始

### Step 6: 同步策略选择

走到 "Mostly Complete: Decision Required" 界面时：
- **当前设备有笔记，想加入已有服务器** → "My remote server is already set up. I want to join this device."
- **当前设备是空的，想从服务器下载** → 同上
- **当前设备要初始化服务器** → 第一个选项（会覆盖服务器数据，谨慎！）

## 技术参考

### 架构

```
┌─────────────┐     HTTP/HTTPS  ┌───────┐     HTTP      ┌──────────┐
│  Obsidian   │◄──────────────►│ Caddy │◄─────────────►│ CouchDB  │
│  (客户端)   │  LiveSync插件  │ (代理) │   :5984       │  (数据库) │
└─────────────┘                └───────┘               └──────────┘
```

### 组件说明

| 组件 | 作用 | 镜像 |
|------|------|------|
| CouchDB | 数据同步后端 | `couchdb:3` |
| Caddy | 反向代理 + 自动SSL | `caddy:2-alpine` |
| Init | 自动配置 + URI生成 | `python:3.12-slim` |

### 数据持久化

| Volume | 内容 |
|--------|------|
| `couchdb-data` | 笔记数据 |
| `caddy-data` | SSL证书 |
| `caddy-config` | Caddy配置 |

### 备份

```bash
# 备份 CouchDB 数据
docker exec neverend-couchdb tar czf - /opt/couchdb/data > backup.tar.gz

# 恢复
docker cp backup.tar.gz neverend-couchdb:/tmp/
docker exec neverend-couchdb tar xzf /tmp/backup.tar.gz -C /
```

## 服务端快速检查

```bash
# 进入 neverend 目录
cd /home/ubuntu/neverend

# 查看容器状态
sudo docker compose ps

# 本地验证 CouchDB 链路
curl -s -o /dev/null -w "%{http_code}\n" http://user:PASSWORD@127.0.0.1:PORT/obsidian-livesync/

# 服务器本地验证公网端口
curl -s -o /dev/null -w "%{http_code}\n" --connect-timeout 5 http://$(curl -s ifconfig.me):PORT

# 查看日志
sudo docker logs --tail 50 neverend-caddy
sudo docker logs --tail 50 neverend-couchdb
```

## 国内访问测试

**必须从中国境内终端执行，服务器本地测试不能代替！**

```bash
# Windows PowerShell
Test-NetConnection -ComputerName 服务器IP -Port 端口

# macOS/Linux
nc -vz 服务器IP 端口
```

## Pitfalls（实战踩坑清单）

### 🔴 高频踩坑

1. **80/443 端口被占用** → 服务器很可能已有 nginx/xray，选 18080 等非标准端口。已验证 18080 国内可访问。
2. **Setup URI 中的 localhost:5984** → init 脚本默认生成本地地址，必须替换为 `http://IP:端口`。推荐直接用手动配置。
3. **PowerShell 的 curl 不是真 curl** → Windows 测试端口用 `Test-NetConnection`，不是 `curl`。
4. **Setup URI 粘贴截断** → 必须整行复制，半截断会报 "Failed to parse Setup-URI"。
5. **E2EE 默认未启用** → 手动配置时要特意开启 `encrypt=true`。

### 🟡 中频踩坑

6. **旧配置缓存** → 改完设置后如果报错仍显示旧端口，重置 LiveSync 数据库或重启 Obsidian。
7. **客户端选错角色** → 加入已有服务器时选 "Join"，不要选 "Primary device"（会覆盖服务器数据）。
8. **容器里的 nginx ≠ 宿主机的 nginx** → 修改端口时不要搞混。
9. **百度网盘 bdpan 路径限制** → 大文件备份需用 bypy 其他路径。

### 🟢 低频踩坑

10. **域名未解析就启动** → Caddy 无法申请 SSL 证书 → 用 IP:端口 先测试。
11. **忘记 .env 中的密码** → 容器删除后无法登录 → 启动后立即记录密码。
12. **手机无法连接** → 必须有合法 SSL 证书 → 必须用真实域名 + 公网 IP。
13. **同步冲突** → LiveSync 自动处理，但大文件（>50MB）可能失败 → 拆分大附件。
14. **CORS 报错** → 检查 local.ini 中的 origins 是否包含你的协议 → localhost 用 http。

## 常见报错与解决

| 报错 | 原因 | 解决 |
|------|------|------|
| Failed to parse Setup-URI | URI 没粘完被截断 | 从生成的 txt 文件整行复制 |
| 连接显示 8080 / 连不上 | 旧配置未刷新 | 重置 LiveSync 设置后重新运行向导，或重启 Obsidian |
| 401 Unauthorized | 用户名/密码错 | 检查 user 和 password 是否与 neverend-init 输出一致 |
| 503 | 几乎不是服务器问题 | 关闭代理/VPN，检查 URI 端口是否正确 |
| E2EE 不能解密 | 端到端加密未启用或 passphrase 错 | 确保 encrypt=true 且 passphrase 正确 |
| 第一次同步后笔记乱了 | 设备角色选错 | 加入已有服务器时，不要选 "Setup as primary device" |

## 验证清单

部署完成后，逐项验证：

- [ ] `neverend-caddy` 和 `neverend-couchdb` 容器都 Up
- [ ] 本地 curl 返回 200 或 401
- [ ] 从国内终端测试端口连通
- [ ] Obsidian 手动配置填对 IP:端口
- [ ] E2EE 启用，passphrase 正确
- [ ] 同步成功，状态栏显示 Completed

## 给 Agent 的配置指南

1. 服务器信息在 `/home/ubuntu/neverend/.env` 和 `neverend-init` 输出中
2. 生成 Setup URI 时必须把 `localhost:5984` 替换成 `IP:端口`
3. 故障排查优先检查客户端 URI 端口、代理/VPN、旧配置
4. 发给用户时同时提供：手动配置表 + 口令 + E2EE passphrase
5. 如需更新密码，必须同步更新 .env、CouchDB 用户、所有客户端配置
6. **推荐发手动配置表而非 Setup URI**，更稳不易出错

## 给用户的使用说明

1. 下载并安装 Obsidian 插件 Self-hosted LiveSync
2. 推荐使用手动配置，填写上文表格中的字段
3. 同步策略选择 join device，勿选 primary device
4. 第一次同步可能较慢，等待 Completed 状态
5. 若遇到报错，先关闭代理/VPN，重启 Obsidian 后重试

## 短期维护

```bash
# 重启服务
cd /home/ubuntu/neverend && sudo docker compose restart

# 查日志
sudo docker logs --tail 50 neverend-caddy
sudo docker logs --tail 50 neverend-couchdb

# 更改端口
# 修改 docker-compose.yml 中 caddy 的 ports 映射
# 修改 conf/Caddyfile 中的 bind 和端口
# 重新 docker compose up -d
```
