"""Configuration constants for the documentation changelog tracker."""

from pathlib import Path

# Project root (one level up from scripts/)
ROOT_DIR = Path(__file__).resolve().parent.parent

# URLs
LLMS_TXT_URL = "https://code.claude.com/docs/llms.txt"
BASE_URL = "https://code.claude.com"

# Directories
SNAPSHOTS_DIR = ROOT_DIR / "snapshots"
CHANGELOG_FILE = ROOT_DIR / "changelog" / "entries.json"
SITE_DIR = ROOT_DIR / "site"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Fetch settings
FETCH_DELAY = 0.3  # seconds between request starts
MAX_CONCURRENT = 5  # max parallel requests
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # base seconds for exponential backoff
REQUEST_TIMEOUT = 30.0  # seconds

USER_AGENT = (
    "claude-code-doc-log/1.0 "
    "(https://github.com/masakikubota/claude-code-doc-log; "
    "documentation changelog tracker)"
)

# Diff display
LARGE_DIFF_THRESHOLD = 100  # lines; diffs larger than this are collapsed
