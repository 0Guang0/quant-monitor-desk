#!/usr/bin/env python3
"""Verify docs/ and specs/ files are indexed in MIGRATION_MAP."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_MAP = REPO_ROOT / "MIGRATION_MAP.md"
DOCS_SPECS_INDEX = REPO_ROOT / "docs/generated/docs_specs_index.generated.md"

# Navigation hubs — listed in INDEX, not required per-file in MIGRATION_MAP body.
WAIVERS = frozenset({"docs/INDEX.md"})


def extract_migration_map_paths(path: Path = MIGRATION_MAP) -> set[str]:
    text = path.read_text(encoding="utf-8")
    docs = set(re.findall(r"(docs/[a-zA-Z0-9_./-]+\.md)", text))
    specs = set(re.findall(r"(specs/[a-zA-Z0-9_./-]+\.(?:md|yaml|yml))", text))
    return docs | specs


def extract_generated_index_paths(path: Path = DOCS_SPECS_INDEX) -> set[str]:
    if not path.is_file():
        return set()
    return {
        line.strip().strip("- ").strip("`")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- `")
    }


def indexed_docs_specs_paths() -> set[str]:
    return extract_migration_map_paths() | extract_generated_index_paths()


def _docs_specs_files() -> set[str]:
    docs = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in REPO_ROOT.glob("docs/**/*.md")
        if "generated" not in p.parts
    }
    specs = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in REPO_ROOT.glob("specs/**/*")
        if p.suffix in {".md", ".yaml", ".yml"}
    }
    return docs | specs


def check_migration_map_coverage() -> list[str]:
    errors: list[str] = []
    if not MIGRATION_MAP.is_file():
        return ["MIGRATION_MAP.md missing"]
    if not DOCS_SPECS_INDEX.is_file():
        errors.append(
            f"missing {DOCS_SPECS_INDEX.relative_to(REPO_ROOT).as_posix()} "
            "(run scripts/generate_project_map.py)"
        )
    listed = indexed_docs_specs_paths()
    all_files = _docs_specs_files()
    for rel in sorted(all_files - listed - WAIVERS):
        errors.append(f"missing from docs/specs index: {rel}")
    for rel in sorted(listed):
        if rel in WAIVERS:
            continue
        if rel.startswith("docs/") or rel.startswith("specs/"):
            from repo_path_resolve import repo_path_exists

            if not repo_path_exists(rel):
                errors.append(f"stale MIGRATION_MAP ref: {rel}")
    return errors


def check_authority_graph_refs() -> list[str]:
    from loop_engineering_common import load_authority_graph, path_exists

    errors: list[str] = []
    graph = load_authority_graph()
    for name, cfg in (graph.get("modules") or {}).items():
        for bucket in ("docs", "contracts", "rules", "implementation_tasks", "tests"):
            for rel in cfg.get(bucket) or []:
                if not path_exists(str(rel)):
                    errors.append(f"authority_graph/{name}: missing {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    errors = check_migration_map_coverage() + check_authority_graph_refs()
    if errors:
        print("docs/specs index check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: docs/specs indexed (MIGRATION_MAP + generated index)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
