# Claude Code Documentation Changelog

Automated daily tracker for changes to the [Claude Code documentation](https://code.claude.com/docs/en/overview).

## How it works

1. A GitHub Action runs daily at 09:00 UTC
2. It fetches all English documentation pages from `code.claude.com/docs/en/`
3. Compares each page against the previous snapshot
4. If changes are detected, records them with diffs in `changelog/entries.json`
5. Generates a static HTML site and deploys it to GitHub Pages

## Project structure

- `scripts/` — Python scripts for fetching, diffing, and site generation
- `templates/` — Jinja2 HTML templates for the static site
- `snapshots/` — Latest text snapshot of each doc page (git-tracked)
- `changelog/entries.json` — Append-only record of all detected changes

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch.py
```

## License

MIT
