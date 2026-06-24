# 🔄 无限循环 Neverend

**Obsidian 一键自托管同步——替代 $8/月的 Obsidian Sync**

> `docker compose up -d` 即可拥有免费的跨设备笔记同步

## 为什么需要它？

| 方案 | 费用 | 难度 | 隐私 |
|------|------|------|------|
| Obsidian Sync（官方） | $8/月 | ⭐ | ❌ 云端 |
| **Neverend（自建）** | **免费** | ⭐⭐ | ✅ 完全自控 |
| 手动搭建 CouchDB | 免费 | ⭐⭐⭐⭐⭐ | ✅ 完全自控 |

Neverend 把原本需要 **6 步手动配置**（创建目录→写配置→启动容器→初始化CouchDB→装Deno→生成URI）压缩为 **1 条命令**。

## 快速开始

### 前提条件

- 一台服务器（VPS / NAS / 旧电脑均可）
- Docker + Docker Compose
- 域名（手机访问需要，桌面可选）

### 3 步部署

```bash
# 1. 克隆
git clone https://github.com/503496348-ops/neverend.git
cd neverend

# 2. 配置
cp .env.example .env
# 编辑 .env，填入你的域名和密码

# 3. 启动
docker compose up -d
```

### 查看 Setup URI

```bash
docker logs neverend-init
```

输出：
```
🔄 无限循环 Neverend — 部署完成！

🔗 Setup URI：
obsidian://setuplivesync?settings=...

🔑 Setup URI 口令：patient-haze
🔐 端到端加密口令：auto-generated
```

### 在 Obsidian 中使用

1. 安装插件 **Self-hosted LiveSync**（社区插件市场搜索）
2. Ctrl/Cmd+P → "Use the copied setup URI"
3. 粘贴上面的 Setup URI
4. 输入口令 → 完成！

## 架构

```
Obsidian ──HTTPS──► Caddy ──HTTP──► CouchDB
(客户端)  (LiveSync) (SSL反代)     (数据库)
```

所有组件运行在 Docker 中，数据持久化到 Docker Volume。

## 配置说明

编辑 `.env` 文件：

```bash
# 必填
DOMAIN=notes.example.com       # 你的域名（内网填 localhost）
COUCHDB_USER=admin             # 管理员账号
COUCHDB_PASSWORD=your-password # 管理员密码（务必修改！）

# 可选
COUCHDB_DBNAME=obsidian-livesync  # 数据库名
E2EE_PASSPHRASE=                  # 端到端加密口令（留空自动生成）
NEVEREND_USER=user                # 同步用户名
NEVEREND_PASSWORD=password        # 同步密码
```

## 多设备同步

在第一台设备配置完成后：
1. 从 `docker logs neverend-init` 获取 Setup URI
2. 在新设备的 Obsidian 中安装 LiveSync 插件
3. 粘贴同一个 Setup URI
4. 选择 "Set it up as secondary device"
5. 自动开始同步！

## 常见问题

**Q: 和 Obsidian Sync 有什么区别？**
A: 功能相同（跨设备实时同步），但 Neverend 是自建的，数据在你自己的服务器上，完全免费。

**Q: 手机能用吗？**
A: 可以，但需要域名 + SSL 证书（Caddy 自动申请）。内网只能桌面端用。

**Q: 数据安全吗？**
A: 支持端到端加密（AES-256-GCM），数据离开设备前已加密，服务器上只有密文。

**Q: 支持多大的笔记库？**
A: 理论无上限。单文档限制 50MB，HTTP 请求限制 4GB。超大附件建议用其他方式同步。

**Q: 服务器挂了笔记会丢吗？**
A: 不会。每个设备本地都有完整副本，服务器只是同步中转。

## 许可证

Apache-2.0

## 致谢

- [vrtmrz/obsidian-livesync](https://github.com/vrtmrz/obsidian-livesync) — LiveSync 插件
- [Apache CouchDB](https://couchdb.apache.org/) — 同步数据库
- [Caddy](https://caddyserver.com/) — 自动 HTTPS 反向代理

---

**© 2026 AtomCollide-智械工坊**
