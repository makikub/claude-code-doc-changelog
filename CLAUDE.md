# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code ドキュメントサイト (code.claude.com/docs/en/) の変更を毎日追跡し、静的HTMLチェンジログサイトを生成するPythonツール。

## Commands

```bash
# セットアップ
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# ドキュメント取得＆差分検出
python scripts/fetch.py

# 静的サイト生成
python -m scripts.site_generator
```

## Architecture

- `scripts/fetch.py` — メインオーケストレーター（取得→差分→changelog追記→snapshot更新）
- `scripts/extract.py` — llms.txt解析、HTMLスクレイピング、Markdown変換
- `scripts/diff_engine.py` — unified diff生成、変更セクション検出
- `scripts/site_generator.py` — Jinja2テンプレートで静的HTML生成
- `scripts/config.py` — 全定数（URL、ディレクトリパス、fetch設定）

## Important: Git-Tracked Data Files

`snapshots/*.md` と `changelog/entries.json` は **Gitで追跡されるデータファイル**。手動編集は避け、`fetch.py` 経由で更新する。`site/` は生成物のためgitignore対象。

## Scraping Fragility

- ページ一覧は `code.claude.com/docs/llms.txt` に依存。フォーマット変更で破損する
- HTML抽出は特定CSSクラス (`mdx-content`, `text-lg prose`) に依存。サイトリデザインで破損する
- Cloudflareメール保護リンクは `(email-protected)` に正規化される

## CI/CD

GitHub Actionsで毎日09:00 UTC自動実行。スケジュール実行時のみfetch、push時はサイト再生成＋GitHub Pagesデプロイ。

## Code Style

- Python 3.12、型ヒント使用（`from __future__ import annotations`）
- async/await + httpx.AsyncClient でHTTP並行処理
- ruff でフォーマット・リント（PostToolUseフックで自動実行）
