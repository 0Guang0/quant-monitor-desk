"""Pre-release hardening checks (incremental; Round 5 expands scope)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_module_boundaries.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(f"module boundary check failed: {result.stderr or result.stdout}")


def main() -> int:
    check_no_prod_stub_validation()
    check_workflow_permissions()
    check_dependabot_present()
    check_agent_contract()
    check_resource_contract()
    check_module_boundaries()

    if FAILURES:
        for item in FAILURES:
            print(f"PRODUCTION_GATE_FAIL: {item}", file=sys.stderr)
        return 1

    print("production_gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
