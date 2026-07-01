#!/usr/bin/env python3
"""Neverend sync auditor for exported sync documents."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import argparse, json, re
from pathlib import Path
from typing import Iterable, List
CONFLICT_RE=re.compile(r'(_conflicts|conflict|<<<<<<<|>>>>>>>)', re.I)
@dataclass(frozen=True)
class AuditFinding:
    doc_id: str; severity: str; code: str; message: str
    def to_dict(self) -> dict: return asdict(self)
def iter_docs(payload: dict) -> Iterable[dict]:
    if 'documents' in payload: yield from payload.get('documents') or []
    elif 'rows' in payload:
        for row in payload.get('rows') or []:
            if isinstance(row, dict) and isinstance(row.get('doc'), dict): yield row['doc']
    elif isinstance(payload, dict): yield payload
def audit_docs(docs: Iterable[dict], *, max_attachment_bytes: int=8000000) -> List[AuditFinding]:
    findings=[]
    for doc in docs:
        doc_id=str(doc.get('_id') or doc.get('id') or '<unknown>'); blob=json.dumps(doc, ensure_ascii=False)
        if CONFLICT_RE.search(blob): findings.append(AuditFinding(doc_id,'high','conflict_marker','Document contains conflict markers or conflict metadata'))
        if doc.get('_deleted') and doc.get('_attachments'): findings.append(AuditFinding(doc_id,'medium','deleted_with_attachments','Deleted document still carries attachments'))
        total=sum(int(meta.get('length') or 0) for meta in (doc.get('_attachments') or {}).values() if isinstance(meta, dict))
        if total > max_attachment_bytes: findings.append(AuditFinding(doc_id,'medium','large_attachment',f'Attachment bytes exceed limit: {total}'))
        if doc_id.startswith('h:') and not any(k in doc for k in ('_rev','updated','mtime')): findings.append(AuditFinding(doc_id,'low','missing_freshness_marker','Note document has no freshness marker'))
    return findings
def audit_file(path: str | Path) -> List[AuditFinding]: return audit_docs(iter_docs(json.loads(Path(path).read_text(encoding='utf-8'))))
def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('json_file'); args=parser.parse_args(); findings=audit_file(args.json_file)
    print(json.dumps([f.to_dict() for f in findings], ensure_ascii=False, indent=2)); return 1 if any(f.severity == 'high' for f in findings) else 0
if __name__ == '__main__': raise SystemExit(main())
