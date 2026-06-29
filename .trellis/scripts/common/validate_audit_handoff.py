"""Validate Audit A9 handoff and Repair close — mechanical gates."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

_FINDING_ID_RE = re.compile(r"^\|\s*(A[1-8]-P[0-3]-\S+)\s*\|", re.MULTILINE)
_PLACEHOLDER_RE = re.compile(r"^\|\s*—\s*\|\s*—\s*\|\s*无\s*\|", re.MULTILINE)
_VERDICT_RE = re.compile(r"^\s*\*\*(PASS|FAIL|SKIP)\*\*\s*$", re.MULTILINE)
_FORBIDDEN_IN_ROW = re.compile(
    r"NON-BLOCKING|BLOCKING|信息性|PASS_WITH|"
    r"\bfixed\b|\bdeferred\b|"
    r"P0\s+BLOCKING|P\d\s+NON-BLOCKING",
    re.IGNORECASE,
)
_PRESIDENT_IN_DIM = re.compile(r"总裁决\s*[:：]", re.IGNORECASE)
_A9_DISPOSITIONS = frozenset({"待修复", "阶段外置"})
_REPAIR_DISPOSITIONS = frozenset({"已修复", "阶段外置"})
_MATRIX_KEYS = tuple(f"A{n}" for n in range(1, 9))
_VERDICT_TO_MATRIX = {"PASS": "pass", "FAIL": "fail", "SKIP": "skip"}
_VALID_MATRIX_RESULTS = frozenset({"pass", "fail", "skip", "fail_then_fixed"})


def _section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def _finding_ids(text: str | None) -> set[str]:
    return set(_FINDING_ID_RE.findall(text or ""))


def _has_only_placeholder(section: str | None) -> bool:
    if not section:
        return True
    return not _finding_ids(section) and bool(_PLACEHOLDER_RE.search(section))


def _dimension_verdict(text: str) -> str | None:
    block = _section(text, "§维度裁决")
    if not block:
        return None
    match = _VERDICT_RE.search(block)
    return match.group(1) if match else None


def _ledger_parts(line: str) -> list[str] | None:
    if not _FINDING_ID_RE.match(line):
        return None
    parts = [p.strip() for p in line.split("|")]
    return parts if len(parts) >= 10 else None


def _check_deferred_row(parts: list[str], fid: str, errors: list[str]) -> None:
    if not parts[6] or parts[6] == "—":
        errors.append(f"audit-repair-ledger.md {fid}: 阶段外置 requires 绑定任务")
    registry = parts[8]
    if "待修复清单" not in registry:
        errors.append(
            f"audit-repair-ledger.md {fid}: 阶段外置 登记位置 must include "
            "docs/quality/待修复清单.md"
        )
    if "PROJECT_IMPLEMENTATION_ROADMAP" not in registry:
        errors.append(
            f"audit-repair-ledger.md {fid}: 阶段外置 登记位置 must include "
            "PROJECT_IMPLEMENTATION_ROADMAP.md"
        )


def _validate_ledger_dispositions(
    ledger: str,
    *,
    allowed: frozenset[str],
    phase_label: str,
    errors: list[str],
) -> None:
    for line in ledger.splitlines():
        parts = _ledger_parts(line)
        if not parts:
            continue
        fid = parts[1]
        if _FORBIDDEN_IN_ROW.search(line):
            errors.append(f"audit-repair-ledger.md {fid}: legacy vocabulary in row")
        disp = parts[5]
        if disp not in allowed:
            errors.append(
                f"audit-repair-ledger.md {fid}: {phase_label} disposition must be "
                f"{' or '.join(sorted(allowed))} (got {disp!r})"
            )
        elif disp == "阶段外置":
            _check_deferred_row(parts, fid, errors)


def _collect_dimension_findings(task_dir: Path) -> tuple[list[str], set[str], dict[str, str]]:
    errors: list[str] = []
    all_ids: set[str] = set()
    verdicts: dict[str, str] = {}
    for n in range(1, 9):
        path = task_dir / "research" / f"audit-a{n}-report.md"
        text = path.read_text(encoding="utf-8")
        verdict = _dimension_verdict(text)
        if verdict is None:
            errors.append(f"{path.name}: missing §维度裁决 (PASS|FAIL|SKIP)")
            continue
        verdicts[path.name] = verdict

        plan_in = _section(text, "计划内问题")
        plan_out = _section(text, "计划外发现")
        all_ids.update(_finding_ids(plan_in))
        all_ids.update(_finding_ids(plan_out))

        only_ph = _has_only_placeholder(plan_in) and _has_only_placeholder(plan_out)
        if verdict == "PASS" and not only_ph:
            errors.append(f"{path.name}: §维度裁决 PASS but findings table has non-placeholder rows")
        if verdict == "FAIL" and only_ph:
            errors.append(f"{path.name}: §维度裁决 FAIL but both findings tables are placeholder-only")
        if _PRESIDENT_IN_DIM.search(text):
            errors.append(f"{path.name}: 总裁决 belongs in audit.report.md §4.2 only")
        for line in (plan_in or "").splitlines() + (plan_out or "").splitlines():
            if _FINDING_ID_RE.match(line) and _FORBIDDEN_IN_ROW.search(line):
                errors.append(
                    f"{path.name}: findings use legacy severity (NON-BLOCKING/信息性/BLOCKING)"
                )
                break

    return errors, all_ids, verdicts


def _validate_matrix(task_dir: Path, verdicts: dict[str, str], errors: list[str]) -> None:
    matrix_path = task_dir / "audit_matrix.json"
    if not matrix_path.is_file():
        errors.append("Missing audit_matrix.json")
        return
    try:
        dims = json.loads(matrix_path.read_text(encoding="utf-8")).get("dimensions")
    except json.JSONDecodeError as exc:
        errors.append(f"audit_matrix.json invalid JSON: {exc}")
        return
    if not isinstance(dims, dict):
        errors.append("audit_matrix.json missing dimensions object")
        return

    for key in _MATRIX_KEYS:
        entry = dims.get(key)
        if not isinstance(entry, dict):
            errors.append(f"audit_matrix.json missing or invalid dimension {key}")
            continue
        result = entry.get("result")
        if result not in _VALID_MATRIX_RESULTS:
            errors.append(f"audit_matrix.json dimensions.{key}.result invalid: {result!r}")
            continue
        verdict = verdicts.get(f"audit-{key.lower()}-report.md")
        expected = _VERDICT_TO_MATRIX.get(verdict or "")
        if expected and result not in {expected, "fail_then_fixed"}:
            errors.append(
                f"audit_matrix.json {key}.result={result!r} ≠ report §维度裁决 {verdict}"
            )


def validate_audit_handoff(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """A9 → Repair gate: ledger disposition ∈ {待修复, 阶段外置}."""
    _ = repo_root
    research = task_dir / "research"
    missing = [f"audit-a{n}-report.md" for n in range(1, 9) if not (research / f"audit-a{n}-report.md").is_file()]
    if missing:
        return [f"Missing dimension reports: {', '.join(missing)}"]

    errors, all_ids, verdicts = _collect_dimension_findings(task_dir)
    audit_report = task_dir / "audit.report.md"
    if not audit_report.is_file():
        errors.append("Missing audit.report.md (A9 main session)")
    else:
        for line in audit_report.read_text(encoding="utf-8").splitlines():
            if _FINDING_ID_RE.match(line) and _FORBIDDEN_IN_ROW.search(line):
                errors.append("audit.report.md §4.1 finding rows use legacy vocabulary")
                break

    ledger_path = research / "audit-repair-ledger.md"
    if not ledger_path.is_file():
        errors.append("Missing research/audit-repair-ledger.md")
    else:
        ledger = ledger_path.read_text(encoding="utf-8")
        if missing_ids := sorted(all_ids - _finding_ids(ledger)):
            errors.append(
                "audit-repair-ledger.md missing finding IDs from A1–A8: " + ", ".join(missing_ids)
            )
        _validate_ledger_dispositions(
            ledger, allowed=_A9_DISPOSITIONS, phase_label="A9", errors=errors
        )

    _validate_matrix(task_dir, verdicts, errors)
    return errors


def validate_repair_close(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Repair 关账 gate: disposition ∈ {已修复, 阶段外置}."""
    _ = repo_root
    ledger_path = task_dir / "research" / "audit-repair-ledger.md"
    if not ledger_path.is_file():
        return ["Missing research/audit-repair-ledger.md"]
    errors: list[str] = []
    _validate_ledger_dispositions(
        ledger_path.read_text(encoding="utf-8"),
        allowed=_REPAIR_DISPOSITIONS,
        phase_label="Repair 关账",
        errors=errors,
    )
    return errors


def _cmd_gate(args, validate: Callable[[Path, Path | None], list[str]], ok_msg: str) -> int:
    from .paths import get_repo_root

    errors = validate(Path(args.dir).resolve(), get_repo_root())
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(ok_msg)
    return 0


def cmd_validate_audit_handoff(args) -> int:
    return _cmd_gate(args, validate_audit_handoff, "validate-audit-handoff: OK")


def cmd_validate_repair_close(args) -> int:
    return _cmd_gate(args, validate_repair_close, "validate-repair-close: OK")
