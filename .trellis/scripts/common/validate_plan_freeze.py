"""Validate Plan freeze (protocol v2) and per-phase checkpoints."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

_BOOT_MARKER = "Phase P0 complete"
_GLOBAL_IMPL_PATHS = (
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md",
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md",
    "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md",
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md",
)
_GLOBAL_IMPL_README = "docs/implementation_tasks/README.md"


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


def _load_impl_jsonl_entries(task_dir: Path) -> list[dict]:
    path = task_dir / "implement.jsonl"
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


def _impl_path_from_entry(entry: dict) -> str | None:
    for key in ("path", "file"):
        val = entry.get(key)
        if val:
            return str(val).replace("\\", "/")
    return None


def _master_analysis_waiver(task_dir: Path) -> bool:
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return False
    text = master.read_text(encoding="utf-8")
    return bool(re.search(r"analysis_waiver\s*\|\s*`?true`?", text, re.I))


def _task_card_ids_from_master(task_dir: Path) -> set[str]:
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return set()
    text = master.read_text(encoding="utf-8")
    return set(re.findall(r"\b(\d{3})_implement_", text))


def _task_card_ids_from_trace(task_dir: Path) -> set[str]:
    trace = task_dir / "research" / "original-plan-trace.md"
    if not trace.is_file():
        return set()
    return set(re.findall(r"\b(\d{3})_implement_", trace.read_text(encoding="utf-8")))


def _required_task_card_ids(task_dir: Path) -> set[str]:
    ids = _task_card_ids_from_master(task_dir) | _task_card_ids_from_trace(task_dir)
    if ids:
        return ids
    for entry in _load_impl_jsonl_entries(task_dir):
        path = _impl_path_from_entry(entry)
        if not path:
            continue
        m = re.search(r"/(\d{3})_implement_", path.replace("\\", "/"))
        if m:
            ids.add(m.group(1))
    return ids


def _validate_original_plan_artifacts(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    trace = task_dir / "research" / "original-plan-trace.md"
    if not trace.is_file():
        errors.append("Missing research/original-plan-trace.md (Plan P0o original plan trace)")

    boot = task_dir / "research" / "plan-boot.md"
    if boot.is_file():
        boot_text = boot.read_text(encoding="utf-8")
        if "原计划已读" not in boot_text and "原计划" not in boot_text:
            errors.append("plan-boot.md must document original plan read (原计划已读)")

    master = task_dir / "MASTER.plan.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8")
        if "原计划" not in text and "original-plan" not in text.lower():
            errors.append("MASTER.plan.md missing original plan linkage (原计划 / §1.3)")
        if "### 1.3" not in text and "§1.3" not in text:
            errors.append("MASTER.plan.md missing §1.3 original plan merge table")


def _validate_implement_jsonl_original_plan(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    impl_jsonl = task_dir / "implement.jsonl"
    if not impl_jsonl.is_file():
        return

    entries = _load_impl_jsonl_entries(task_dir)
    paths = [_impl_path_from_entry(e) for e in entries]
    paths = [p for p in paths if p]

    if not any(p.replace("\\", "/") == _GLOBAL_IMPL_README for p in paths):
        errors.append(f"implement.jsonl missing required index: {_GLOBAL_IMPL_README}")

    for global_rel in _GLOBAL_IMPL_PATHS:
        if not any(p.replace("\\", "/") == global_rel for p in paths):
            errors.append(
                f"implement.jsonl missing required global rule: {global_rel}"
            )
        elif not (repo_root / global_rel).is_file():
            errors.append(f"implement.jsonl references missing file: {global_rel}")

    required_ids = _required_task_card_ids(task_dir)
    if not required_ids:
        errors.append(
            "implement.jsonl missing original task card "
            "(docs/implementation_tasks/.../NNN_*.md)"
        )
    else:
        for card_id in sorted(required_ids):
            pattern = f"/{card_id}_implement_"
            if not any(pattern in p.replace("\\", "/") for p in paths):
                errors.append(
                    f"implement.jsonl missing task card for {card_id} "
                    f"(expected path containing {pattern})"
                )

    for rel in paths:
        norm = rel.replace("\\", "/")
        if norm.startswith("docs/implementation_tasks/") and not (
            repo_root / norm
        ).is_file():
            errors.append(f"implement.jsonl references missing file: {norm}")


def _validate_check_jsonl_original_plan(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    check_path = task_dir / "check.jsonl"
    if not check_path.is_file():
        return
    entries = []
    for line in check_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    paths = []
    for entry in entries:
        for key in ("path", "file"):
            if entry.get(key):
                paths.append(str(entry[key]).replace("\\", "/"))
    for global_rel in _GLOBAL_IMPL_PATHS:
        if not any(p == global_rel for p in paths):
            errors.append(f"check.jsonl missing required global rule: {global_rel}")


def _validate_plan_freeze_template(task_dir: Path, errors: list[str]) -> None:
    freeze = task_dir / "plan.freeze.md"
    if not freeze.is_file():
        return
    text = freeze.read_text(encoding="utf-8")
    if "### 3.0b" not in text and "原计划包门禁" not in text:
        errors.append(
            "plan.freeze.md missing §3.0b original plan package checklist "
            "(use templates/plan.freeze.md or append ### 3.0b)"
        )


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

    if phase == "P0i":
        from .manifest_protocol import validate_manifest_phase_p0i

        validate_manifest_phase_p0i(task_dir, repo_root, errors)

    if phase == "5c":
        from .manifest_protocol import validate_manifest_phase_5c

        validate_manifest_phase_5c(task_dir, repo_root, errors)

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
        if (task_dir / "task.json").is_file():
            errors.append("MASTER.plan.md missing (complex task requires MASTER)")
        return errors

    cfg = _load_plan_paths(repo_root)
    boot_marker = cfg.get("boot_marker", _BOOT_MARKER)
    waiver = _master_analysis_waiver(task_dir)

    boot = task_dir / "research" / "plan-boot.md"
    if not boot.is_file():
        errors.append("Missing research/plan-boot.md (Plan Phase P0 boot)")
    elif boot_marker not in boot.read_text(encoding="utf-8"):
        errors.append(f"plan-boot.md must contain {boot_marker!r}")

    if not waiver:
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

    _validate_original_plan_artifacts(task_dir, repo_root, errors)
    _validate_implement_jsonl_original_plan(task_dir, repo_root, errors)
    _validate_check_jsonl_original_plan(task_dir, repo_root, errors)
    _validate_plan_freeze_template(task_dir, errors)

    from .manifest_protocol import validate_manifest_freeze

    validate_manifest_freeze(task_dir, repo_root, errors)

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
