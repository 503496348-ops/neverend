#!/usr/bin/env python3
"""
Neverend Backup — CouchDB 数据库备份与恢复。
支持全量备份、增量备份、定时备份。
"""

import json
import os
import sys
import time
import shutil
import tarfile
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

COUCHDB_HOST = os.environ.get("COUCHDB_HOST", "http://localhost:5984")
COUCHDB_USER = os.environ.get("COUCHDB_USER", "admin")
COUCHDB_PASSWORD = os.environ.get("COUCHDB_PASSWORD", "changeme")
COUCHDB_DBNAME = os.environ.get("COUCHDB_DBNAME", "obsidian-livesync")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/backups")


def get_auth():
    import base64
    auth = f"{COUCHDB_USER}:{COUCHDB_PASSWORD}"
    return f"Basic {base64.b64encode(auth.encode()).decode()}"


def couch_get(path):
    """Make a GET request to CouchDB."""
    req = urllib.request.Request(
        f"{COUCHDB_HOST}{path}",
        headers={"Authorization": get_auth()},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def backup_full(output_path=None):
    """
    Full database backup using CouchDB _all_docs + _bulk_docs restore.
    Creates a JSON file with all documents.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_path is None:
        output_path = os.path.join(BACKUP_DIR, f"neverend_backup_{timestamp}.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"📦 Starting full backup of '{COUCHDB_DBNAME}'...")

    # Fetch all documents (including design docs)
    try:
        data = couch_get(f"/{COUCHDB_DBNAME}/_all_docs?include_docs=true")
    except Exception as e:
        print(f"❌ Failed to fetch documents: {e}")
        return None

    docs = [row["doc"] for row in data.get("rows", []) if not row["id"].startswith("_design/")]
    total = len(docs)

    backup_data = {
        "metadata": {
            "database": COUCHDB_DBNAME,
            "timestamp": timestamp,
            "doc_count": total,
            "version": "1.0",
        },
        "documents": docs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Backup complete: {total} documents, {size_mb:.1f} MB")
    print(f"   Saved to: {output_path}")

    return output_path


def backup_incremental(since_seq=None, output_path=None):
    """
    Incremental backup using CouchDB _changes API.
    Only backs up documents changed since the given sequence.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_path is None:
        output_path = os.path.join(BACKUP_DIR, f"neverend_incr_{timestamp}.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    seq_param = f"?since={since_seq}" if since_seq else "?since=0"
    try:
        changes = couch_get(f"/{COUCHDB_DBNAME}/_changes{seq_param}&include_docs=true")
    except Exception as e:
        print(f"❌ Failed to fetch changes: {e}")
        return None

    docs = [row["doc"] for row in changes.get("results", []) if "doc" in row]
    last_seq = changes.get("last_seq", "0")

    backup_data = {
        "metadata": {
            "database": COUCHDB_DBNAME,
            "timestamp": timestamp,
            "since_seq": since_seq,
            "last_seq": last_seq,
            "doc_count": len(docs),
            "type": "incremental",
        },
        "documents": docs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Incremental backup: {len(docs)} changed docs, seq={last_seq}")
    print(f"   Saved to: {output_path}")

    return output_path, last_seq


def restore(backup_path):
    """
    Restore a backup to the database.
    Uses _bulk_docs for efficient insertion.
    """
    print(f"📥 Restoring from {backup_path}...")

    with open(backup_path, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    docs = backup_data.get("documents", [])
    metadata = backup_data.get("metadata", {})
    total = len(docs)

    print(f"   Found {total} documents (backup from {metadata.get('timestamp', 'unknown')})")

    # Remove _rev fields for insertion
    for doc in docs:
        doc.pop("_rev", None)

    # Bulk insert in batches
    batch_size = 100
    inserted = 0
    for i in range(0, total, batch_size):
        batch = docs[i:i + batch_size]
        try:
            req = urllib.request.Request(
                f"{COUCHDB_HOST}/{COUCHDB_DBNAME}/_bulk_docs",
                data=json.dumps({"docs": batch}).encode(),
                headers={
                    "Authorization": get_auth(),
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                success = sum(1 for r in result if "ok" in r and r["ok"])
                inserted += success
        except Exception as e:
            print(f"   ⚠️ Batch {i//batch_size + 1} error: {e}")

    print(f"✅ Restored {inserted}/{total} documents")
    return inserted


def cleanup_old_backups(keep_days=7):
    """Remove backups older than keep_days."""
    if not os.path.exists(BACKUP_DIR):
        return

    cutoff = time.time() - (keep_days * 86400)
    removed = 0

    for f in os.listdir(BACKUP_DIR):
        if not f.startswith("neverend_"):
            continue
        path = os.path.join(BACKUP_DIR, f)
        if os.path.getmtime(path) < cutoff:
            os.remove(path)
            removed += 1

    if removed:
        print(f"🧹 Cleaned up {removed} old backups (>{keep_days} days)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Neverend Backup Tool")
    sub = parser.add_subparsers(dest="command")

    # backup
    backup_p = sub.add_parser("backup", help="Full backup")
    backup_p.add_argument("-o", "--output", help="Output file path")
    backup_p.add_argument("--incr", action="store_true", help="Incremental backup")
    backup_p.add_argument("--since", help="Sequence for incremental backup")

    # restore
    restore_p = sub.add_parser("restore", help="Restore from backup")
    restore_p.add_argument("file", help="Backup file path")

    # cleanup
    cleanup_p = sub.add_parser("cleanup", help="Remove old backups")
    cleanup_p.add_argument("--days", type=int, default=7, help="Keep backups from N days")

    args = parser.parse_args()

    if args.command == "backup":
        if args.incr:
            backup_incremental(args.since, args.output)
        else:
            backup_full(args.output)
    elif args.command == "restore":
        restore(args.file)
    elif args.command == "cleanup":
        cleanup_old_backups(args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
