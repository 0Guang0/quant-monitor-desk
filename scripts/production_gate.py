"""Pre-release hardening checks (incremental; Round 5 expands scope)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_DRY_MATRIX_ROOT = ROOT / ".audit-sandbox" / "source-route-db-ci-dry"
CI_DRY_MATRIX_REPORT = CI_DRY_MATRIX_ROOT / "reports" / "source-matrix-acceptance.json"
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _run_checked(cmd: list[str], *, label: str) -> None:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        fail(f"{label} failed (exit {result.returncode}): {detail}")


def check_no_prod_stub_validation() -> None:
    for path in (ROOT / "backend" / "app").rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if path.name != "validation_gate.py" and "StubValidationGate()" in text:
            fail(f"production code uses StubValidationGate(): {path.relative_to(ROOT)}")
        if path.name != "validation_gate.py" and "stub-pass" in text:
            fail(f"production code contains stub-pass validation id: {path.relative_to(ROOT)}")


def check_workflow_permissions() -> None:
    workflow = ROOT / ".github/workflows/ci.yml"
    if not workflow.is_file():
        fail("missing .github/workflows/ci.yml")
        return
    text = workflow.read_text(encoding="utf-8")
    if "permissions:" not in text or "contents: read" not in text:
        fail("ci.yml must declare least-privilege permissions: contents: read")


def check_dependabot_present() -> None:
    if not (ROOT / ".github/dependabot.yml").is_file():
        fail("missing .github/dependabot.yml")


def check_agent_contract() -> None:
    text = read("specs/contracts/agent_contract.yaml")
    for forbidden in (
        "execute_arbitrary_sql",
        "write_duckdb_directly",
        "fetch_web_directly",
        "modify_clean_table_directly",
    ):
        if forbidden not in text:
            fail(f"agent contract missing forbidden tool: {forbidden}")


def check_resource_contract() -> None:
    text = read("specs/contracts/resource_limits.yaml")
    if "default_profile: eco" not in text:
        fail("resource contract must default to eco")
    for key in ("api_limits", "agent_max_rows", "daily_bar_max_days"):
        if key not in text:
            fail(f"resource contract missing {key}")


def check_module_boundaries() -> None:
    _run_checked(
        [sys.executable, str(ROOT / "scripts" / "check_module_boundaries.py")],
        label="module boundary check",
    )


def check_acceptance_helper_consumers_strict() -> None:
    _run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_acceptance_helper_consumers.py"),
            "--strict",
            "--strict-seam-inventory",
        ],
        label="acceptance helper consumers --strict --strict-seam-inventory",
    )


def check_source_route_matrix_static() -> None:
    _run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_source_route_db_acceptance_matrix.py"),
            "--strict",
        ],
        label="source route matrix static contract",
    )


def check_source_route_matrix_dry_run_closure() -> None:
    CI_DRY_MATRIX_ROOT.mkdir(parents=True, exist_ok=True)
    _run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "qmd_ops.py"),
            "accept-source-route-db",
            "--all-documented-sources",
            "--data-root",
            str(CI_DRY_MATRIX_ROOT),
            "--report",
            str(CI_DRY_MATRIX_REPORT),
            "--format",
            "json",
        ],
        label="source route matrix dry-run generation",
    )
    _run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_source_route_db_acceptance_matrix.py"),
            "--strict",
            "--report",
            str(CI_DRY_MATRIX_REPORT),
        ],
        label="source route matrix dry-run closure",
    )


def check_source_route_matrix_live_closure(report_path: Path) -> None:
    resolved = report_path if report_path.is_absolute() else ROOT / report_path
    if not resolved.is_file():
        fail(f"source matrix live report not found: {resolved}")
        return
    data_root = resolved.parent.parent if resolved.parent.name == "reports" else None
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "check_source_route_db_acceptance_matrix.py"),
        "--strict",
        "--live-authorized",
        "--report",
        str(resolved),
    ]
    if data_root is not None:
        cmd.extend(["--data-root", str(data_root)])
    _run_checked(cmd, label="source route matrix live-authorized closure")


def main(argv: list[str] | None = None) -> int:
    FAILURES.clear()
    parser = argparse.ArgumentParser(description="Pre-release hardening checks")
    parser.add_argument(
        "--source-matrix-report",
        type=Path,
        default=None,
        help="Optional pre-generated source matrix JSON for release live-authorized closure check",
    )
    parser.add_argument(
        "--live-authorized",
        action="store_true",
        help="Validate --source-matrix-report with final_live_authorized closure (release gate)",
    )
    args = parser.parse_args(argv)

    check_no_prod_stub_validation()
    check_workflow_permissions()
    check_dependabot_present()
    check_agent_contract()
    check_resource_contract()
    check_module_boundaries()
    check_acceptance_helper_consumers_strict()
    check_source_route_matrix_static()

    if args.live_authorized:
        if args.source_matrix_report is None:
            fail("--live-authorized requires --source-matrix-report")
        else:
            check_source_route_matrix_live_closure(args.source_matrix_report)
    else:
        if args.source_matrix_report is not None:
            fail("--source-matrix-report requires --live-authorized")
        check_source_route_matrix_dry_run_closure()

    if FAILURES:
        for item in FAILURES:
            print(f"PRODUCTION_GATE_FAIL: {item}", file=sys.stderr)
        return 1

    print("production_gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
