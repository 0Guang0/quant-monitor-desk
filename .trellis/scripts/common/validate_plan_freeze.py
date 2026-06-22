"""Validate Plan freeze and per-phase checkpoints.

This validator follows the three-layer context model:
Design/rules/contracts/definitions -> docs/implementation_tasks original task cards
-> .trellis/tasks frozen plans and manifests -> Execute/Audit/Repair.

Original task cards are Plan-phase inputs. Execute/Audit manifests should list only the
frozen plan plus source documents that cannot be safely summarized.
"""

from __future__ import annotations

import json
import re
import sys
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


def _load_plan_paths(repo_root: Path) -> dict:
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


def _load_jsonl_entries(path: Path) -> list[dict]:
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


def _load_skill_reads(task_dir: Path) -> list[dict]:
    return _load_jsonl_entries(task_dir / "research" / "plan-skill-reads.jsonl")


def _skills_from_reads(reads: list[dict]) -> set[str]:
    return {str(r.get("skill", "")).strip() for r in reads if r.get("skill")}


def _path_from_entry(entry: dict) -> str | None:
    for key in ("path", "file"):
        val = entry.get(key)
        if val:
            return str(val).replace("\\", "/")
    return None


def _paths_from_jsonl(path: Path) -> list[str]:
    return [p for p in (_path_from_entry(e) for e in _load_jsonl_entries(path)) if p]


def _first_jsonl_file(jsonl_path: Path) -> str | None:
    paths = _paths_from_jsonl(jsonl_path)
    return paths[0] if paths else None


def _master_analysis_waiver(task_dir: Path) -> bool:
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return False
    text = master.read_text(encoding="utf-8")
    return bool(re.search(r"analysis_waiver\s*\|\s*`?true`?", text, re.I))


def _find_repo_root(task_dir: Path) -> Path:
    repo_root = task_dir
    while repo_root.name and not (repo_root / ".trellis").is_dir():
        if repo_root.parent == repo_root:
            break
        repo_root = repo_root.parent
    return repo_root


def _path_exists(task_dir: Path, repo_root: Path, rel: str) -> bool:
    norm = rel.replace("\\", "/")
    if norm.startswith((".trellis/", ".cursor/")):
        return True
    if norm.startswith(("docs/", "specs/", "backend/", "frontend/", "scripts/", "tests/", "configs/")):
        return (repo_root / norm).is_file() or (repo_root / norm).is_dir()
    # Repo-root entry files (README.md, MIGRATION_MAP.md, …)
    if "/" not in norm:
        root_candidate = repo_root / norm
        if root_candidate.is_file() or root_candidate.is_dir():
            return True
    return (task_dir / norm).is_file() or (task_dir / norm).is_dir()


def _is_original_task_card(path: str) -> bool:
    norm = path.replace("\\", "/")
    return norm.startswith("docs/implementation_tasks/") and bool(
        re.search(r"/\d{3}[A-Z]?_", norm)
    )


def _strict_source_context_enabled(task_dir: Path) -> bool:
    data_path = task_dir / "task.json"
    if not data_path.is_file():
        return False
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    meta = data.get("meta") or {}
    return str(meta.get("context_bridge_version", "")) == "1"


def _master_allows_original_task_cards(master_text: str) -> bool:
    return "must read original" in master_text or "必须读原文" in master_text


def _validate_original_plan_artifacts(task_dir: Path, errors: list[str]) -> None:
    trace = task_dir / "research" / "original-plan-trace.md"
    if not trace.is_file():
        errors.append("Missing research/original-plan-trace.md (Plan P0 original plan trace)")

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
        if _strict_source_context_enabled(task_dir) and "Source Context Index" not in text:
            errors.append("MASTER.plan.md missing Source Context Index")


def _validate_implement_jsonl_manifest(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    impl_jsonl = task_dir / "implement.jsonl"
    if not impl_jsonl.is_file():
        return

    paths = _paths_from_jsonl(impl_jsonl)
    if not paths:
        errors.append("implement.jsonl has no readable file/path entries")
        return

    first = paths[0].replace("\\", "/")
    if "MASTER.plan.md" not in first:
        errors.append(f"implement.jsonl first entry must be MASTER.plan.md (got {first!r})")

    master = task_dir / "MASTER.plan.md"
    master_text = master.read_text(encoding="utf-8") if master.is_file() else ""
    allow_original = _master_allows_original_task_cards(master_text)

    for rel in paths:
        norm = rel.replace("\\", "/")
        if _strict_source_context_enabled(task_dir) and _is_original_task_card(norm) and not allow_original:
            errors.append(
                f"implement.jsonl references original task card without explicit MASTER must-read marker: {norm}"
            )
        if not _path_exists(task_dir, repo_root, norm):
            errors.append(f"implement.jsonl references missing file: {norm}")


def _validate_audit_manifest(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    audit_plan = task_dir / "AUDIT.plan.md"
    audit_text = audit_plan.read_text(encoding="utf-8") if audit_plan.is_file() else ""
    if _strict_source_context_enabled(task_dir) and audit_plan.is_file() and "Audit Source Trace" not in audit_text:
        errors.append("AUDIT.plan.md missing Audit Source Trace")

    for manifest_name in ("audit.jsonl", "check.jsonl"):
        manifest = task_dir / manifest_name
        if not manifest.is_file():
            continue
        paths = _paths_from_jsonl(manifest)
        allow_original = "must read original" in audit_text or "必须读原文" in audit_text
        for rel in paths:
            norm = rel.replace("\\", "/")
            if _strict_source_context_enabled(task_dir) and _is_original_task_card(norm) and not allow_original:
                errors.append(
                    f"{manifest_name} references original task card without explicit AUDIT.plan must-read marker: {norm}"
                )
            if not _path_exists(task_dir, repo_root, norm):
                errors.append(f"{manifest_name} references missing file: {norm}")


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
    """Validate one Plan phase checkpoint."""
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
        errors.append(f"plan-skill-reads.jsonl missing one of {skills_any} for phase {phase}")

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
                    f"MASTER §8 embeds {len(test_defs)} test functions; move bodies to research/ (max 2 tracer examples in MASTER)"
                )
        elif not list(task_dir.glob("research/*evidence*.md")):
            errors.append("Legacy MASTER §8 (TDD 全文): require research/*evidence*.md for Execute")

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

    _validate_original_plan_artifacts(task_dir, errors)
    _validate_implement_jsonl_manifest(task_dir, repo_root, errors)
    _validate_audit_manifest(task_dir, repo_root, errors)
    _validate_plan_freeze_template(task_dir, errors)

    from .manifest_protocol import validate_manifest_freeze

    validate_manifest_freeze(task_dir, repo_root, errors)
    errors.extend(_deprecated_loop_meta_errors(task_dir, repo_root))
    _validate_loop_engineering_freeze(task_dir, repo_root, errors)
    _validate_repo_loop_gates(repo_root, errors)
    return errors


def validate_plan_freeze_warnings(task_dir: Path, repo_root: Path) -> list[str]:
    """Non-blocking freeze warnings (authority_graph gaps, etc.)."""
    warnings: list[str] = []
    if not (task_dir / "MASTER.plan.md").is_file():
        return warnings
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from loop_engineering_common import authority_graph_coverage_gaps, loop_required
    except ImportError:
        return warnings
    if not loop_required(task_dir):
        return warnings
    for path in authority_graph_coverage_gaps(task_dir):
        warnings.append(f"authority_graph gap: {path} — add specs/context/authority_graph.yaml entry")
    return warnings


def _deprecated_loop_meta_errors(task_dir: Path, repo_root: Path) -> list[str]:
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from loop_engineering_common import deprecated_loop_meta_errors
    except ImportError:
        return []
    return deprecated_loop_meta_errors(task_dir)


def _validate_repo_loop_gates(repo_root: Path, errors: list[str]) -> None:
    """ponytail: reuse existing check scripts at freeze — no duplicate gate logic."""
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from check_docs_specs_indexed import check_migration_map_coverage
        from check_test_catalog import check_catalog
        from check_verification_matrix import check_matrix
    except ImportError:
        return
    for err in check_catalog():
        errors.append(f"repo test_catalog: {err}")
    for err in check_matrix():
        errors.append(f"repo verification_matrix: {err}")
    for err in check_migration_map_coverage():
        errors.append(f"repo docs_specs_index: {err}")


def _validate_loop_engineering_freeze(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    """Complex tasks (task_track=complex): auto-generate + validate loop artifacts."""
    if not (repo_root / "specs/context/authority_graph.yaml").is_file():
        return
    if not (task_dir / "MASTER.plan.md").is_file():
        return
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from context_router import generate_task_loop_artifacts
        from loop_engineering_common import loop_required, loop_engineering_enabled, validate_context_pack
    except ImportError:
        return

    if not loop_required(task_dir):
        return

    pack_path = task_dir / "context_pack.json"
    if not pack_path.is_file():
        for err in generate_task_loop_artifacts(task_dir):
            errors.append(f"context_router: {err}")
        if not pack_path.is_file():
            errors.append("missing context_pack.json after context_router")
            return

    try:
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        errors.append("context_pack.json is invalid JSON")
        return
    for err in validate_context_pack(pack):
        errors.append(err)
    impl = task_dir / "implement.jsonl"
    if impl.is_file():
        paths = _paths_from_jsonl(impl)
        loop_on = loop_engineering_enabled(task_dir)
        if loop_on and len(paths) >= 2 and "context_pack.json" not in paths[1]:
            errors.append(
                "implement.jsonl slot 2 must be context_pack.json when loop engineering is enabled"
            )
        if len(paths) >= 2 and loop_on and "trellis-execute" not in paths[2]:
            if not any("trellis-execute" in p for p in paths[:4]):
                errors.append(
                    "implement.jsonl must include trellis-execute/SKILL.md within first 4 entries"
                )


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
    warnings = validate_plan_freeze_warnings(task_dir, repo_root)
    if warnings:
        print(colored("Plan freeze warnings:", Colors.YELLOW))
        for warn in warnings:
            print(f"  ! {warn}")
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
