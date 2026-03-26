"""Generate static HTML site from changelog entries."""

import json
import logging
import shutil
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader

from scripts.config import CHANGELOG_FILE, LARGE_DIFF_THRESHOLD, SITE_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)


def load_changelog() -> list[dict]:
    """Load changelog entries from JSON file."""
    if not CHANGELOG_FILE.exists():
        return []
    with open(CHANGELOG_FILE) as f:
        return json.load(f)


def _group_by_date(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by date, sorted most recent first."""
    by_date: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_date[entry["date"]].append(entry)
    return dict(sorted(by_date.items(), reverse=True))


def _group_by_page(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by page slug, entries sorted most recent first."""
    by_page: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_page[entry["slug"]].append(entry)
    # Sort entries within each page by date descending
    for slug in by_page:
        by_page[slug].sort(key=lambda e: e["date"], reverse=True)
    return dict(sorted(by_page.items()))


def _diff_line_count(diff_text: str) -> int:
    """Count the number of lines in a diff."""
    return len(diff_text.splitlines())


def generate_site() -> None:
    """Generate the complete static site from changelog entries."""
    entries = load_changelog()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["root_prefix"] = ""
    env.globals["large_diff_threshold"] = LARGE_DIFF_THRESHOLD
    env.globals["diff_line_count"] = _diff_line_count

    # Prepare output directory
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)
    (SITE_DIR / "changes").mkdir()
    (SITE_DIR / "pages").mkdir()

    by_date = _group_by_date(entries)
    by_page = _group_by_page(entries)

    # Collect all known page titles (slug -> latest title)
    page_titles: dict[str, str] = {}
    for entry in entries:
        page_titles[entry["slug"]] = entry["title"]

    _generate_index(env, by_date)
    _generate_daily_pages(env, by_date)
    _generate_page_histories(env, by_page, page_titles)
    _generate_css()

    logger.info(
        "Site generated: %d dates, %d pages, %d total entries",
        len(by_date), len(by_page), len(entries),
    )


def _generate_index(env: Environment, by_date: dict[str, list[dict]]) -> None:
    """Generate the index page."""
    template = env.get_template("index.html")

    # Build summary for each date
    date_summaries = []
    for date, day_entries in by_date.items():
        counts = defaultdict(int)
        for e in day_entries:
            counts[e["change_type"]] += 1
        date_summaries.append({
            "date": date,
            "entries": day_entries,
            "total": len(day_entries),
            "added": counts.get("added", 0),
            "modified": counts.get("modified", 0),
            "removed": counts.get("removed", 0),
        })

    html = template.render(date_summaries=date_summaries)
    (SITE_DIR / "index.html").write_text(html)


def _generate_daily_pages(env: Environment, by_date: dict[str, list[dict]]) -> None:
    """Generate one HTML page per date."""
    template = env.get_template("daily.html")
    dates = sorted(by_date.keys(), reverse=True)

    for i, date in enumerate(dates):
        prev_date = dates[i + 1] if i + 1 < len(dates) else None
        next_date = dates[i - 1] if i > 0 else None
        html = template.render(
            date=date,
            entries=by_date[date],
            prev_date=prev_date,
            next_date=next_date,
        )
        (SITE_DIR / "changes" / f"{date}.html").write_text(html)


def _generate_page_histories(
    env: Environment,
    by_page: dict[str, list[dict]],
    page_titles: dict[str, str],
) -> None:
    """Generate one HTML page per documentation page."""
    template = env.get_template("page_history.html")
    slugs = sorted(by_page.keys())

    for slug in slugs:
        title = page_titles.get(slug, slug)
        html = template.render(
            slug=slug,
            title=title,
            entries=by_page[slug],
        )
        (SITE_DIR / "pages" / f"{slug}.html").write_text(html)


def _generate_css() -> None:
    """Write the stylesheet."""
    css = _get_css()
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "style.css").write_text(css)


def _get_css() -> str:
    return """\
:root {
  --bg: #ffffff;
  --bg-secondary: #f6f8fa;
  --text: #1f2328;
  --text-secondary: #656d76;
  --border: #d0d7de;
  --accent: #0969da;
  --added-bg: #dafbe1;
  --added-text: #1a7f37;
  --removed-bg: #ffebe9;
  --removed-text: #cf222e;
  --modified-bg: #ddf4ff;
  --modified-text: #0969da;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117;
    --bg-secondary: #161b22;
    --text: #e6edf3;
    --text-secondary: #7d8590;
    --border: #30363d;
    --accent: #58a6ff;
    --added-bg: #12261e;
    --added-text: #3fb950;
    --removed-bg: #2d1215;
    --removed-text: #f85149;
    --modified-bg: #0c2d6b;
    --modified-text: #58a6ff;
  }
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  color: var(--text);
  background: var(--bg);
  line-height: 1.6;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

header {
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

header h1 a {
  color: var(--text);
  text-decoration: none;
}

header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

nav {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

nav a {
  color: var(--accent);
  text-decoration: none;
  margin-right: 1rem;
}

nav a:hover { text-decoration: underline; }

h2 {
  font-size: 1.25rem;
  margin: 1.5rem 0 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border);
}

a { color: var(--accent); }

.date-group {
  margin-bottom: 2rem;
}

.date-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.date-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
}

.date-header .count {
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
}

.badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.badge-added { background: var(--added-bg); color: var(--added-text); }
.badge-modified { background: var(--modified-bg); color: var(--modified-text); }
.badge-removed { background: var(--removed-bg); color: var(--removed-text); }

.entry {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}

.entry:last-child { border-bottom: none; }

.entry-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.entry-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.entry-meta {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.diff-container {
  margin-top: 0.75rem;
}

details summary {
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

details summary:hover { text-decoration: underline; }

/* Override diff2html for consistency */
.d2h-wrapper { font-size: 0.8rem; }
.d2h-file-header { display: none; }

/* diff2html dark mode overrides */
@media (prefers-color-scheme: dark) {
  .d2h-file-wrapper {
    background: var(--bg-secondary);
    border-color: var(--border);
    color: var(--text);
  }

  .d2h-file-diff {
    background: var(--bg-secondary);
  }

  .d2h-code-line,
  .d2h-code-side-line {
    background: var(--bg-secondary);
    color: var(--text);
  }

  .d2h-code-line-ctn {
    color: var(--text);
  }

  .d2h-ins {
    background: var(--added-bg);
    border-color: #1b4721;
  }

  .d2h-ins .d2h-code-line-ctn {
    color: var(--text);
  }

  .d2h-ins .d2h-code-line-prefix {
    color: var(--added-text);
  }

  .d2h-ins ins,
  .d2h-code-line-ctn ins {
    background: rgba(63, 185, 80, 0.3);
    text-decoration: none;
  }

  .d2h-del {
    background: var(--removed-bg);
    border-color: #6e3630;
  }

  .d2h-del .d2h-code-line-ctn {
    color: var(--text);
  }

  .d2h-del .d2h-code-line-prefix {
    color: var(--removed-text);
  }

  .d2h-del del,
  .d2h-code-line-ctn del {
    background: rgba(248, 81, 73, 0.3);
    text-decoration: none;
  }

  .d2h-info {
    background: #1c2128;
    color: var(--text-secondary);
    border-color: var(--border);
  }

  .d2h-code-linenumber {
    background: var(--bg-secondary);
    color: var(--text-secondary);
    border-color: var(--border);
  }

  .d2h-ins .d2h-code-linenumber {
    background: var(--added-bg);
    color: var(--text-secondary);
    border-color: #1b4721;
  }

  .d2h-del .d2h-code-linenumber {
    background: var(--removed-bg);
    color: var(--text-secondary);
    border-color: #6e3630;
  }

  .d2h-tag {
    background: var(--bg);
    color: var(--text-secondary);
    border-color: var(--border);
  }

  .d2h-emptyplaceholder {
    background: #1c2128;
    border-color: var(--border);
  }
}

.pagination {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-secondary);
}

footer {
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* ===== Mobile diff visibility fixes ===== */
@media (max-width: 768px) {
  .d2h-code-linenumber {
    display: none !important;
  }

  .d2h-code-wrapper *,
  .d2h-diff-table * {
    position: static !important;
    left: auto !important;
  }

  .d2h-wrapper {
    font-size: 0.72rem;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .d2h-file-wrapper {
    border-left: none;
    border-right: none;
    border-radius: 0;
  }

  .d2h-code-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .d2h-diff-table {
    width: 100%;
    table-layout: auto;
  }

  .d2h-code-line-ctn {
    white-space: pre-wrap;
    word-break: break-all;
    overflow-wrap: break-word;
  }

  .d2h-ins {
    background-color: #c6efce !important;
    border-color: #6cc070 !important;
  }

  .d2h-ins .d2h-code-line-ctn {
    background-color: #c6efce !important;
    border-left: 3px solid var(--added-text);
    padding-left: 4px;
  }

  .d2h-del {
    background-color: #ffc7ce !important;
    border-color: #e06c75 !important;
  }

  .d2h-del .d2h-code-line-ctn {
    background-color: #ffc7ce !important;
    border-left: 3px solid var(--removed-text);
    padding-left: 4px;
  }

  .d2h-ins ins,
  .d2h-code-line-ctn ins {
    background-color: rgba(40, 167, 69, 0.4) !important;
    text-decoration: none;
  }

  .d2h-del del,
  .d2h-code-line-ctn del {
    background-color: rgba(220, 53, 69, 0.35) !important;
    text-decoration: none;
  }

  .diff-container {
    margin-top: 0.5rem;
  }
}

/* ===== Mobile + dark mode combined ===== */
@media (max-width: 768px) and (prefers-color-scheme: dark) {
  .d2h-ins {
    background-color: #1a3a2a !important;
    border-color: #2d6a4f !important;
  }

  .d2h-ins .d2h-code-line-ctn {
    background-color: #1a3a2a !important;
  }

  .d2h-del {
    background-color: #3d1a1e !important;
    border-color: #8b3a3a !important;
  }

  .d2h-del .d2h-code-line-ctn {
    background-color: #3d1a1e !important;
  }

  .d2h-ins ins,
  .d2h-code-line-ctn ins {
    background-color: rgba(63, 185, 80, 0.45) !important;
  }

  .d2h-del del,
  .d2h-code-line-ctn del {
    background-color: rgba(248, 81, 73, 0.4) !important;
  }
}
"""


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    generate_site()
