# Changelog

All notable changes to `neverend` should be documented in this file.

This repository follows a lightweight Keep-a-Changelog style and semantic versioning where applicable.

## Unreleased

- Governance baseline initialized.

## 1.3.0 - Vault index and link health

- Added `scripts/vault_index.py` for local-first Markdown/Obsidian vault indexing.
- Added SQLite, JSON, and Markdown health report outputs covering wiki links, Markdown links, broken links, orphan notes, tags, and aliases.
- Added tests for link extraction, orphan detection, broken-link reporting, and SQLite persistence.

## 1.2.0 - Knowledge ingestion governance

- Added Wiki ingestion governance reference for semantic classification, dry-run manifests, Markdown normalization, structure health audits, and rollback evidence.
- Expanded Skill triggers and workflow to cover knowledge-base organization beyond Obsidian synchronization.
