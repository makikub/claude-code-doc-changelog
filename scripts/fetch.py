"""Main orchestrator: fetch docs, detect changes, update changelog, generate site."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone

import httpx

from scripts.config import CHANGELOG_FILE, REQUEST_TIMEOUT, SNAPSHOTS_DIR, USER_AGENT
from scripts.diff_engine import compute_diff, compute_summary, detect_change_type
from scripts.extract import PageInfo, fetch_all_pages, fetch_page_list
from scripts.site_generator import generate_site, load_changelog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def read_snapshot(slug: str) -> str | None:
    """Read the previous snapshot for a page, or None if it doesn't exist."""
    path = SNAPSHOTS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    return path.read_text()


def write_snapshot(slug: str, content: str) -> None:
    """Write the current content as a snapshot."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOTS_DIR / f"{slug}.md").write_text(content)


def delete_snapshot(slug: str) -> None:
    """Delete a snapshot file."""
    path = SNAPSHOTS_DIR / f"{slug}.md"
    if path.exists():
        path.unlink()


def save_changelog(entries: list[dict]) -> None:
    """Save changelog entries to JSON."""
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHANGELOG_FILE, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def find_existing_snapshot_slugs() -> set[str]:
    """Find all existing snapshot slugs."""
    if not SNAPSHOTS_DIR.exists():
        return set()
    return {p.stem for p in SNAPSHOTS_DIR.glob("*.md")}


async def run() -> int:
    """Main entry point. Returns the number of changes detected."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Starting documentation check for %s", today)

    # 1. Fetch page list from llms.txt
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        pages = await fetch_page_list(client)

    logger.info("Found %d English documentation pages", len(pages))

    if not pages:
        logger.error("No pages found in llms.txt - aborting")
        return -1

    # Build slug -> PageInfo lookup
    page_map: dict[str, PageInfo] = {p.slug: p for p in pages}

    # 2. Fetch all page contents
    contents = await fetch_all_pages(pages)
    logger.info("Successfully fetched %d/%d pages", len(contents), len(pages))

    # 3. Compare with snapshots and build changelog entries
    new_entries: list[dict] = []
    existing_slugs = find_existing_snapshot_slugs()
    current_slugs = set(contents.keys())

    # Check for modified and added pages
    for slug, new_content in sorted(contents.items()):
        old_content = read_snapshot(slug)
        page_info = page_map[slug]

        if old_content == new_content:
            continue  # No change

        change_type = detect_change_type(old_content, new_content)
        diff = compute_diff(old_content, new_content, slug)
        summary = compute_summary(old_content, new_content)

        new_entries.append({
            "date": today,
            "slug": slug,
            "title": page_info.title,
            "change_type": change_type,
            "summary": {
                "lines_added": summary.lines_added,
                "lines_removed": summary.lines_removed,
                "sections_changed": summary.sections_changed,
            },
            "diff": diff,
        })

        write_snapshot(slug, new_content)
        logger.info("  %s: %s (+%d/-%d)", change_type.upper(), slug,
                     summary.lines_added, summary.lines_removed)

    # 4. Check for removed pages
    removed_slugs = existing_slugs - current_slugs
    for slug in sorted(removed_slugs):
        old_content = read_snapshot(slug)
        diff = compute_diff(old_content, None, slug)
        summary = compute_summary(old_content, None)

        new_entries.append({
            "date": today,
            "slug": slug,
            "title": slug,  # No title available for removed pages
            "change_type": "removed",
            "summary": {
                "lines_added": 0,
                "lines_removed": summary.lines_removed,
                "sections_changed": [],
            },
            "diff": diff,
        })

        delete_snapshot(slug)
        logger.info("  REMOVED: %s", slug)

    # 5. Update changelog and generate site
    if new_entries:
        all_entries = load_changelog()
        all_entries.extend(new_entries)
        save_changelog(all_entries)
        logger.info("Added %d changelog entries", len(new_entries))

    # Always regenerate site (handles template changes even without new data)
    generate_site()

    # Summary
    if new_entries:
        added = sum(1 for e in new_entries if e["change_type"] == "added")
        modified = sum(1 for e in new_entries if e["change_type"] == "modified")
        removed = sum(1 for e in new_entries if e["change_type"] == "removed")
        parts = []
        if added:
            parts.append(f"{added} added")
        if modified:
            parts.append(f"{modified} modified")
        if removed:
            parts.append(f"{removed} removed")
        logger.info("%s: %d changes (%s)", today, len(new_entries), ", ".join(parts))
    else:
        logger.info("%s: No changes detected", today)

    return len(new_entries)


def main() -> None:
    result = asyncio.run(run())
    sys.exit(1 if result < 0 else 0)


if __name__ == "__main__":
    main()
