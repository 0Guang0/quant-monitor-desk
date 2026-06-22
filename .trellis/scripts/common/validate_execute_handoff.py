"""Validate Execute handoff to Audit (§11 DoD) — protocol v2."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_FAIL_RE = re.compile(
    r"FAIL|ERROR|ModuleNotFound|not found|collected 0 items|AssertionError",
    re.IGNORECASE,
)
_PASS_RE = re.compile(
    r"passed|PASSED|exit 0|exit_code.?0|All checks passed|100%",
    re.IGNORECASE,
)
_STEP_HEADER_RE = re.compile(r"^###\s+(8\.\d+)", re.MULTILINE)
_BOOT_COMPLETE = "Phase 0 complete"


def _extract_section(text: str, header_prefix: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    prefix = f"## {header_prefix}"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start is None and stripped.startswith(prefix):
            start = i
            continue
        if start is not None and stripped.startswith("## ") and not stripped.startswith(prefix):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def _parse_executed_steps(master_text: str) -> list[str]:
    section8 = _extract_section(master_text, "8.")
    steps: list[str] = []
    for match in _STEP_HEADER_RE.finditer(section8):
        step_id = match.group(1)
        chunk = section8[match.start() :]
        next_hdr = re.search(r"\n###\s+8\.\d+", chunk[len(match.group(0)) :])
        block = chunk[: len(match.group(0)) + next_hdr.start()] if next_hdr else chunk
        if re.search(r"已执行\s*\|\s*\[x\]", block) or re.search(r"\|\s*已执行\s*\|\s*\[x\]", block):
            steps.append(step_id)
    return steps


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
    """Validate one §8.x step has RED/GREEN evidence files."""
    _ = repo_root
    errors: list[str] = []
    if not re.fullmatch(r"8\.\d+", step):
        errors.append(f"Invalid step id: {step!r} (expected 8.0, 8.1, …)")
        return errors

    evidence_dir = task_dir / "research" / "execute-evidence"
    red_path = evidence_dir / f"{step}-red.txt"
    green_path = evidence_dir / f"{step}-green.txt"

    if not red_path.is_file():
        errors.append(f"Missing RED evidence: research/execute-evidence/{step}-red.txt")
    else:
        red_text = red_path.read_text(encoding="utf-8")
        if not _FAIL_RE.search(red_text):
            errors.append(
                f"{step}-red.txt must contain FAIL/ERROR signal (TDD RED phase)"
            )

    if not green_path.is_file():
        errors.append(f"Missing GREEN evidence: research/execute-evidence/{step}-green.txt")
    else:
        green_text = green_path.read_text(encoding="utf-8")
        if not _PASS_RE.search(green_text):
            errors.append(
                f"{step}-green.txt must contain PASS/exit 0 signal (TDD GREEN phase)"
            )

    return errors


def validate_execute_handoff(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Return validation errors; empty list means pass."""
    if repo_root is None:
        repo_root = task_dir
        while repo_root.name and not (repo_root / ".trellis").is_dir():
            if repo_root.parent == repo_root:
                break
            repo_root = repo_root.parent

    errors: list[str] = []
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return errors

    # --- Protocol v2 boot artifacts ---
    boot = task_dir / "research" / "execute-boot.md"
    if not boot.is_file():
        errors.append("Missing research/execute-boot.md (Phase 0 boot)")
    elif _BOOT_COMPLETE not in boot.read_text(encoding="utf-8"):
        errors.append(f"execute-boot.md must contain {_BOOT_COMPLETE!r}")

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

    # --- Evidence (legacy summary OR per-step dir) ---
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

    text = master.read_text(encoding="utf-8")

    # Per-step evidence for executed §8 steps
    for step in _parse_executed_steps(text):
        errors.extend(validate_execute_step(task_dir, step, repo_root=repo_root))

    sec12_match = re.search(r"## 12\.[\s\S]*?(?=\n## |\Z)", text)
    if sec12_match:
        sec12 = sec12_match.group(0)
        for skill in (
            "test-driven-development",
            "incremental-implementation",
            "trellis-implement",
        ):
            row = re.search(rf"\|\s*{re.escape(skill)}\s*\|[^\n]+\|", sec12)
            if row and "[x]" not in row.group(0) and "不用" not in row.group(0):
                if "| 必做 |" in row.group(0) or "|必做|" in row.group(0):
                    errors.append(f"MASTER §12 '{skill}' 必做行未勾选 [x]")

    sec11 = re.search(r"## 11\.[\s\S]*?(?=\n## |\Z)", text)
    if sec11 and re.search(r"- \[ \]", sec11.group(0)):
        errors.append("MASTER §11 DoD has unchecked items")

    from .manifest_protocol import validate_execute_boot, validate_manifest_amend_chain

    validate_execute_boot(task_dir, errors)
    validate_manifest_amend_chain(task_dir, errors)
    _validate_loop_handoff(task_dir, repo_root, errors)

    return errors


def _validate_loop_handoff(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from check_task_evidence import check_task_evidence
        from loop_engineering_common import loop_engineering_enabled
    except ImportError:
        return
    if not loop_engineering_enabled(task_dir):
        return
    for err in check_task_evidence(task_dir):
        errors.append(err)
    if not (task_dir / "evidence_index.json").is_file():
        errors.append("missing evidence_index.json (loop handoff)")
    if not (task_dir / "loop_manifest.json").is_file():
        errors.append("missing loop_manifest.json (loop handoff)")


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
