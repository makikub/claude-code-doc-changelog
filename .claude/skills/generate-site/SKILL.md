---
name: generate-site
description: 静的チェンジログサイトをローカル生成してプレビューする。テンプレートやCSS変更の確認に使用。
---

## Instructions

1. venvが有効か確認し、必要に応じてアクティベートする
2. `python -m scripts.site_generator` を実行してサイトを生成する
3. 生成結果を `site/` ディレクトリで確認する
4. エラーがあれば原因を特定して報告する

## Notes

- `site/` はgitignore対象のため、コミットされない
- 生成にはchangelog/entries.jsonとtemplates/が必要
- entries.jsonが空の場合、意味のあるサイトは生成されない
