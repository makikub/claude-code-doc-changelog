"""Generate static HTML site from changelog entries."""

from __future__ import annotations

import json
import logging
import shutil
from collections import defaultdict
from datetime import datetime

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
    for slug in by_page:
        by_page[slug].sort(key=lambda e: e["date"], reverse=True)
    return dict(sorted(by_page.items()))


def _diff_line_count(diff_text: str) -> int:
    """Count the number of lines in a diff."""
    return len(diff_text.splitlines())


def _format_date(date_str: str) -> str:
    """Format ISO date as 'Mar 26, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")


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
    env.filters["format_date"] = _format_date

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

    _generate_index(env, by_date, total_entries=len(entries), total_pages=len(by_page))
    _generate_daily_pages(env, by_date)
    _generate_page_histories(env, by_page, page_titles)
    _generate_pages_index(env, by_page, page_titles)
    _generate_css()

    logger.info(
        "Site generated: %d dates, %d pages, %d total entries",
        len(by_date),
        len(by_page),
        len(entries),
    )


def _generate_index(
    env: Environment,
    by_date: dict[str, list[dict]],
    *,
    total_entries: int,
    total_pages: int,
) -> None:
    """Generate the index page."""
    template = env.get_template("index.html")

    date_summaries = []
    for date, day_entries in by_date.items():
        counts = defaultdict(int)
        for e in day_entries:
            counts[e["change_type"]] += 1
        date_summaries.append(
            {
                "date": date,
                "entries": day_entries,
                "total": len(day_entries),
                "added": counts.get("added", 0),
                "modified": counts.get("modified", 0),
                "removed": counts.get("removed", 0),
            }
        )

    html = template.render(
        date_summaries=date_summaries,
        total_entries=total_entries,
        total_pages=total_pages,
    )
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


def _generate_pages_index(
    env: Environment,
    by_page: dict[str, list[dict]],
    page_titles: dict[str, str],
) -> None:
    """Generate the pages index listing all tracked documentation pages."""
    template = env.get_template("pages_index.html")

    pages = []
    for slug, page_entries in sorted(by_page.items()):
        title = page_titles.get(slug, slug)
        pages.append(
            {
                "slug": slug,
                "title": title,
                "change_count": len(page_entries),
                "latest_date": page_entries[0]["date"],
            }
        )

    html = template.render(pages=pages)
    (SITE_DIR / "pages" / "index.html").write_text(html)


def _generate_css() -> None:
    """Write the stylesheet."""
    css = _get_css()
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "style.css").write_text(css)


def _get_css() -> str:
    return """\
/* ============================================
   Claude Code Docs Changelog
   Design: Technical Editorial
   ============================================ */

:root {
  --bg: #FAFAF8;
  --bg-secondary: #F2F0ED;
  --bg-elevated: #FFFFFF;
  --text: #1C1917;
  --text-secondary: #78716C;
  --text-tertiary: #A8A29E;
  --border: #E7E5E4;
  --border-strong: #D6D3D1;

  --accent: #C2410C;
  --accent-light: #FFF7ED;
  --accent-hover: #EA580C;

  --added: #16A34A;
  --added-bg: #F0FDF4;
  --added-border: #BBF7D0;
  --modified: #2563EB;
  --modified-bg: #EFF6FF;
  --modified-border: #BFDBFE;
  --removed: #DC2626;
  --removed-bg: #FEF2F2;
  --removed-border: #FECACA;

  --font-display: 'Bricolage Grotesque', Georgia, serif;
  --font-body: 'Figtree', -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0C0A09;
    --bg-secondary: #1C1917;
    --bg-elevated: #292524;
    --text: #FAFAF9;
    --text-secondary: #A8A29E;
    --text-tertiary: #78716C;
    --border: #292524;
    --border-strong: #44403C;
    --accent: #F97316;
    --accent-light: #1C1108;
    --accent-hover: #FB923C;
    --added: #4ADE80;
    --added-bg: #052E16;
    --added-border: #14532D;
    --modified: #60A5FA;
    --modified-bg: #172554;
    --modified-border: #1E3A5F;
    --removed: #F87171;
    --removed-bg: #450A0A;
    --removed-border: #7F1D1D;
  }
}

/* === Reset & Base === */
* { margin: 0; padding: 0; box-sizing: border-box; }

html {
  scroll-padding-top: 5rem;
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-body);
  color: var(--text);
  background: var(--bg);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  color: var(--accent);
  text-decoration: none;
  transition: color 0.15s ease;
}

a:hover { color: var(--accent-hover); }

/* === Header === */
.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}

.site-header::before {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), #F59E0B, var(--accent));
}

.header-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text);
}

.logo:hover { color: var(--text); }

.logo-mark {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}

.logo-text {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header-nav {
  display: flex;
  gap: 0.25rem;
}

.header-nav a {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  transition: all 0.15s ease;
}

.header-nav a:hover {
  color: var(--text);
  background: var(--bg-secondary);
}

.header-nav a.is-active {
  color: var(--accent);
  background: var(--accent-light);
}

.header-nav .nav-external { color: var(--text-tertiary); }

.site-tagline {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  margin-top: 0.125rem;
}

.site-tagline a {
  color: var(--text-secondary);
  text-decoration: underline;
  text-decoration-color: var(--border-strong);
  text-underline-offset: 2px;
}

/* === Container === */
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem 2rem;
}

/* === Stats Bar === */
.stats-bar {
  display: flex;
  gap: 2.5rem;
  padding: 1.5rem 0 1.25rem;
  border-bottom: 1px solid var(--border);
}

.stat-item { display: flex; flex-direction: column; }

.stat-value {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}

/* === Timeline === */
.timeline { padding-top: 1.25rem; }

.timeline-group {
  position: relative;
  border: none;
  background: none;
  animation: fadeInUp 0.3s ease both;
}

.timeline-group:nth-child(1) { animation-delay: 0s; }
.timeline-group:nth-child(2) { animation-delay: 0.04s; }
.timeline-group:nth-child(3) { animation-delay: 0.08s; }
.timeline-group:nth-child(4) { animation-delay: 0.12s; }
.timeline-group:nth-child(5) { animation-delay: 0.16s; }

.timeline-group[open] { margin-bottom: 0.75rem; }

/* Vertical spine */
.timeline-group::before {
  content: '';
  position: absolute;
  left: 0.5rem;
  top: 1.75rem;
  bottom: 0;
  width: 2px;
  background: var(--border);
}

.timeline-group:last-child::before { bottom: 1.75rem; }

/* Date header */
summary.timeline-date {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0;
  cursor: pointer;
  list-style: none;
  user-select: none;
  position: relative;
}

summary.timeline-date::-webkit-details-marker { display: none; }

/* Dot */
summary.timeline-date::before {
  content: '';
  width: 0.6875rem;
  height: 0.6875rem;
  border-radius: 50%;
  background: var(--bg);
  border: 2.5px solid var(--accent);
  flex-shrink: 0;
  z-index: 1;
  transition: all 0.2s ease;
}

.timeline-group[open] > summary.timeline-date::before {
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-light);
}

summary.timeline-date .date-text {
  font-family: var(--font-display);
  font-size: 1.0625rem;
  font-weight: 700;
}

summary.timeline-date .date-text a {
  color: var(--text);
}

summary.timeline-date .date-text a:hover {
  color: var(--accent);
}

summary.timeline-date .change-count {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-weight: 500;
}

summary.timeline-date .date-badges {
  display: flex;
  gap: 0.375rem;
}

summary.timeline-date .date-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.0625rem 0.4375rem;
  border-radius: 2rem;
}

.date-badge-added {
  background: var(--added-bg);
  color: var(--added);
  border: 1px solid var(--added-border);
}

.date-badge-modified {
  background: var(--modified-bg);
  color: var(--modified);
  border: 1px solid var(--modified-border);
}

.date-badge-removed {
  background: var(--removed-bg);
  color: var(--removed);
  border: 1px solid var(--removed-border);
}

summary.timeline-date .expand-icon {
  margin-left: auto;
  font-size: 0.5rem;
  color: var(--text-tertiary);
  transition: transform 0.2s ease;
}

.timeline-group[open] > summary.timeline-date .expand-icon {
  transform: rotate(90deg);
}

.timeline-entries {
  padding-left: 2.25rem;
  padding-bottom: 0.75rem;
}

/* === Entry Card === */
.entry {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  border-left: 3px solid var(--border-strong);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.entry:hover {
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.entry.type-added { border-left-color: var(--added); }
.entry.type-modified { border-left-color: var(--modified); }
.entry.type-removed { border-left-color: var(--removed); }

.entry-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  flex-wrap: wrap;
}

.entry-title {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--text);
}

.entry-title:hover { color: var(--accent); }

.entry-link {
  font-size: 0.75rem;
  margin-left: auto;
  white-space: nowrap;
  color: var(--text-tertiary);
}

.entry-link:hover { color: var(--accent); }

.entry-meta {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-wrap: wrap;
}

.entry-meta .sections-info {
  color: var(--text-tertiary);
  font-size: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

/* === Badge === */
.badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 2rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.badge-added {
  background: var(--added-bg);
  color: var(--added);
  border: 1px solid var(--added-border);
}

.badge-modified {
  background: var(--modified-bg);
  color: var(--modified);
  border: 1px solid var(--modified-border);
}

.badge-removed {
  background: var(--removed-bg);
  color: var(--removed);
  border: 1px solid var(--removed-border);
}

/* === Magnitude Bar === */
.magnitude {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 6px;
}

.mag-added, .mag-removed {
  display: block;
  height: 100%;
  border-radius: 3px;
  min-width: 2px;
  width: clamp(2px, calc(var(--n) * 0.3px), 60px);
}

.mag-added { background: var(--added); opacity: 0.7; }
.mag-removed { background: var(--removed); opacity: 0.7; }

/* === Diff Container === */
.diff-container {
  margin-top: 0.75rem;
  border-radius: 0.5rem;
  overflow: hidden;
}

.diff-container details summary {
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--accent);
  margin-bottom: 0.5rem;
  padding: 0.375rem 0;
}

.diff-container details summary:hover { text-decoration: underline; }

/* diff2html base overrides */
.d2h-wrapper { font-size: 0.8125rem; font-family: var(--font-mono); }
.d2h-file-header { display: none; }

/* diff2html dark mode */
@media (prefers-color-scheme: dark) {
  .d2h-file-wrapper {
    background: var(--bg-secondary);
    border-color: var(--border);
    color: var(--text);
  }

  .d2h-file-diff { background: var(--bg-secondary); }

  .d2h-code-line,
  .d2h-code-side-line {
    background: var(--bg-secondary);
    color: var(--text);
  }

  .d2h-code-line-ctn { color: var(--text); }

  .d2h-ins {
    background: var(--added-bg);
    border-color: var(--added-border);
  }

  .d2h-ins .d2h-code-line-ctn { color: var(--text); }
  .d2h-ins .d2h-code-line-prefix { color: var(--added); }

  .d2h-ins ins,
  .d2h-code-line-ctn ins {
    background: rgba(63, 185, 80, 0.3);
    text-decoration: none;
  }

  .d2h-del {
    background: var(--removed-bg);
    border-color: var(--removed-border);
  }

  .d2h-del .d2h-code-line-ctn { color: var(--text); }
  .d2h-del .d2h-code-line-prefix { color: var(--removed); }

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
    border-color: var(--added-border);
  }

  .d2h-del .d2h-code-linenumber {
    background: var(--removed-bg);
    color: var(--text-secondary);
    border-color: var(--removed-border);
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

/* === Pages Grid === */
.pages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
  padding-top: 1rem;
}

.page-card {
  display: block;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem 1.125rem;
  text-decoration: none;
  transition: all 0.2s ease;
}

.page-card:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}

.page-card-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--text);
  margin-bottom: 0.375rem;
}

.page-card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

/* === Page Header === */
.page-header {
  padding: 1.5rem 0 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.page-header h2 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  border: none;
  margin: 0;
  padding: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.page-breadcrumb {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  margin-bottom: 0.375rem;
}

.page-breadcrumb a { color: var(--text-secondary); }

/* === Daily entries list === */
.daily-entries {
  padding-top: 0.5rem;
}

/* === Pagination === */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.pagination a {
  font-size: 0.8125rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-radius: 0.375rem;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.pagination a:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-light);
}

/* === h2 (standalone) === */
h2 {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  margin: 1.5rem 0 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border);
}

/* === Empty state === */
.empty-state {
  text-align: center;
  padding: 4rem 1rem;
  color: var(--text-secondary);
}

.empty-state h2 {
  font-family: var(--font-display);
  border: none;
}

/* === Footer === */
footer {
  margin-top: 3rem;
  padding: 1.5rem 0;
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-align: center;
}

/* === Back to Top === */
#back-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 1rem;
  cursor: pointer;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

#back-to-top.visible { opacity: 1; visibility: visible; }

#back-to-top:hover {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

@media (prefers-color-scheme: dark) {
  #back-to-top {
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  }
}

/* === Animations === */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* === Mobile === */
@media (max-width: 768px) {
  .header-inner { padding: 0.5rem 1rem; }
  .logo-text { font-size: 0.9375rem; }
  .logo-mark { font-size: 1.25rem; }
  .site-tagline { display: none; }
  .container { padding: 0 1rem 1.5rem; }

  .stats-bar { gap: 1.5rem; padding: 1rem 0; }
  .stat-value { font-size: 1.25rem; }

  .timeline-entries { padding-left: 1.75rem; }

  .entry-meta .sections-info { max-width: 180px; }

  .pages-grid { grid-template-columns: 1fr; }

  .pagination a { padding: 0.375rem 0.625rem; font-size: 0.75rem; }

  #back-to-top {
    bottom: 1.25rem;
    right: 1.25rem;
    width: 2.25rem;
    height: 2.25rem;
    font-size: 0.875rem;
  }

  /* diff2html mobile: convert table to block for full-width usage */
  .d2h-diff-table,
  .d2h-diff-table tbody,
  .d2h-diff-table tr {
    display: block !important;
    width: 100% !important;
  }

  .d2h-diff-table td {
    display: block !important;
    width: 100% !important;
  }

  .d2h-diff-table td.d2h-code-linenumber,
  .d2h-code-linenumber {
    display: none !important;
  }

  .d2h-code-wrapper *,
  .d2h-diff-table * {
    position: static !important;
    left: auto !important;
  }

  .d2h-wrapper {
    font-size: 0.75rem;
    overflow-x: hidden;
  }

  .d2h-file-wrapper {
    border-left: none;
    border-right: none;
    border-radius: 0;
  }

  .d2h-code-wrapper {
    overflow-x: hidden;
  }

  .d2h-code-line {
    display: block !important;
    width: 100% !important;
    white-space: normal;
    padding: 1px 0.625em;
  }

  .d2h-code-line-ctn {
    white-space: pre-wrap;
    overflow-wrap: break-word;
    word-break: normal;
    display: inline;
  }

  .diff-container {
    margin-left: -1rem;
    margin-right: -1rem;
  }

  .d2h-ins {
    background-color: #c6efce !important;
    border-color: #6cc070 !important;
  }

  .d2h-ins .d2h-code-line-ctn {
    background-color: #c6efce !important;
    border-left: 3px solid var(--added);
    padding-left: 4px;
  }

  .d2h-del {
    background-color: #ffc7ce !important;
    border-color: #e06c75 !important;
  }

  .d2h-del .d2h-code-line-ctn {
    background-color: #ffc7ce !important;
    border-left: 3px solid var(--removed);
    padding-left: 4px;
  }

  .d2h-ins ins, .d2h-code-line-ctn ins {
    background-color: rgba(40, 167, 69, 0.4) !important;
    text-decoration: none;
  }

  .d2h-del del, .d2h-code-line-ctn del {
    background-color: rgba(220, 53, 69, 0.35) !important;
    text-decoration: none;
  }
}

/* Mobile dark mode combined */
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

  .d2h-ins ins, .d2h-code-line-ctn ins {
    background-color: rgba(63, 185, 80, 0.45) !important;
  }

  .d2h-del del, .d2h-code-line-ctn del {
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
