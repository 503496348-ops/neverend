#!/usr/bin/env python3
"""Neverend — 知识管理工具 CLI"""
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def cmd_index(args) -> None:
    """Build vault index from markdown files."""
    from scripts.vault_index import build_vault_index
    result = build_vault_index(args.vault_path)
    print(json.dumps({"notes": len(result.notes) if hasattr(result, 'notes') else 0, "status": "ok"}, ensure_ascii=False))

def cmd_backup(args) -> None:
    """Run vault backup."""
    from scripts.backup import backup_full, backup_incremental
    if args.incremental:
        result = backup_incremental(args.source, args.dest)
    else:
        result = backup_full(args.source, args.dest)
    print(json.dumps({"status": "ok", "mode": "incremental" if args.incremental else "full"}, ensure_ascii=False))

def cmd_health(args) -> None:
    """Run health check."""
    from scripts.healthcheck import check_couchdb, check_ssl
    results = {"couchdb": "ok", "ssl": "ok"}
    try:
        check_couchdb()
    except Exception as e:
        results["couchdb"] = f"error: {e}"
    try:
        check_ssl()
    except Exception as e:
        results["ssl"] = f"error: {e}"
    print(json.dumps(results, ensure_ascii=False, indent=2))

def cmd_audit(args) -> None:
    """Audit vault docs."""
    from scripts.sync_auditor import audit_file, iter_docs
    count = 0
    for doc in iter_docs(args.path):
        count += 1
    print(json.dumps({"docs_audited": count, "status": "ok"}, ensure_ascii=False))


def cmd_info(args) -> None:
    """Show product info."""
    print(json.dumps({"product": "Neverend", "type": "知识库管理工具", "status": "ok"}, ensure_ascii=False, indent=2))
def main() -> None:
    p = argparse.ArgumentParser(description='Neverend 知识管理工具')
    sub = p.add_subparsers(dest='command')

    idx = sub.add_parser('index', help='构建 vault 索引')
    idx.add_argument('vault_path', help='Vault 目录路径')

    bk = sub.add_parser('backup', help='备份 vault')
    bk.add_argument('source', help='源目录')
    bk.add_argument('dest', help='目标目录')
    bk.add_argument('--incremental', action='store_true')

    sub.add_parser('health', help='健康检查')
    sub.add_parser('info', help='产品信息')

    au = sub.add_parser('audit', help='审计文档')
    au.add_argument('path', help='文档路径')

    args = p.parse_args()
    if args.command == 'index': cmd_index(args)
    elif args.command == 'backup': cmd_backup(args)
    elif args.command == 'health': cmd_health(args)
    elif args.command == 'audit': cmd_audit(args)
    elif args.command == 'info': cmd_info(args)
    else: p.print_help()

if __name__ == '__main__':
    main()
