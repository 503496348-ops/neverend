---
name: neverend
version: 1.0.0
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
    updated: 2026-06-24
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

## Quick Start

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
- 域名（手机访问必须，桌面可选）
- 公网 IP 或 Cloudflare Tunnel

### Step 2: 配置

```bash
cp .env.example .env
```

必填配置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DOMAIN` | 你的域名 | `notes.example.com` |
| `COUCHDB_USER` | 管理员用户名 | `admin` |
| `COUCHDB_PASSWORD` | 管理员密码 | `your-secure-password` |

可选配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `COUCHDB_DBNAME` | 数据库名 | `obsidian-livesync` |
| `E2EE_PASSPHRASE` | 端到端加密口令 | 自动生成 |
| `NEVEREND_USER` | 同步用户名 | `user` |
| `NEVEREND_PASSWORD` | 同步密码 | `password` |

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

### Step 5: Obsidian 客户端配置

1. 打开 Obsidian → 设置 → 第三方插件 → 浏览
2. 搜索 "Self-hosted LiveSync" → 安装 → 启用
3. Ctrl/Cmd+P → 输入 "Use the copied setup URI"
4. 粘贴 Setup URI
5. 输入 Setup URI 口令
6. 选择 "Set it up as secondary device"
7. 等待同步开始

## 技术参考

### 架构

```
┌─────────────┐     HTTPS      ┌───────┐     HTTP      ┌──────────┐
│  Obsidian   │◄──────────────►│ Caddy │◄─────────────►│ CouchDB  │
│  (客户端)   │  LiveSync插件  │ (SSL) │   :5984       │  (数据库) │
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

## Pitfalls

1. **域名未解析就启动** → Caddy 无法申请 SSL 证书 → 用 `localhost` 先测试
2. **忘记 .env 中的密码** → 容器删除后数据丢失前无法登录 → 启动后立即记录密码
3. **手机无法连接** → 必须有合法 SSL 证书 → 必须用真实域名 + 公网 IP
4. **同步冲突** → LiveSync 自动处理，但大文件（>50MB）可能失败 → 拆分大附件
5. **CouchDB 权限错误** → docker-compose 中 volume 权限不一致 → 重启容器
6. **CORS 报错** → 检查 local.ini 中的 origins 是否包含你的协议 → localhost 用 http
