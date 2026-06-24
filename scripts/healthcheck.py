#!/usr/bin/env python3
"""
Neverend Health Check — CouchDB + Caddy 健康状态检测。
用于 docker compose 健康检查和手动诊断。
"""

import json
import os
import sys
import urllib.request
import urllib.error

COUCHDB_HOST = os.environ.get("COUCHDB_HOST", "http://localhost:5984")
COUCHDB_USER = os.environ.get("COUCHDB_USER", "admin")
COUCHDB_PASSWORD = os.environ.get("COUCHDB_PASSWORD", "changeme")
COUCHDB_DBNAME = os.environ.get("COUCHDB_DBNAME", "obsidian-livesync")
DOMAIN = os.environ.get("DOMAIN", "localhost")


def check_couchdb():
    """Check CouchDB connectivity and status."""
    auth = f"{COUCHDB_USER}:{COUCHDB_PASSWORD}"
    auth_b64 = __import__("base64").b64encode(auth.encode()).decode()

    results = {}

    # 1. Basic connectivity
    try:
        req = urllib.request.Request(
            f"{COUCHDB_HOST}/_up",
            headers={"Authorization": f"Basic {auth_b64}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            results["connectivity"] = data.get("status") == "ok"
    except Exception as e:
        results["connectivity"] = False
        results["connectivity_error"] = str(e)
        return results

    # 2. Database exists
    try:
        req = urllib.request.Request(
            f"{COUCHDB_HOST}/{COUCHDB_DBNAME}",
            headers={"Authorization": f"Basic {auth_b64}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            results["database"] = data.get("db_name") == COUCHDB_DBNAME
            results["doc_count"] = data.get("doc_count", 0)
            results["db_size"] = data.get("sizes", {}).get("active", 0)
    except Exception as e:
        results["database"] = False
        results["database_error"] = str(e)

    # 3. CORS configuration
    try:
        req = urllib.request.Request(
            f"{COUCHDB_HOST}/_node/_local/_config/httpd/enable_cors",
            headers={"Authorization": f"Basic {auth_b64}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            cors_enabled = json.loads(resp.read()) == "true"
            results["cors"] = cors_enabled
    except Exception:
        results["cors"] = False

    # 4. Replication protocol
    try:
        req = urllib.request.Request(
            f"{COUCHDB_HOST}/",
            headers={"Authorization": f"Basic {auth_b64}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            results["version"] = data.get("version", "unknown")
            results["couchdb"] = "Welcome" in data.get("couchdb", "")
    except Exception:
        results["couchdb"] = False

    return results


def check_ssl():
    """Check if SSL is working (for non-localhost)."""
    if DOMAIN == "localhost":
        return {"ssl": True, "note": "localhost, SSL not required"}

    try:
        req = urllib.request.Request(f"https://{DOMAIN}/_up")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"ssl": True, "status": resp.status}
    except Exception as e:
        return {"ssl": False, "error": str(e)}


def main():
    print("🔄 Neverend 健康检查")
    print("=" * 40)

    # CouchDB
    couch = check_couchdb()
    print(f"\n📦 CouchDB:")
    print(f"  连接: {'✅' if couch.get('connectivity') else '❌'}")
    print(f"  数据库: {'✅' if couch.get('database') else '❌'}")
    print(f"  CORS: {'✅' if couch.get('cors') else '❌'}")
    if "version" in couch:
        print(f"  版本: {couch['version']}")
    if "doc_count" in couch:
        print(f"  文档数: {couch['doc_count']}")
    if "db_size" in couch:
        size_mb = couch["db_size"] / (1024 * 1024)
        print(f"  数据大小: {size_mb:.1f} MB")

    # SSL
    ssl = check_ssl()
    print(f"\n🔒 SSL:")
    print(f"  状态: {'✅' if ssl.get('ssl') else '❌'}")
    if "note" in ssl:
        print(f"  备注: {ssl['note']}")

    # Overall
    all_ok = couch.get("connectivity") and couch.get("database") and couch.get("cors")
    print(f"\n{'=' * 40}")
    print(f"总体状态: {'✅ 正常' if all_ok else '❌ 异常'}")

    if not all_ok:
        print("\n🔧 建议操作:")
        if not couch.get("connectivity"):
            print("  - 检查 CouchDB 容器是否运行: docker compose ps")
            print("  - 查看日志: docker logs neverend-couchdb")
        if not couch.get("database"):
            print("  - 数据库未创建，运行: docker compose restart init")
        if not couch.get("cors"):
            print("  - CORS 未配置，检查 conf/local.ini")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
