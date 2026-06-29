"""Validate Execute handoff to Audit — v4 primary; legacy v3 in_progress shim."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .md_utils import extract_md_section as _extract_section

_FAIL_RE = re.compile(
    r"FAIL|ERROR|ModuleNotFound|not found|collected 0 items|AssertionError",
    re.IGNORECASE,
)
_PASS_RE = re.compile(
    r"passed|PASSED|exit 0|exit_code.?0|All checks passed|100%",
    re.IGNORECASE,
)
_STEP_HEADER_RE = re.compile(r"^###\s+(\d+\.\d+)", re.MULTILINE)


def _marked_steps_in_section(section: str) -> list[str]:
    steps: list[str] = []
    for match in _STEP_HEADER_RE.finditer(section):
        step_id = match.group(1)
        chunk = section[match.start() :]
        next_hdr = re.search(r"\n###\s+\d+\.\d+", chunk[len(match.group(0)) :])
        block = chunk[: len(match.group(0)) + next_hdr.start()] if next_hdr else chunk
        if re.search(r"已执行\s*\|\s*\[x\]", block) or re.search(
            r"\|\s*已执行\s*\|\s*\[x\]", block
        ):
            steps.append(step_id)
    return steps


def _parse_v4_executed_steps(frozen_text: str) -> list[str]:
    section9 = _extract_section(frozen_text, "9.")
    return _marked_steps_in_section(section9 or frozen_text)


def _parse_legacy_executed_steps(master_text: str) -> list[str]:
    section8 = _extract_section(master_text, "8.")
    return [s for s in _marked_steps_in_section(section8 or master_text) if s.startswith("8.")]


def _discover_v4_executed_steps(task_dir: Path) -> list[str]:
    """Steps with red+green evidence pairs (SSOT for handoff)."""
    evidence = task_dir / "research" / "execute-evidence"
    if not evidence.is_dir():
        return []
    return sorted(
        {
            step
            for green in evidence.glob("*-green.txt")
            if (step := green.name.removesuffix("-green.txt"))
            and re.fullmatch(r"\d+\.\d+", step)
            and (evidence / f"{step}-red.txt").is_file()
        },
        key=lambda s: tuple(int(p) for p in s.split(".")),
    )


def _load_skill_reads(task_dir: Path) -> list[dict]:
    path = task_dir / "research" / "execute-skill-reads.jsonl"
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _required_handoff_skills(repo_root: Path) -> list[str]:
    yaml_path = repo_root / ".trellis/spec/guides/execute-skill-paths.yaml"
    if not yaml_path.is_file():
        return [
            "test-driven-development",
            "incremental-implementation",
            "karpathy-guidelines",
            "testing-guidelines",
        ]
    text = yaml_path.read_text(encoding="utf-8")
    match = re.search(r"handoff_required_skills:\s*\n((?:\s+-\s+.+\n)+)", text)
    if not match:
        return []
    return [
        line.strip().lstrip("- ").strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("-")
    ]


def _skills_from_reads(reads: list[dict]) -> set[str]:
    return {str(r.get("skill", "")).strip() for r in reads if r.get("skill")}


def validate_execute_step(task_dir: Path, step: str, *, repo_root: Path | None = None) -> list[str]:
    """Validate one §9.x (v4) or §8.x (legacy) step RED/GREEN evidence files."""
    _ = repo_root
    errors: list[str] = []
    if not re.fullmatch(r"\d+\.\d+", step):
        errors.append(f"Invalid step id: {step!r} (expected e.g. 8.0 or 9.0)")
        return errors

    evidence_dir = task_dir / "research" / "execute-evidence"
    red_path = evidence_dir / f"{step}-red.txt"
    green_path = evidence_dir / f"{step}-green.txt"

    if not red_path.is_file():
        errors.append(f"Missing RED evidence: research/execute-evidence/{step}-red.txt")
    elif not _FAIL_RE.search(red_path.read_text(encoding="utf-8")):
        errors.append(f"{step}-red.txt must contain FAIL/ERROR signal (TDD RED phase)")

    if not green_path.is_file():
        errors.append(f"Missing GREEN evidence: research/execute-evidence/{step}-green.txt")
    elif not _PASS_RE.search(green_path.read_text(encoding="utf-8")):
        errors.append(f"{step}-green.txt must contain PASS/exit 0 signal (TDD GREEN phase)")

    return errors


def _append_execute_handoff_boot_errors(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    gnxs = task_dir / "research" / "gitnexus-execute-summary.md"
    if not gnxs.is_file():
        errors.append("Missing research/gitnexus-execute-summary.md (Phase 0a GitNexus)")

    reads_path = task_dir / "research" / "execute-skill-reads.jsonl"
    if not reads_path.is_file():
        errors.append("Missing research/execute-skill-reads.jsonl (skill Read audit log)")
    else:
        reads = _load_skill_reads(task_dir)
        if not reads:
            errors.append("execute-skill-reads.jsonl has no valid JSON lines")
        read_skills = _skills_from_reads(reads)
        for skill in _required_handoff_skills(repo_root):
            if skill not in read_skills:
                errors.append(f"execute-skill-reads.jsonl missing required skill: {skill}")

    evidence_md = list(task_dir.glob("research/*evidence*.md"))
    evidence_dir = task_dir / "research" / "execute-evidence"
    if not evidence_md and not evidence_dir.is_dir():
        errors.append(
            "Missing Execute evidence: research/*evidence*.md or research/execute-evidence/"
        )

    skill_eval = task_dir / "research" / "execute-skill-evaluation.md"
    if not skill_eval.is_file():
        errors.append("Missing research/execute-skill-evaluation.md (§12 skill evaluation)")
    elif reads_path.is_file():
        eval_text = skill_eval.read_text(encoding="utf-8")
        if "execute-skill-reads.jsonl" not in eval_text and "skill-reads" not in eval_text:
            errors.append(
                "execute-skill-evaluation.md must reference execute-skill-reads.jsonl"
            )


def _validate_loop_handoff(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from check_task_evidence import check_task_evidence
        from loop_engineering_common import loop_required
    except ImportError as exc:
        errors.append(f"loop handoff import failed: {exc}")
        return
    if not loop_required(task_dir):
        return
    for err in check_task_evidence(task_dir):
        errors.append(err)
    if not (task_dir / "evidence_index.json").is_file():
        errors.append("missing evidence_index.json (loop handoff)")
    if not (task_dir / "loop_manifest.json").is_file():
        errors.append("missing loop_manifest.json (loop handoff)")


def _validate_v4_handoff(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    _append_execute_handoff_boot_errors(task_dir, repo_root, errors)
    for step in _discover_v4_executed_steps(task_dir):
        errors.extend(validate_execute_step(task_dir, step, repo_root=repo_root))
    from .manifest_protocol import validate_execute_boot, validate_manifest_amend_chain

    validate_execute_boot(task_dir, errors)
    validate_manifest_amend_chain(task_dir, errors)
    _validate_loop_handoff(task_dir, repo_root, errors)


def _validate_legacy_handoff(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    _append_execute_handoff_boot_errors(task_dir, repo_root, errors)
    master = task_dir / "MASTER.plan.md"
    text = master.read_text(encoding="utf-8")
    for step in _parse_legacy_executed_steps(text):
        errors.extend(validate_execute_step(task_dir, step, repo_root=repo_root))
    from .manifest_protocol import validate_execute_boot, validate_manifest_amend_chain

    validate_execute_boot(task_dir, errors)
    validate_manifest_amend_chain(task_dir, errors)
    _validate_loop_handoff(task_dir, repo_root, errors)


def validate_execute_handoff(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Return validation errors; empty list means pass."""
    from .paths import get_repo_root
    from .plan_protocol import is_plan_protocol_v4
    from .task_archive import (
        has_task_plan_artifacts,
        is_active_legacy_v3,
        is_archived_task,
        legacy_handoff_allowed,
        legacy_handoff_error,
    )

    if repo_root is None:
        repo_root = get_repo_root()

    errors: list[str] = []
    if is_archived_task(task_dir):
        return errors

    if not (task_dir / "task.json").is_file():
        if has_task_plan_artifacts(task_dir):
            return ["missing task.json (required when plan artifacts present)"]
        return errors

    if is_plan_protocol_v4(task_dir) and (task_dir / "EXECUTION_INDEX.md").is_file():
        _validate_v4_handoff(task_dir, repo_root, errors)
        return errors

    if legacy_handoff_allowed(task_dir):
        _validate_legacy_handoff(task_dir, repo_root, errors)
        return errors

    if is_active_legacy_v3(task_dir):
        errors.append(legacy_handoff_error())
    return errors


def cmd_validate_execute_handoff(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_execute_handoff(task_dir, repo_root)
    if errors:
        print(colored("Execute handoff validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1

    print(colored("Execute handoff validation passed", Colors.GREEN))
    return 0


def cmd_validate_execute_step(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_execute_step(task_dir, args.step, repo_root=repo_root)
    if errors:
        print(colored(f"Execute step {args.step} validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1

    print(colored(f"Execute step {args.step} validation passed", Colors.GREEN))
    return 0
