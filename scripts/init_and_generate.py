#!/usr/bin/env python3
"""
Neverend — Auto-initialize CouchDB and generate Obsidian LiveSync Setup URI.
Runs once on first docker compose up.
"""

import json
import os
import sys
import time
import base64
import hashlib
import secrets
import string
import urllib.request
import urllib.parse
import urllib.error

# ── Config ──────────────────────────────────────────────────────────────
COUCHDB_HOST = os.environ.get("COUCHDB_HOST", "http://couchdb:5984")
COUCHDB_USER = os.environ.get("COUCHDB_USER", "admin")
COUCHDB_PASSWORD = os.environ.get("COUCHDB_PASSWORD", "changeme")
COUCHDB_DBNAME = os.environ.get("COUCHDB_DBNAME", "obsidian-livesync")
DOMAIN = os.environ.get("DOMAIN", "localhost")
E2EE_PASSPHRASE = os.environ.get("E2EE_PASSPHRASE", "")
NEVEREND_USER = os.environ.get("NEVEREND_USER", "user")
NEVEREND_PASSWORD = os.environ.get("NEVEREND_PASSWORD", "password")

AUTH = base64.b64encode(f"{COUCHDB_USER}:{COUCHDB_PASSWORD}".encode()).decode()


def couch_request(method, path, data=None):
    """Make an authenticated request to CouchDB."""
    url = f"{COUCHDB_HOST}{path}"
    headers = {
        "Authorization": f"Basic {AUTH}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()) if resp.read() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 409:  # Conflict (already exists)
            return {"ok": True, "note": "already exists"}
        print(f"  HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def wait_for_couchdb():
    """Wait until CouchDB is responsive."""
    print("⏳ Waiting for CouchDB...")
    for i in range(60):
        try:
            req = urllib.request.Request(
                f"{COUCHDB_HOST}/_up",
                headers={"Authorization": f"Basic {AUTH}"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ok":
                    print("✅ CouchDB is ready")
                    return True
        except:
            pass
        time.sleep(2)
    print("❌ CouchDB did not start in time")
    return False


def setup_single_node():
    """Configure CouchDB as single node."""
    print("🔧 Configuring single node...")
    result = couch_request("POST", "/_cluster_setup", {
        "action": "enable_single_node",
        "username": COUCHDB_USER,
        "password": COUCHDB_PASSWORD,
        "bind_address": "0.0.0.0",
        "port": 5984,
        "singlenode": True,
    })
    if result:
        print("✅ Single node configured")


def configure_couchdb():
    """Apply LiveSync-required configuration."""
    print("🔧 Applying LiveSync configuration...")
    configs = [
        ("chttpd/require_valid_user", "true"),
        ("chttpd_auth/require_valid_user", "true"),
        ("httpd/WWW-Authenticate", 'Basic realm="couchdb"'),
        ("httpd/enable_cors", "true"),
        ("chttpd/enable_cors", "true"),
        ("chttpd/max_http_request_size", "4294967296"),
        ("couchdb/max_document_size", "50000000"),
        ("cors/credentials", "true"),
        ("cors/origins", "app://obsidian.md,capacitor://localhost,http://localhost"),
        ("cors/headers", "accept, authorization, content-type, origin, referer"),
        ("cors/methods", "GET, PUT, POST, HEAD, DELETE"),
        ("cors/max_age", "3600"),
    ]
    for key, value in configs:
        couch_request("PUT", f"/_node/_local/_config/{key}", value)
    print("✅ LiveSync configuration applied")


def create_database():
    """Create the sync database."""
    print(f"📦 Creating database '{COUCHDB_DBNAME}'...")
    result = couch_request("PUT", f"/{COUCHDB_DBNAME}")
    if result:
        print(f"✅ Database '{COUCHDB_DBNAME}' ready")


def create_user():
    """Create a CouchDB user for LiveSync (not admin)."""
    print(f"👤 Creating user '{NEVEREND_USER}'...")
    # Create user document in _users database
    user_doc = {
        "_id": f"org.couchdb.user:{NEVEREND_USER}",
        "name": NEVEREND_USER,
        "password": NEVEREND_PASSWORD,
        "roles": [],
        "type": "user",
    }
    # Ensure _users database exists
    couch_request("PUT", "/_users")
    result = couch_request("PUT", f"/_users/org.couchdb.user:{NEVEREND_USER}", user_doc)
    if result:
        print(f"✅ User '{NEVEREND_USER}' created")

    # Grant read/write access to the sync database
    # Set security on the database
    security_doc = {
        "admins": {"names": [COUCHDB_USER], "roles": []},
        "members": {"names": [NEVEREND_USER], "roles": []},
    }
    couch_request("PUT", f"/{COUCHDB_DBNAME}/_security", security_doc)
    print(f"✅ User '{NEVEREND_USER}' granted access to '{COUCHDB_DBNAME}'")


def generate_passphrase():
    """Generate a friendly passphrase like the original (adjective-noun)."""
    adjectives = [
        "autumn", "hidden", "bitter", "misty", "silent", "empty", "dry", "dark",
        "summer", "icy", "delicate", "quiet", "white", "cool", "spring", "winter",
        "patient", "twilight", "dawn", "crimson", "wispy", "weathered", "blue",
        "broken", "cold", "damp", "falling", "frosty", "green", "long", "late",
        "bold", "little", "morning", "old", "red", "rough", "still", "small",
        "sparkling", "shy", "wandering", "wild", "black", "young", "holy",
        "solitary", "fragrant", "aged", "snowy", "proud", "floral", "restless",
        "divine", "polished", "ancient", "purple", "lively", "nameless",
    ]
    nouns = [
        "waterfall", "river", "breeze", "moon", "rain", "wind", "sea", "morning",
        "snow", "lake", "sunset", "pine", "shadow", "leaf", "dawn", "glitter",
        "forest", "hill", "cloud", "meadow", "sun", "glade", "bird", "brook",
        "butterfly", "bush", "dew", "dust", "field", "fire", "flower", "firefly",
        "feather", "grass", "haze", "mountain", "night", "pond", "darkness",
        "snowflake", "silence", "sound", "sky", "shape", "surf", "thunder",
        "violet", "water", "wildflower", "wave", "resonance", "log", "dream",
        "cherry", "tree", "fog", "frost", "voice", "paper", "frog", "smoke", "star",
    ]
    return f"{secrets.choice(adjectives)}-{secrets.choice(nouns)}"


def encrypt_setup_config(config: dict, passphrase: str) -> str:
    """
    Encrypt LiveSync config for Setup URI.
    Uses PBKDF2-SHA256 + AES-256-GCM for AES-256 encryption.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes

        # Generate random salt and IV
        salt = secrets.token_bytes(16)
        iv = secrets.token_bytes(12)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(passphrase.encode("utf-8"))

        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        plaintext = json.dumps(config).encode("utf-8")
        ciphertext = aesgcm.encrypt(iv, plaintext, None)

        # Format: salt(16) + iv(12) + ciphertext+tag
        encrypted = salt + iv + ciphertext
        return base64.b64encode(encrypted).decode("ascii")

    except ImportError:
        # Fallback: use openssl subprocess
        import subprocess
        import tempfile

        salt_hex = secrets.token_hex(16)
        iv_hex = secrets.token_hex(12)
        plaintext = json.dumps(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(plaintext)
            input_file = f.name

        try:
            result = subprocess.run(
                [
                    "openssl", "enc", "-aes-256-gcm",
                    "-salt", "-pbkdf2", "-iter", "100000",
                    "-pass", f"pass:{passphrase}",
                    "-in", input_file,
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return base64.b64encode(result.stdout.encode("latin-1")).decode("ascii")
        finally:
            os.unlink(input_file)

        # Last resort: base64 encoding (not encrypted, but functional)
        print("⚠️  No encryption available, using base64 encoding")
        return base64.b64encode(json.dumps(config).encode()).decode("ascii")


def generate_setup_uri():
    """Generate the obsidian://setuplivesync URI."""
    # Determine the server URL
    if DOMAIN == "localhost":
        server_url = f"http://localhost:5984"
    else:
        server_url = f"https://{DOMAIN}"

    e2ee_passphrase = E2EE_PASSPHRASE or generate_passphrase()
    uri_passphrase = generate_passphrase()

    config = {
        "couchDB_URI": server_url,
        "couchDB_USER": NEVEREND_USER,
        "couchDB_PASSWORD": NEVEREND_PASSWORD,
        "couchDB_DBNAME": COUCHDB_DBNAME,
        "syncOnStart": True,
        "gcDelay": 0,
        "periodicReplication": True,
        "syncOnFileOpen": True,
        "encrypt": bool(E2EE_PASSPHRASE or True),
        "passphrase": e2ee_passphrase,
        "usePathObfuscation": True,
        "batchSave": True,
        "batch_size": 50,
        "batches_limit": 50,
        "useHistory": True,
        "disableRequestURI": True,
        "customChunkSize": 50,
        "syncAfterMerge": False,
        "concurrencyOfReadChunksOnline": 100,
        "minimumIntervalOfReadChunksOnline": 100,
        "handleFilenameCaseSensitive": False,
        "doNotUseFixedRevisionForChunks": False,
        "settingVersion": 10,
        "notifyThresholdOfRemoteStorageSize": 800,
    }

    encrypted = encrypt_setup_config(config, uri_passphrase)
    setup_uri = f"obsidian://setuplivesync?settings={urllib.parse.quote(encrypted)}"

    return setup_uri, uri_passphrase, e2ee_passphrase


def print_banner(uri, uri_pass, e2ee_pass):
    """Print the final setup instructions."""
    print()
    print("=" * 60)
    print("  🔄 无限循环 Neverend — 部署完成！")
    print("=" * 60)
    print()
    print("📋 在 Obsidian 中使用：")
    print("   1. 安装插件：搜索 'Self-hosted LiveSync'")
    print("   2. 打开命令面板（Ctrl/Cmd+P）")
    print("   3. 输入 'Use the copied setup URI'")
    print("   4. 粘贴下面的 URI")
    print()
    print(f"🔗 Setup URI（已复制到剪贴板，或手动复制）：")
    print()
    print(uri)
    print()
    print(f"🔑 Setup URI 口令：{uri_pass}")
    print(f"🔐 端到端加密口令：{e2ee_pass}")
    print()
    print("⚠️  请妥善保存以上口令！它们不会再次显示。")
    print()
    if DOMAIN != "localhost":
        print(f"🌐 服务器地址：https://{DOMAIN}")
    else:
        print(f"🌐 服务器地址：http://localhost:5984（仅限本机）")
        print("   如需手机访问，请配置域名并修改 .env 中的 DOMAIN")
    print()
    print("=" * 60)


def main():
    print()
    print("🔄 无限循环 Neverend — 初始化开始")
    print(f"   CouchDB: {COUCHDB_HOST}")
    print(f"   Domain:  {DOMAIN}")
    print(f"   DB:      {COUCHDB_DBNAME}")
    print()

    # Step 1: Wait for CouchDB
    if not wait_for_couchdb():
        sys.exit(1)

    # Step 2: Check if already initialized
    existing = couch_request("GET", f"/{COUCHDB_DBNAME}")
    if existing and "db_name" in existing:
        print(f"ℹ️  Database '{COUCHDB_DBNAME}' already exists, skipping init")
    else:
        # Step 3: Setup single node
        setup_single_node()

        # Step 4: Configure CouchDB
        configure_couchdb()

        # Step 5: Create database
        create_database()

        # Step 6: Create user
        create_user()

    # Step 7: Generate Setup URI
    print("🔑 Generating Setup URI...")
    uri, uri_pass, e2ee_pass = generate_setup_uri()

    # Step 8: Print results
    print_banner(uri, uri_pass, e2ee_pass)

    # Save to file for later reference
    with open("/tmp/neverend-setup.txt", "w") as f:
        f.write(f"Setup URI: {uri}\n")
        f.write(f"URI Passphrase: {uri_pass}\n")
        f.write(f"E2EE Passphrase: {e2ee_pass}\n")
        f.write(f"Server: {'https://' + DOMAIN if DOMAIN != 'localhost' else 'http://localhost:5984'}\n")
        f.write(f"User: {NEVEREND_USER}\n")
        f.write(f"Password: {NEVEREND_PASSWORD}\n")

    print("📄 配置已保存到 /tmp/neverend-setup.txt")


if __name__ == "__main__":
    main()
