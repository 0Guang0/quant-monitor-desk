#!/usr/bin/env python3
"""One-shot Trellis loop maintenance: catalog, generated maps, authority_graph gaps."""

from __future__ import annotations

import argparse
import sys

from loop_engineering_common import REPO_ROOT, discover_unmapped_backend_packages, repo_relative


def run_maintain(*, fix: bool) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). fix=True writes catalog + generated maps."""
    errors: list[str] = []
    warnings: list[str] = []

    from check_active_master_tasks import check_active_master_tasks
    from check_contract_coverage import check_coverage
    from check_test_catalog import build_catalog, check_catalog, write_catalog
    from check_verification_matrix import check_matrix

    if fix:
        write_catalog(build_catalog())
        print(f"Wrote {repo_relative(REPO_ROOT / 'tests/test_catalog.yaml')}")
    else:
        for err in check_catalog():
            errors.append(f"test_catalog: {err}")
        for err in check_matrix():
            errors.append(f"verification_matrix: {err}")
        for err in check_coverage():
            errors.append(f"contract_coverage: {err}")
        for err in check_active_master_tasks():
            errors.append(f"active_master_tasks: {err}")

    from generate_project_map import _build_project_map, _docs_specs_files, _stale_errors, _write_all

    project_map = _build_project_map()
    docs_specs = _docs_specs_files()
    if fix:
        _write_all(project_map, docs_specs)
        print(f"Wrote {repo_relative(REPO_ROOT / 'docs/generated/project_map.generated.json')}")
        print(f"Wrote {repo_relative(REPO_ROOT / 'docs/generated/docs_specs_index.generated.md')}")
    else:
        for err in _stale_errors(project_map, docs_specs):
            errors.append(f"project_map: {err}")

    unmapped = discover_unmapped_backend_packages()
    for pkg in unmapped:
        msg = f"authority_graph: unmapped backend/app/{pkg} — add specs/context/authority_graph.yaml entry"
        if fix:
            warnings.append(msg)
        else:
            errors.append(msg)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Write test_catalog.yaml and generated project/docs indexes",
    )
    args = parser.parse_args()

    errors, warnings = run_maintain(fix=args.fix)
    for warn in warnings:
        print(f"WARNING: {warn}", file=sys.stderr)
    if errors:
        print("loop maintain FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: loop maintain" + (" (fixed)" if args.fix else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
