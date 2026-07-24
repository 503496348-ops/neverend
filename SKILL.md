---
name: neverend
description: "知识库管理工具 — Obsidian Vault 索引构建、备份、同步审计"
license: MIT
metadata:
  author: 503496348-ops
  version: 1.0.0
---

# Neverend — 知识库管理工具

## 触发条件

- "知识库"
- "vault"
- "备份"
- "索引"
- "同步审计"
- "obsidian"

为 Obsidian Vault 提供索引构建、增量备份和同步审计能力。

## 核心能力

| 命令 | 说明 |
|------|------|
| `neverend index <path>` | 从 Markdown 文件构建 SQLite 索引 |
| `neverend backup <src> <dst>` | 全量/增量备份 Vault |
| `neverend health` | CouchDB + SSL 健康检查 |
| `neverend audit <path>` | 审计文档一致性 |

## 快速开始

```bash
# 构建 vault 索引
python3 scripts/cli.py index /path/to/vault

# 增量备份
python3 scripts/cli.py backup /vault /backup --incremental

# 健康检查
python3 scripts/cli.py health
```

## 架构

- `scripts/vault_index.py` — SQLite 索引构建器（NoteRecord/LinkRecord）
- `scripts/backup.py` — CouchDB 全量/增量备份
- `scripts/sync_auditor.py` — 文档同步审计
- `scripts/healthcheck.py` — CouchDB + SSL 检查
- `scripts/setup_wizard.py` — 初始化向导

## 测试

```bash
python3 -m pytest tests/ -q
```

## DNA Memory 融合（Obsidian真源+有界采集）

基于 [DNA Memory](https://github.com/AIPMAndy/dna-memory) Markdown真源模式增强：
- Markdown为唯一长期真源，SQLite为可重建索引
- YAML frontmatter元数据（type/confidence/source/created/supersedes）
- 有界采集规则（session ID+路径+哈希+偏移+计数）
- Vault同步审计（孤儿索引/幽灵文件/过期记忆检测）

详见 `references/dna-memory-obsidian-pattern.md`
