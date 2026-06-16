"""Verify relative markdown links under docs/ resolve to existing files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _is_external(link: str) -> bool:
    lowered = link.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or link.startswith("#")
    )


def _target_path(source: Path, link: str) -> Path:
    path_part = link.split("#", 1)[0]
    if not path_part:
        return source
    resolved = (source.parent / path_part).resolve()
    return resolved


def _collect_markdown_files() -> list[Path]:
    files = sorted(DOCS_ROOT.rglob("*.md"))
    index = DOCS_ROOT / "INDEX.md"
    if index not in files:
        files.insert(0, index)
    return files


def check_links() -> list[str]:
    errors: list[str] = []
    for md_file in _collect_markdown_files():
        text = md_file.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            link = match.group(1).strip()
            if not link or _is_external(link):
                continue
            target = _target_path(md_file, link)
            if not target.exists():
                rel_source = md_file.relative_to(REPO_ROOT)
                errors.append(f"{rel_source}: broken link -> {link}")
    return errors


def main() -> int:
    errors = check_links()
    if errors:
        print("Broken documentation links:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print(f"OK: checked links in {len(_collect_markdown_files())} markdown files under docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
