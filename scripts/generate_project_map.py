#!/usr/bin/env python3
"""Generate machine-readable project map and docs/specs index from loop configs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_engineering_common import (
    AUTHORITY_GRAPH_PATH,
    REPO_ROOT,
    TEST_CATALOG_PATH,
    load_authority_graph,
    load_test_catalog,
    repo_relative,
)

OUT_MD = REPO_ROOT / "docs/generated/project_map.generated.md"
OUT_JSON = REPO_ROOT / "docs/generated/project_map.generated.json"
DOCS_SPECS_INDEX = REPO_ROOT / "docs/generated/docs_specs_index.generated.md"


def _docs_specs_files() -> list[str]:
    docs = sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in REPO_ROOT.glob("docs/**/*.md")
        if "generated" not in p.parts
    )
    specs = sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in REPO_ROOT.glob("specs/**/*")
        if p.suffix in {".md", ".yaml", ".yml"}
    )
    return docs + specs


def _build_project_map() -> dict:
    graph = load_authority_graph()
    rating_ssot = graph.get("rating_ssot")
    modules: dict = {}
    catalog = load_test_catalog()
    for name, cfg in (graph.get("modules") or {}).items():
        tests = []
        for rel in cfg.get("tests") or []:
            entry = catalog.get(rel) or {}
            tests.append(
                {
                    "path": rel,
                    "purpose": entry.get("purpose", ""),
                    "command": entry.get("command", f"uv run python -m pytest {rel} -q"),
                }
            )
        modules[name] = {
            "module_ids": cfg.get("module_ids") or [],
            "implementation": cfg.get("implementation") or [],
            "docs": cfg.get("docs") or [],
            "contracts": cfg.get("contracts") or [],
            "rules": cfg.get("rules") or [],
            "implementation_tasks": cfg.get("implementation_tasks") or [],
            "required_evidence": cfg.get("required_evidence") or [],
            "tests": tests,
            "forbidden_claims": cfg.get("forbidden_claims") or [],
        }
    return {"version": "2", "rating_ssot": rating_ssot, "rating_index": graph.get("rating_index") or {}, "modules": modules}


def _render_project_map_md(payload: dict) -> str:
    lines = [
        "# Project Map (generated)",
        "",
        "Do not edit by hand. Regenerate with `uv run python scripts/generate_project_map.py`.",
        "",
    ]
    if payload.get("rating_ssot"):
        lines.append(f"Rating SSOT: `{payload['rating_ssot']}`")
        lines.append("")
    for name, cfg in payload.get("modules", {}).items():
        lines.append(f"## {name}")
        if cfg.get("module_ids"):
            lines.append(f"- module_ids: {', '.join(cfg['module_ids'])}")
        lines.append(f"- implementation: {', '.join(cfg.get('implementation') or [])}")
        lines.append(f"- docs: {len(cfg.get('docs') or [])}")
        lines.append(f"- contracts: {len(cfg.get('contracts') or [])}")
        if cfg.get("implementation_tasks"):
            lines.append(f"- implementation_tasks: {len(cfg['implementation_tasks'])}")
        if cfg.get("required_evidence"):
            lines.append(f"- required_evidence: {', '.join(cfg['required_evidence'])}")
        lines.append(f"- tests: {len(cfg.get('tests') or [])}")
        if cfg.get("forbidden_claims"):
            lines.append(f"- forbidden: {', '.join(cfg['forbidden_claims'])}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_docs_specs_index_md(files: list[str]) -> str:
    lines = [
        "# docs/specs index (generated)",
        "",
        "Do not edit by hand. Regenerate with `uv run python scripts/generate_project_map.py`.",
        "Used with MIGRATION_MAP.md for machine omission checks (`check_docs_specs_indexed.py`).",
        "",
    ]
    for rel in files:
        lines.append(f"- `{rel}`")
    return "\n".join(lines) + "\n"


def _write_all(project_map: dict, docs_specs: list[str]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(project_map, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    OUT_MD.write_text(_render_project_map_md(project_map), encoding="utf-8")
    DOCS_SPECS_INDEX.write_text(_render_docs_specs_index_md(docs_specs), encoding="utf-8")


def _stale_errors(project_map: dict, docs_specs: list[str]) -> list[str]:
    errors: list[str] = []
    if not OUT_JSON.is_file():
        errors.append(f"stale: missing {repo_relative(OUT_JSON)}")
    else:
        current = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        if current != project_map:
            errors.append("stale: project_map.generated.json out of date")
    if not DOCS_SPECS_INDEX.is_file():
        errors.append(f"stale: missing {repo_relative(DOCS_SPECS_INDEX)}")
    else:
        listed = {
            line.strip().strip("- ").strip("`")
            for line in DOCS_SPECS_INDEX.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("- `")
        }
        if listed != set(docs_specs):
            errors.append("stale: docs_specs_index.generated.md out of date")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale")
    args = parser.parse_args()
    if not AUTHORITY_GRAPH_PATH.is_file() or not TEST_CATALOG_PATH.is_file():
        print("missing authority_graph or test_catalog", file=sys.stderr)
        return 1
    project_map = _build_project_map()
    docs_specs = _docs_specs_files()
    if args.check:
        errors = _stale_errors(project_map, docs_specs)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print("OK: project map and docs/specs index fresh")
        return 0
    _write_all(project_map, docs_specs)
    print(f"Wrote {repo_relative(OUT_JSON)}")
    print(f"Wrote {repo_relative(OUT_MD)}")
    print(f"Wrote {repo_relative(DOCS_SPECS_INDEX)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
