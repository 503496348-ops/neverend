# DNA Memory Obsidian真源模式融合

> 来源: [DNA Memory](https://github.com/AIPMAndy/dna-memory) — Markdown/Obsidian长期真源
> 融合目标: Obsidian vault管理、有界采集、session元数据

## Markdown真源策略

长期记忆以Markdown文件为唯一真源：
- SQLite是可删除、可重建的索引层
- 文件路径即分类（preference/fact/insight/...）
- YAML frontmatter携带元数据（type/confidence/source/created/supersedes）

## 记忆文件结构

```yaml
---
type: preference|fact|insight|decision|project_state|open_loop|workflow|error_lesson
confidence: high|medium|low
importance: 0.0-1.0
source: session_id or url
created: ISO timestamp
supersedes: [older_memory_id]  # optional
---

# 记忆标题

简洁结论（<800字符）

## 来源
有界来源指针（非完整transcript）
```

## 有界采集规则

只采集：
- session ID + 路径 + 哈希 + 偏移 + 计数
- 经过审查的提案
- 验证后的关键结论

不采集：
- 完整transcript
- 凭证/密钥
- 原始prompt
- 大段工具输出

## Vault同步审计

定期检查：
- Markdown文件与SQLite索引一致性
- 孤儿索引（索引存在但文件缺失）
- 幽灵文件（文件存在但无索引）
- 过期记忆（超过有效期未更新）
