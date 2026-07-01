# 🔄 无限循环 Neverend

**Obsidian 一键自托管同步——替代 $8/月的 Obsidian Sync**

> `curl -fsSL .../install.sh | bash` 即可拥有免费的跨设备笔记同步

## 为什么需要它？

| 方案 | 费用 | 难度 | 隐私 |
|------|------|------|------|
| Obsidian Sync（官方） | $8/月 | ⭐ | ❌ 云端 |
| **Neverend（自建）** | **免费** | ⭐ | ✅ 完全自控 |
| 手动搭建 CouchDB | 免费 | ⭐⭐⭐⭐⭐ | ✅ 完全自控 |

Neverend 把原本需要 **6 步手动配置**（创建目录→写配置→启动容器→初始化CouchDB→装Deno→生成URI）压缩为 **1 条命令**。

## 快速开始

### 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash
```

脚本自动完成：检查/安装 Docker → 克隆仓库 → 生成密码 → 启动服务 → 输出 Setup URI

### 无交互安装（智能体/脚本用）

```bash
# 有域名
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash -s -- --domain notes.yourdomain.com --auto

# 无域名，使用 IP:端口（推荐 18080，已验证国内可访问）
curl -fsSL https://raw.githubusercontent.com/503496348-ops/neverend/main/install.sh | bash -s -- --port 18080 --auto
```

### 在 Obsidian 中使用

**方法 A：手动配置（推荐，更稳）**

1. 安装插件 **Self-hosted LiveSync**（社区插件市场搜索）
2. 打开插件设置，填写以下字段：

| 字段 | 值 |
|------|-----|
| Remote Database URI | `http://你的IP:端口` |
| Username | `user` |
| Password | `（密码）` |
| Database Name | `obsidian-livesync` |
| End-to-End Encryption | `true` |
| Passphrase | `（E2EE 口令）` |

3. 点击 "Test" 验证连接
4. 选择 "Join"（加入已有服务器）

**方法 B：Setup URI**

1. Ctrl/Cmd+P → "Use the copied setup URI"
2. 粘贴 Setup URI → 输入口令 → 完成！

**⚠️ 注意：Setup URI 中的 localhost:5984 必须替换为实际的 IP:端口！**

## 同步策略选择

走到 "Mostly Complete: Decision Required" 界面时：
- **当前设备有笔记** → "My remote server is already set up. I want to join this device."
- **当前设备是空的** → 同上
- **当前设备要初始化服务器** → 第一个选项（会覆盖服务器数据，谨慎！）

## 架构

```
Obsidian ──HTTP/HTTPS──► Caddy ──HTTP──► CouchDB
(客户端)    (LiveSync)   (反代)       (数据库)
```

所有组件运行在 Docker 中，数据持久化到 Docker Volume。

## 配置说明

编辑 `.env` 文件：

```bash
DOMAIN=notes.yourdomain.com  # 你的域名（或 IP）
COUCHDB_USER=admin            # 管理员账号
COUCHDB_PASSWORD=changeme     # 管理员密码（务必修改！）
COUCHDB_DBNAME=obsidian-livesync
E2EE_PASSPHRASE=              # 端到端加密口令（留空自动生成）
NEVEREND_USER=obsidian        # 同步用户名
NEVEREND_PASSWORD=            # 同步密码（留空自动生成）
NEVEREND_PORT=80              # 公网端口（80/443 被占用时用 18080）
```

## 多设备同步

在第一台设备配置完成后：
1. 从 `docker logs neverend-init` 获取 Setup URI
2. 在新设备的 Obsidian 中安装 LiveSync 插件
3. 粘贴同一个 Setup URI（或手动配置）
4. 选择 "Set it up as secondary device"
5. 自动开始同步！

## 实战踩坑清单

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

### 🟢 低频踩坑

9. **域名未解析就启动** → Caddy 无法申请 SSL 证书 → 用 IP:端口 先测试。
10. **忘记 .env 中的密码** → 容器删除后无法登录 → 启动后立即记录密码。
11. **手机无法连接** → 必须有合法 SSL 证书 → 必须用真实域名 + 公网 IP。
12. **同步冲突** → LiveSync 自动处理，但大文件（>50MB）可能失败 → 拆分大附件。

## 常见报错与解决

| 报错 | 原因 | 解决 |
|------|------|------|
| Failed to parse Setup-URI | URI 没粘完被截断 | 从生成的 txt 文件整行复制 |
| 连接显示 8080 / 连不上 | 旧配置未刷新 | 重置 LiveSync 设置后重新运行向导，或重启 Obsidian |
| 401 Unauthorized | 用户名/密码错 | 检查 user 和 password 是否与 neverend-init 输出一致 |
| 503 | 几乎不是服务器问题 | 关闭代理/VPN，检查 URI 端口是否正确 |
| E2EE 不能解密 | 端到端加密未启用或 passphrase 错 | 确保 encrypt=true 且 passphrase 正确 |
| 第一次同步后笔记乱了 | 设备角色选错 | 加入已有服务器时，不要选 "Setup as primary device" |

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

## 验证清单

部署完成后，逐项验证：

- [ ] `neverend-caddy` 和 `neverend-couchdb` 容器都 Up
- [ ] 本地 curl 返回 200 或 401
- [ ] 从国内终端测试端口连通
- [ ] Obsidian 手动配置填对 IP:端口
- [ ] E2EE 启用，passphrase 正确
- [ ] 同步成功，状态栏显示 Completed

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

**Q: 80/443 端口被占用了怎么办？**
A: 使用 `--port 18080` 参数，或修改 `.env` 中的 `NEVEREND_PORT=18080`。已验证 18080 国内可访问。

## 技术栈

- **LiveSync 同步协议** — 开源社区同步插件，支持全平台
- **Apache CouchDB** — 分布式同步数据库
- **Caddy** — 自动 HTTPS 反向代理

## 许可证

Apache-2.0

---

## 🚀 关于元素碰撞 AtomCollide — AI 智能体实验室

**测试人专属成长社群 正式招募**

我们的目标很纯粹：连接每一位测试工程师 / AI 使用探索与爱好者，让你在这里既能扎实打磨技术硬实力，也能打通职业晋升的新通路。这是一个专注于 AI 领域的开源组织，汇聚了众多优秀学习者。

**使命 — for the learner，和学习者一起成长。**

元素碰撞 AtomCollide — AI 智能体实验室聚集了来自全国各地、各大一线厂的测试从业者，大家在社群里深度投入 AI 赋能测试的落地研究，共同沉淀了《AtomCollide AI 测试实战知识库》，只输出对测试人真正有用、可直接落地的干货内容。

### 💼 找工作：更省力，也更精准

- **一线大厂内推通道**：汇聚字节、阿里、腾讯等头部企业测试负责人与同行资源，岗位直达面试官，比海投简历效率高 3 倍以上
- **全链路求职赋能包**：专属整理的 AI 测试面试题库、简历优化模板、面试技巧与晋升指导，帮你在关键环节建立优势
- **线下技术沙龙 & 人脉网络**：不定期举办城市线下交流局，拓展靠谱行业人脉

### 🧪 学 AI 测试：真正落地，拒绝空谈

- **从 0 到 1 实战落地体系**：紧跟 Skills、MCP、Openclaw、RAG、AI IDE 等前沿技术，深度融合进接口测试、自动化测试、性能测试等全流程
- **独家自研资料与工具矩阵**：《AtomCollide AI 测试实战知识库》全套内容、AI 测试自研平台、系统视频教程、职场通用模板
- **前沿技术同步与提效方案**：最新研究成果与行业动态分享，走在 AI 测试的最前沿

这是一个**拒绝水群、纯技术驱动、真诚互助的成长社群**。

### 📚 知识库

- [知识库入口 1](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne)
- [知识库入口 2](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh)
- [知识库入口 3](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe)
- [T3｜学习文档・组织升级](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb)
- [知识库入口 5](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd)
- [知识库入口 6](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd)
- [知识库入口 7](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg)

### 💬 社群入口

| 社群 | 链接 |
|------|------|
| AI 探索交流 1 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI 探索交流 2 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI 探索交流 3 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI 探索交流 4 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI 探索交流 5 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI 探索交流 6 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI 探索交流 7 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI 探索交流 8 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI 探索交流 9 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI 探索交流 10 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI 探索交流 · 网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI 探索交流群 · 音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI 探索交流群 · 微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

> 📢 **社群公告**：所有社群已实现内容全域同步，保留 1 个常用社群即可。

### 🌐 产品矩阵全家福

👉 [查看 24 款产品矩阵](https://503496348-ops.github.io/atomcollide-product-matrix/)

---

**© 2026 元素碰撞 AtomCollide — AI 智能体实验室**
**使命：for the learner，和学习者一起成长**

---

## 组织与社群入口

**元素碰撞 · AtomCollide-AI 智能体实验室**：面向学习者、创作者与自动化实践者，持续沉淀可复用的 AI Agent 产品、工作流与工程经验。使命：**for the learner**。

> 请选择 1 个常用社群加入，内容全域同步，无需重复加入。

### 知识库

| 知识库 | 链接 |
|---|---|
| 踩坑合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne) |
| 商业化案例库 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh) |
| 科普专栏 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe) |
| Open Build | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb) |
| LLM / Agent / 研究报告 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd) |
| Skill 封装合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd) |
| 社区治理运营 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg) |

### 社群邀请

| 社群 | 链接 |
|---|---|
| AI 探索交流 1 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI 探索交流 2 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI 探索交流 3 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI 探索交流 4 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI 探索交流 5 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI 探索交流 6 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI 探索交流 7 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI 探索交流 8 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI 探索交流 9 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI 探索交流 10 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI 探索交流 — 网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI 探索交流群 — 音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI 探索交流群 — 微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

---

AtomCollide-智械工坊团队出品。更多产品见：[AtomCollide Product Matrix](https://503496348-ops.github.io/atomcollide-product-matrix/)。


## 示例输出

本仓库的最小可验证使用路径：

1. 阅读 README 的 Quick Start / 使用说明，完成本地安装或配置。
2. 按仓库提供的命令、脚本或入口运行一次最小任务。
3. 对照本产品定位验证输出：**无限循环（Neverend）** 属于 **知识管理** 产品，目标是把输入材料转化为可检查、可复用的结果。
4. 若运行环境暂不可用，先通过 README、CHANGELOG、CI 状态和源码结构完成静态验收，再补充真实截图或录屏。

> 维护要求：后续每次发布都应把真实运行截图、CLI 输出、网页截图或 API 响应样例补充到本节，避免仓库首页只描述能力、不展示结果。

## Governance Links

- [LICENSE](LICENSE)
- [CHANGELOG](CHANGELOG.md)
- [SECURITY](SECURITY.md)
- [CONTRIBUTING](CONTRIBUTING.md)


