#!/usr/bin/env python3
"""
Neverend Setup Wizard — 交互式配置向导。
引导用户完成 .env 配置，生成 docker-compose 启动命令。
"""

import os
import re
import secrets
import string
import sys
from pathlib import Path


def generate_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_passphrase():
    """Generate a friendly passphrase."""
    adjectives = [
        "autumn", "hidden", "bitter", "misty", "silent", "empty", "dark",
        "summer", "icy", "quiet", "white", "cool", "spring", "patient",
        "twilight", "dawn", "crimson", "blue", "broken", "cold", "frosty",
        "green", "bold", "little", "morning", "old", "red", "wild",
        "ancient", "purple", "lively", "nameless", "solitary", "fragrant",
    ]
    nouns = [
        "waterfall", "river", "breeze", "moon", "rain", "wind", "sea",
        "morning", "snow", "lake", "sunset", "pine", "shadow", "leaf",
        "dawn", "glitter", "forest", "hill", "cloud", "meadow", "sun",
        "bird", "brook", "butterfly", "bush", "dew", "field", "fire",
        "flower", "grass", "haze", "mountain", "night", "pond", "star",
        "sky", "wave", "dream", "cherry", "tree", "fog", "voice",
    ]
    return f"{secrets.choice(adjectives)}-{secrets.choice(nouns)}"


def validate_domain(domain):
    """Validate domain format."""
    if domain == "localhost":
        return True
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    return bool(re.match(pattern, domain))


def prompt_with_default(prompt_text, default, validator=None, error_msg=""):
    """Prompt user with a default value."""
    while True:
        value = input(f"{prompt_text} [{default}]: ").strip()
        if not value:
            value = default
        if validator and not validator(value):
            print(f"  ❌ {error_msg or 'Invalid input'}")
            continue
        return value


def main():
    print()
    print("=" * 50)
    print("  🔄 无限循环 Neverend — 配置向导")
    print("=" * 50)
    print()
    print("本向导将引导你完成 Neverend 的配置。")
    print("配置完成后会生成 .env 文件并启动服务。")
    print()

    # ── Step 1: Domain ──
    print("── Step 1/4: 域名配置 ──")
    print("  手机访问需要域名 + SSL 证书。")
    print("  仅桌面使用可填 localhost。")
    print()
    domain = prompt_with_default(
        "  域名",
        "localhost",
        validator=validate_domain,
        error_msg="域名格式不正确，请使用 example.com 格式或 localhost",
    )

    # ── Step 2: CouchDB credentials ──
    print()
    print("── Step 2/4: CouchDB 管理员账号 ──")
    print("  这是数据库的管理员账号，请牢记。")
    print()
    couch_user = prompt_with_default("  管理员用户名", "admin")
    couch_password = prompt_with_default("  管理员密码", generate_password())

    # ── Step 3: Sync user credentials ──
    print()
    print("── Step 3/4: 同步用户账号 ──")
    print("  这是 Obsidian LiveSync 插件使用的账号。")
    print("  （建议与管理员账号不同，更安全）")
    print()
    sync_user = prompt_with_default("  同步用户名", "obsidian")
    sync_password = prompt_with_default("  同步密码", generate_password())

    # ── Step 4: E2E encryption ──
    print()
    print("── Step 4/4: 端到端加密 ──")
    print("  启用后，笔记在离开设备前会加密。")
    print("  强烈推荐启用。")
    print()
    enable_e2ee = input("  启用端到端加密？(Y/n) [Y]: ").strip().lower()
    e2ee_passphrase = ""
    if enable_e2ee != "n":
        e2ee_passphrase = generate_passphrase()
        print(f"  🔐 已生成加密口令: {e2ee_passphrase}")
        print("  ⚠️  请务必记录此口令！丢失后无法解密笔记。")

    # ── Generate .env ──
    print()
    print("── 生成配置 ──")

    env_content = f"""# 无限循环 Neverend 配置
# 由 setup_wizard.py 生成于 {__import__('datetime').datetime.now().isoformat()}

# 域名
DOMAIN={domain}

# CouchDB 管理员
COUCHDB_USER={couch_user}
COUCHDB_PASSWORD={couch_password}

# 数据库名
COUCHDB_DBNAME=obsidian-livesync

# 端到端加密口令
E2EE_PASSPHRASE={e2ee_passphrase}

# 同步用户
NEVEREND_USER={sync_user}
NEVEREND_PASSWORD={sync_password}
"""

    env_path = Path(__file__).parent.parent / ".env"
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"  ✅ 配置已保存到 {env_path}")

    # ── Summary ──
    print()
    print("=" * 50)
    print("  📋 配置摘要")
    print("=" * 50)
    print(f"  域名:     {domain}")
    print(f"  管理员:   {couch_user}")
    print(f"  同步用户: {sync_user}")
    print(f"  E2E加密:  {'✅ 已启用' if e2ee_passphrase else '❌ 未启用'}")
    if e2ee_passphrase:
        print(f"  加密口令: {e2ee_passphrase}")
    print()

    # ── Next steps ──
    print("── 下一步 ──")
    print()
    print("  1. 启动服务:")
    print("     docker compose up -d")
    print()
    print("  2. 查看 Setup URI:")
    print("     docker logs neverend-init")
    print()
    print("  3. 在 Obsidian 中:")
    print("     - 安装 Self-hosted LiveSync 插件")
    print("     - 命令面板 → 'Use the copied setup URI'")
    print("     - 粘贴 URI → 输入口令 → 完成")
    print()

    # Ask to start
    start = input("  现在启动 docker compose？(y/N) [N]: ").strip().lower()
    if start == "y":
        os.system("cd {} && docker compose up -d".format(
            str(Path(__file__).parent.parent)
        ))
    else:
        print()
        print("  手动启动: cd neverend && docker compose up -d")


if __name__ == "__main__":
    main()
