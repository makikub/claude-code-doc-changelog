"""Compute diffs and summaries between document snapshots."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


@dataclass
class DiffSummary:
    lines_added: int = 0
    lines_removed: int = 0
    sections_changed: list[str] = field(default_factory=list)


def detect_change_type(old_content: str | None, new_content: str | None) -> str:
    """Determine the type of change: 'added', 'removed', or 'modified'."""
    if old_content is None:
        return "added"
    if new_content is None:
        return "removed"
    return "modified"


def compute_diff(
    old_content: str | None,
    new_content: str | None,
    slug: str,
) -> str:
    """Compute a unified diff between old and new content."""
    old_lines = (old_content or "").splitlines(keepends=True)
    new_lines = (new_content or "").splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{slug}.md",
        tofile=f"b/{slug}.md",
    )
    return "".join(diff)


def compute_summary(
    old_content: str | None,
    new_content: str | None,
) -> DiffSummary:
    """Compute summary statistics for a diff."""
    old_lines = (old_content or "").splitlines()
    new_lines = (new_content or "").splitlines()

    # Count added/removed lines from unified diff
    diff = difflib.unified_diff(old_lines, new_lines, n=0)
    added = 0
    removed = 0
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    # Find which sections (## headings) were affected
    sections_changed = _find_changed_sections(old_lines, new_lines)

    return DiffSummary(
        lines_added=added,
        lines_removed=removed,
        sections_changed=sections_changed,
    )


def _find_changed_sections(old_lines: list[str], new_lines: list[str]) -> list[str]:
    """Identify which markdown sections (h2 headings) contain changes."""
    heading_re = re.compile(r"^##\s+(.+)")

    def build_section_map(lines: list[str]) -> list[str]:
        """Map each line index to its parent section heading."""
        sections: list[str] = []
        current_section = "(top)"
        for line in lines:
            m = heading_re.match(line)
            if m:
                current_section = m.group(1).strip()
            sections.append(current_section)
        return sections

    old_section_map = build_section_map(old_lines)
    new_section_map = build_section_map(new_lines)

    # Use difflib to find which line indices actually changed
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    affected = set()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        # Lines removed or replaced from old
        for i in range(i1, i2):
            affected.add(old_section_map[i])
        # Lines added or replaced in new
        for j in range(j1, j2):
            affected.add(new_section_map[j])

    # Remove the generic top-level marker if real sections exist
    if len(affected) > 1:
        affected.discard("(top)")

    return sorted(affected)
