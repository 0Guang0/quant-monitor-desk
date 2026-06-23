#!/usr/bin/env python3
"""Generate context_pack.json from authority graph for modules, files, or tasks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_engineering_common import (
    AUTHORITY_GRAPH_PATH,
    collect_module_authorities,
    infer_task_touched_paths,
    load_authority_graph,
    load_test_catalog,
    modules_for_paths,
    repo_relative,
    validate_context_pack,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _task_name(task_dir: Path) -> str:
    return task_dir.name


def _infer_paths_from_task(task_dir: Path) -> list[str]:
    return infer_task_touched_paths(task_dir)


def _catalog_purpose(rel: str) -> str:
    catalog = load_test_catalog()
    entry = catalog.get(rel) or {}
    purpose = entry.get("purpose")
    return str(purpose) if purpose else f"Regression coverage for {Path(rel).stem}"


def build_context_pack(
    *,
    task: str | None,
    modules: list[str],
    touched_paths: list[str],
) -> dict:
    graph = load_authority_graph()
    known_modules = set((graph.get("modules") or {}).keys())
    for name in modules:
        if name not in known_modules:
            raise ValueError(f"unknown module in authority graph: {name}")

    if not modules and touched_paths:
        modules = modules_for_paths(touched_paths, graph)

    source_authorities: list[dict[str, str]] = []
    tests: list[dict[str, str]] = []
    forbidden_claims: list[str] = []
    required_evidence: list[str] = []
    seen_auth: set[str] = set()
    seen_tests: set[str] = set()

    for module_name in modules:
        bundle = collect_module_authorities(module_name, graph)
        for item in bundle["source_authorities"]:
            key = item["path"]
            if key not in seen_auth:
                seen_auth.add(key)
                source_authorities.append(item)
        for item in bundle["tests"]:
            key = item["path"]
            if key not in seen_tests:
                seen_tests.add(key)
                tests.append(
                    {
                        "path": key,
                        "purpose": _catalog_purpose(key),
                    }
                )
        for claim in bundle["forbidden_claims"]:
            if claim not in forbidden_claims:
                forbidden_claims.append(claim)
        for ev in bundle["required_evidence"]:
            if ev not in required_evidence:
                required_evidence.append(ev)

    for rel in touched_paths:
        norm = rel.replace("\\", "/")
        if norm.startswith("tests/") and norm.endswith(".py") and norm not in seen_tests:
            seen_tests.add(norm)
            tests.append({"path": norm, "purpose": _catalog_purpose(norm)})

    return {
        "task": task or "",
        "modules": modules,
        "source_authorities": source_authorities,
        "tests": tests,
        "forbidden_claims": forbidden_claims,
        "required_evidence": required_evidence,
    }


def _render_router_section_d() -> str:
    return (
        "## D. 机器路由\n\n"
        "权威数据在 **`context_pack.json`**（本任务根目录）。"
        " 由 `context_router.py --task` 写入；本段不重复列举。\n"
    )


def _upsert_source_index_section_d(task_dir: Path) -> Path | None:
    research = task_dir / "research"
    md_path = research / "source-index.md"
    if not md_path.is_file():
        return None
    text = md_path.read_text(encoding="utf-8")
    section_d = _render_router_section_d()
    start_marker = "## D."
    end_marker = "## E."
    start = text.find(start_marker)
    if start < 0:
        md_path.write_text(text.rstrip() + "\n\n" + section_d, encoding="utf-8")
        return md_path
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        new_text = text[:start].rstrip() + "\n\n" + section_d
    else:
        new_text = text[:start].rstrip() + "\n\n" + section_d + "\n" + text[end:]
    md_path.write_text(new_text.rstrip() + "\n", encoding="utf-8")
    return md_path


def write_context_outputs(task_dir: Path, pack: dict) -> tuple[Path, Path | None]:
    task_dir.mkdir(parents=True, exist_ok=True)
    pack_path = task_dir / "context_pack.json"
    pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = _upsert_source_index_section_d(task_dir)
    return pack_path, md_path


def cmd_module(module: str, output: Path | None) -> int:
    pack = build_context_pack(task=None, modules=[module], touched_paths=[])
    errors = validate_context_pack(pack)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {repo_relative(output)}")
    else:
        print(json.dumps(pack, indent=2, ensure_ascii=False))
    return 0


def cmd_files(files: list[str], output: Path | None) -> int:
    graph = load_authority_graph()
    modules = modules_for_paths(files, graph)
    pack = build_context_pack(task=None, modules=modules, touched_paths=files)
    errors = validate_context_pack(pack)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {repo_relative(output)}")
    else:
        print(json.dumps(pack, indent=2, ensure_ascii=False))
    return 0


def generate_task_loop_artifacts(task_dir: Path) -> list[str]:
    """Build context_pack + loop evidence stubs. Returns errors (empty = ok)."""
    if not task_dir.is_dir():
        return [f"task directory not found: {task_dir}"]
    if not AUTHORITY_GRAPH_PATH.is_file():
        return [f"missing authority graph: {repo_relative(AUTHORITY_GRAPH_PATH)}"]
    touched = _infer_paths_from_task(task_dir)
    graph = load_authority_graph()
    modules = modules_for_paths(touched, graph)
    pack = build_context_pack(task=_task_name(task_dir), modules=modules, touched_paths=touched)
    errors = validate_context_pack(pack)
    if errors:
        return errors
    write_context_outputs(task_dir, pack)
    from loop_engineering_common import write_loop_evidence_stubs

    write_loop_evidence_stubs(task_dir, pack)
    return []


def cmd_task(task_arg: str, check_only: bool) -> int:
    task_dir = Path(task_arg)
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / task_arg
    if not task_dir.is_dir():
        print(f"task directory not found: {task_arg}", file=sys.stderr)
        return 1

    if check_only:
        pack_path = task_dir / "context_pack.json"
        if not pack_path.is_file():
            print("missing context_pack.json", file=sys.stderr)
            return 1
        existing = json.loads(pack_path.read_text(encoding="utf-8"))
        errors = validate_context_pack(existing)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print(f"OK: {repo_relative(pack_path)}")
        return 0

    errors = generate_task_loop_artifacts(task_dir)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    pack_path = task_dir / "context_pack.json"
    md_path = task_dir / "research" / "source-index.md"
    manifest_path = task_dir / "loop_manifest.json"
    evidence_path = task_dir / "evidence_index.json"
    print(f"Wrote {repo_relative(pack_path)}")
    if md_path.is_file():
        print(f"Updated {repo_relative(md_path)} §D")
    print(f"Wrote {repo_relative(manifest_path)}")
    print(f"Wrote {repo_relative(evidence_path)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--module", help="Authority graph module name")
    group.add_argument("--files", nargs="+", help="Repo-relative file paths")
    group.add_argument("--task", help="Task directory under .trellis/tasks")
    parser.add_argument("--output", type=Path, help="Optional output path for --module/--files")
    parser.add_argument("--check", action="store_true", help="Validate existing context_pack.json")
    args = parser.parse_args()

    if not AUTHORITY_GRAPH_PATH.is_file():
        print(f"missing authority graph: {repo_relative(AUTHORITY_GRAPH_PATH)}", file=sys.stderr)
        return 1

    if args.module:
        return cmd_module(args.module, args.output)
    if args.files:
        return cmd_files(args.files, args.output)
    return cmd_task(args.task, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
