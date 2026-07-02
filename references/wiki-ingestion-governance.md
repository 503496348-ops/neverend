# Wiki Ingestion Governance Pack

Neverend 在原有 Obsidian 自托管同步之外，新增“知识库入库治理”能力：把散落的 Markdown/PDF/笔记文件整理成可迁移、可审计、可回滚的知识资产。

## Capability Surface

| Capability | Contract | Evidence |
|---|---|---|
| Semantic classification plan | For each input file, propose a target knowledge path, confidence, and reason. | `classification_plan.json` with file, target_path, confidence, rationale. |
| Dry-run upload manifest | No remote write before user approval. | `upload_manifest.json` with planned create/upload/move operations. |
| Markdown normalization | Normalize headings, blank lines, list indentation, trailing spaces, and link style without touching code blocks. | Before/after diff and skipped large-file list. |
| Wiki structure health audit | Detect deep nesting, empty categories, naming inconsistency, orphan nodes, and duplicate topic clusters. | `wiki_health_report.md` with scores and P0/P1/P2 actions. |
| PDF/asset intake | Stage binary assets separately, verify uploaded node metadata, then attach/move into the target parent. | upload task id, final node token, title, parent token. |

## Agent Workflow

1. **Inventory**: list local files, size, extension, first content sample, and existing target wiki tree.
2. **Classify**: produce a table: file → target path → existing node/new node suggestion → confidence → rationale.
3. **Ask for approval**: remote create/upload/move is blocked until the user accepts the dry run.
4. **Normalize**: format Markdown locally; preserve code fences and skip files above configured risk limits unless explicitly approved.
5. **Upload or move**: execute only approved operations; store a replayable manifest.
6. **Audit again**: run structure health audit after the operation and compare before/after scores.
7. **Rollback notes**: for every remote mutation, record enough identifiers to reverse or manually repair it.

## Safety Boundaries

- Never infer a destructive move/delete from “整理一下”; destructive operations require explicit user approval and a manifest.
- Do not store raw credentials, app tokens, table ids, chat ids, or user ids in reports. Use `[REDACTED]`.
- Prefer dry-run first. If a tool cannot prove the final node exists, mark the operation as unverified.
- Existing taxonomy wins over file-name guesses. New category creation is a suggestion until approved.

## Output Templates

### Classification Plan

```json
{
  "root": "[REDACTED]",
  "files": [
    {
      "path": "docs/example.md",
      "target_path": "Knowledge/Guides",
      "target_exists": true,
      "confidence": 0.86,
      "rationale": "The title and first section describe an operational guide.",
      "operation": "upload"
    }
  ]
}
```

### Health Report Sections

1. Executive summary
2. Structure score: depth, organization, content distribution
3. Problems: empty categories, deep nodes, inconsistent names, orphan nodes
4. Recommended actions: P0/P1/P2
5. Dry-run mutation manifest
6. Verification evidence
