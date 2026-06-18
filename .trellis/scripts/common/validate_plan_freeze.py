"""Validate Plan freeze (protocol v2) and per-phase checkpoints."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

_BOOT_MARKER = "Phase P0 complete"


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


def _first_jsonl_file(jsonl_path: Path) -> str | None:
    try:
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            path = item.get("file") or item.get("path")
            if path:
                return str(path)
    except (json.JSONDecodeError, OSError):
        return None
    return None


def _load_plan_paths(repo_root: Path) -> dict:
    """Load plan-skill-paths.yaml for phase/skill validation."""
    path = repo_root / ".trellis/spec/guides/plan-skill-paths.yaml"
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}

    out: dict = {
        "phases": {},
        "freeze_required_skills": raw.get("freeze_required_skills") or [],
        "freeze_phase3_one_of": raw.get("freeze_phase3_one_of") or [],
        "boot_marker": raw.get("boot_marker") or _BOOT_MARKER,
    }
    for phase, cfg in (raw.get("phases") or {}).items():
        out["phases"][str(phase)] = cfg or {}
    return out


def _load_skill_reads(task_dir: Path) -> list[dict]:
    path = task_dir / "research" / "plan-skill-reads.jsonl"
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


def _skills_from_reads(reads: list[dict]) -> set[str]:
    return {str(r.get("skill", "")).strip() for r in reads if r.get("skill")}


def validate_plan_phase(task_dir: Path, phase: str, *, repo_root: Path | None = None) -> list[str]:
    """Validate one Plan phase checkpoint (protocol v2)."""
    if repo_root is None:
        repo_root = _find_repo_root(task_dir)

    errors: list[str] = []
    cfg = _load_plan_paths(repo_root)
    phases = cfg.get("phases", {})
    if phase not in phases:
        valid = ", ".join(sorted(phases.keys()))
        errors.append(f"Unknown plan phase {phase!r} (valid: {valid})")
        return errors

    phase_cfg = phases[phase]
    reads = _load_skill_reads(task_dir)
    read_skills = _skills_from_reads(reads)

    for skill in phase_cfg.get("skills", []):
        if skill not in read_skills:
            errors.append(f"plan-skill-reads.jsonl missing skill for phase {phase}: {skill}")

    skills_any = phase_cfg.get("skills_any", [])
    if skills_any and not read_skills.intersection(set(skills_any)):
        errors.append(
            f"plan-skill-reads.jsonl missing one of {skills_any} for phase {phase}"
        )

    for rel in phase_cfg.get("artifacts", []):
        if not (task_dir / rel).is_file():
            errors.append(f"Phase {phase} missing artifact: {rel}")

    artifacts_any = phase_cfg.get("artifacts_any", [])
    if artifacts_any and not any((task_dir / rel).is_file() for rel in artifacts_any):
        errors.append(f"Phase {phase} missing one of artifacts: {artifacts_any}")

    if phase == "boot":
        marker = cfg.get("boot_marker", _BOOT_MARKER)
        boot = task_dir / "research" / "plan-boot.md"
        if not boot.is_file():
            errors.append("Missing research/plan-boot.md")
        elif marker not in boot.read_text(encoding="utf-8"):
            errors.append(f"plan-boot.md must contain {marker!r}")

    return errors


def _find_repo_root(task_dir: Path) -> Path:
    repo_root = task_dir
    while repo_root.name and not (repo_root / ".trellis").is_dir():
        if repo_root.parent == repo_root:
            break
        repo_root = repo_root.parent
    return repo_root


def validate_plan_freeze(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Return validation errors; empty list means pass."""
    if repo_root is None:
        repo_root = _find_repo_root(task_dir)

    errors: list[str] = []
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return errors

    cfg = _load_plan_paths(repo_root)
    boot_marker = cfg.get("boot_marker", _BOOT_MARKER)

    boot = task_dir / "research" / "plan-boot.md"
    if not boot.is_file():
        errors.append("Missing research/plan-boot.md (Plan Phase P0 boot)")
    elif boot_marker not in boot.read_text(encoding="utf-8"):
        errors.append(f"plan-boot.md must contain {boot_marker!r}")

    ov = task_dir / "research" / "project-overview.md"
    if not ov.is_file():
        errors.append("Missing research/project-overview.md (Plan Phase 1a)")

    gnx = task_dir / "research" / "gitnexus-summary.md"
    if not gnx.is_file():
        errors.append("Missing research/gitnexus-summary.md (Plan Phase 1b)")

    reads_path = task_dir / "research" / "plan-skill-reads.jsonl"
    if not reads_path.is_file():
        errors.append("Missing research/plan-skill-reads.jsonl (Plan skill Read audit log)")
    else:
        reads = _load_skill_reads(task_dir)
        if not reads:
            errors.append("plan-skill-reads.jsonl has no valid JSON lines")
        read_skills = _skills_from_reads(reads)
        for skill in cfg.get("freeze_required_skills", []):
            if skill not in read_skills:
                errors.append(f"plan-skill-reads.jsonl missing required skill: {skill}")
        one_of = cfg.get("freeze_phase3_one_of", [])
        if one_of and not read_skills.intersection(set(one_of)):
            errors.append(f"plan-skill-reads.jsonl missing Phase 3 skill (one of {one_of})")

    text = master.read_text(encoding="utf-8")
    placeholders = re.findall(r"\{\{[^}]+\}\}", text)
    if placeholders:
        uniq = sorted(set(placeholders))[:8]
        errors.append(f"MASTER.plan.md unresolved placeholders: {uniq}")

    section8 = _extract_section(text, "8.")
    if section8:
        legacy = "TDD 全文" in section8 or "legacy-execute-evidence" in text
        if not legacy:
            for label in ("RED 命令", "GREEN 命令", "RED 证据", "GREEN 证据"):
                if label not in section8:
                    errors.append(f"MASTER §8 missing column: {label}")
            test_defs = re.findall(r"def test_\w+", section8)
            if len(test_defs) > 2:
                errors.append(
                    f"MASTER §8 embeds {len(test_defs)} test functions; "
                    "move bodies to research/ (max 2 tracer examples in MASTER)"
                )
        elif not list(task_dir.glob("research/*evidence*.md")):
            errors.append(
                "Legacy MASTER §8 (TDD 全文): require research/*evidence*.md for Execute"
            )

    impl_jsonl = task_dir / "implement.jsonl"
    if impl_jsonl.is_file():
        first = _first_jsonl_file(impl_jsonl)
        if first and "MASTER.plan" not in first.replace("\\", "/"):
            errors.append(
                f"implement.jsonl first entry must be MASTER.plan.md (got {first!r})"
            )

    audit = task_dir / "AUDIT.plan.md"
    if audit.is_file():
        audit_text = audit.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", audit_text):
            errors.append("AUDIT.plan.md has unresolved {{placeholders}}")

    freeze = task_dir / "plan.freeze.md"
    if not freeze.is_file():
        errors.append("plan.freeze.md missing (required when MASTER.plan.md exists)")
    else:
        sec3 = _extract_section(freeze.read_text(encoding="utf-8"), "3.")
        if sec3 and re.search(r"- \[ \]", sec3):
            errors.append("plan.freeze.md §3 has unchecked items")

    return errors


def cmd_validate_plan_freeze(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_plan_freeze(task_dir, repo_root)
    if errors:
        print(colored("Plan freeze validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        if getattr(args, "force", False):
            print(colored("Continuing due to --force", Colors.YELLOW))
            return 0
        return 1

    print(colored("Plan freeze validation passed", Colors.GREEN))
    return 0


def cmd_validate_plan_phase(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_plan_phase(task_dir, args.phase, repo_root=repo_root)
    if errors:
        print(colored(f"Plan phase {args.phase} validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1

    print(colored(f"Plan phase {args.phase} validation passed", Colors.GREEN))
    return 0
