"""Fetch documentation pages and extract clean text content."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import html2text
import httpx
from bs4 import BeautifulSoup

from scripts.config import (
    BASE_URL,
    FETCH_DELAY,
    LLMS_TXT_URL,
    MAX_CONCURRENT,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    slug: str
    title: str
    url: str


def parse_llms_txt(text: str) -> list[PageInfo]:
    """Parse llms.txt to extract page slugs, titles, and URLs.

    Format: - [Title](URL): Description
    We filter to English pages only (/docs/en/ prefix).
    """
    pages = []
    pattern = re.compile(r"^-\s+\[(.+?)\]\((.+?)\)")

    for line in text.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        title, url = m.group(1), m.group(2)

        # Ensure absolute URL
        if url.startswith("/"):
            url = BASE_URL + url

        # Filter to English pages only
        if "/docs/en/" not in url:
            continue

        # Extract slug from URL and normalize
        slug = url.rstrip("/").split("/")[-1]
        if slug.endswith(".md"):
            slug = slug[:-3]

        # Use the HTML page URL (not .md) for proper content extraction
        html_url = url
        if html_url.endswith(".md"):
            html_url = html_url[:-3]

        pages.append(PageInfo(slug=slug, title=title, url=html_url))

    return pages


def _make_html2text() -> html2text.HTML2Text:
    """Create a configured html2text converter."""
    h = html2text.HTML2Text()
    h.body_width = 0  # no line wrapping
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.protect_links = True
    h.unicode_snob = True
    return h


def extract_content(html: str) -> str:
    """Extract main content from an HTML page and convert to markdown text.

    The doc site uses a Tailwind-based layout (no <main>/<article> tags).
    The primary content area has class 'mdx-content', and the lead paragraph
    has class 'prose' with 'text-lg'.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove elements that add noise to diffs
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Remove sidebar, table of contents, and navigation elements
    for selector in [
        {"class_": re.compile(r"sidebar")},
        {"class_": re.compile(r"\btoc\b")},
        {"class_": re.compile(r"nav-tabs")},
        {"class_": re.compile(r"nav-logo")},
        {"class_": re.compile(r"chat-assistant")},
    ]:
        for tag in soup.find_all(**selector):
            tag.decompose()

    parts = []
    converter = _make_html2text()

    # Extract the lead paragraph (intro text above the main content)
    lead = soup.find(class_=re.compile(r"text-lg.*prose"))
    if lead:
        parts.append(converter.handle(str(lead)).strip())

    # Extract the main content area
    mdx = soup.find(class_=re.compile(r"mdx-content"))
    if mdx:
        parts.append(converter.handle(str(mdx)).strip())

    if parts:
        text = "\n\n".join(parts)
    else:
        # Fallback: try <main>, <article>, or body
        main = soup.find("main") or soup.find("article") or soup.find(role="main")
        if main is None:
            main = soup.find("body") or soup
        text = converter.handle(str(main))

    return normalize_content(text)


def normalize_content(text: str) -> str:
    """Normalize content for stable diffing."""
    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Normalize Cloudflare email protection links (hash changes per request)
    text = re.sub(
        r"\(</cdn-cgi/l/email-protection#[0-9a-f]+>\)",
        "(email-protected)",
        text,
    )

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Ensure trailing newline
    return text + "\n"


async def fetch_page_list(client: httpx.AsyncClient) -> list[PageInfo]:
    """Fetch and parse llms.txt to get the list of documentation pages."""
    resp = await client.get(LLMS_TXT_URL)
    resp.raise_for_status()
    return parse_llms_txt(resp.text)


async def fetch_page_content(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> str | None:
    """Fetch a single page and extract its content.

    Returns the extracted text, or None if all retries fail.
    """
    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await asyncio.sleep(FETCH_DELAY)
                resp = await client.get(url)
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", "5"))
                    logger.warning("Rate limited on %s, waiting %.1fs", url, retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                resp.raise_for_status()
                return extract_content(resp.text)
            except httpx.HTTPError as e:
                wait = RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %d/%d failed for %s: %s (retry in %.1fs)",
                    attempt, MAX_RETRIES, url, e, wait,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(wait)

    logger.error("All retries failed for %s", url)
    return None


async def fetch_all_pages(
    pages: list[PageInfo],
) -> dict[str, str]:
    """Fetch all pages concurrently with rate limiting.

    Returns a dict mapping slug -> extracted content.
    Pages that fail to fetch are omitted.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        tasks = [
            asyncio.create_task(fetch_page_content(client, page.url, semaphore))
            for page in pages
        ]
        contents = await asyncio.gather(*tasks)

    results = {}
    for page, content in zip(pages, contents):
        if content is not None:
            results[page.slug] = content

    return results
