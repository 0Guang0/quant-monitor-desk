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
_CONSOLIDATION_MARKER = "Phase 5e complete"
_PRD_THIN_MAX_LINES = 25

# research drafts that must appear in plan-consolidation.md when present
_CONSOLIDATION_DRAFTS = (
    "plan-boot.md",
    "brainstorm-session.md",
    "spec-driven-development-notes.md",
    "to-issues-slices.md",
    "project-overview.md",
    "grill-me-session.md",
    "interview-me-session.md",
    "grill-with-docs-session.md",
    "gitnexus-summary.md",
    "integration-ledger.md",
    "integration-audit.md",
)
_CONSOLIDATION_STATUS = re.compile(r"\b(merged|pointer|n/a)\b", re.IGNORECASE)
# Execute never reads these; pointer is only for Audit-phase trace (e.g. integration-audit).
_POINTER_ALLOWED_DRAFTS = frozenset({"integration-audit.md"})
_TRIAD_EXECUTE_HINT = re.compile(
    r"(三件套|execute\s*不读|execute\s*禁止读|plan-only\s*草稿|plan\s*draft)",
    re.IGNORECASE,
)


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


def _extract_subsection(text: str, heading_marker: str) -> str:
    """Block under ### 1.5 … until next ### or ##."""
    lines = text.splitlines()
    start: int | None = None
    for i, line in enumerate(lines):
        if heading_marker in line and line.strip().startswith("#"):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("## ") or (s.startswith("### ") and heading_marker not in s):
            end = j
            break
    return "\n".join(lines[start:end])


def _validate_stop_conditions(master_text: str, errors: list[str]) -> None:
    """§1.5: examples 1–4 are not enough; need row #≥5 or explicit 自定义."""
    sec = _extract_section(master_text, "1.5") or _extract_subsection(master_text, "1.5")
    if not sec:
        return
    has_custom = bool(re.search(r"\|\s*5\+?\s*\|", sec)) or "自定义" in sec
    numbered = re.findall(r"^\|\s*(\d+)\s*\|", sec, re.MULTILINE)
    has_fifth = any(int(n) >= 5 for n in numbered if n.isdigit())
    if not (has_custom or has_fifth):
        errors.append(
            "MASTER §1.5: add ≥1 custom stop condition (row #≥5 or 自定义 column); "
            "examples 1–4 alone are insufficient"
        )


def _manifest_protocol_enabled_v4(task_dir: Path) -> bool:
    from .plan_protocol import load_task_json, plan_protocol_version

    if plan_protocol_version(task_dir) == "4":
        ver = str((load_task_json(task_dir).get("meta") or {}).get("manifest_protocol_version", ""))
        return ver in ("1", "2", "3", "4", "")
    return False


def _validate_original_plan_artifacts(task_dir: Path, errors: list[str]) -> None:
    from .plan_protocol import plan_protocol_version

    if plan_protocol_version(task_dir) == "4":
        if not (task_dir / "EXECUTION_INDEX.md").is_file():
            errors.append("Missing EXECUTION_INDEX.md (v4 index)")
        boot = task_dir / "research" / "plan-boot.md"
        if boot.is_file():
            boot_text = boot.read_text(encoding="utf-8")
            if "原计划已读" not in boot_text and "原计划" not in boot_text:
                errors.append("plan-boot.md must document original plan read (原计划已读)")
        return

    source = task_dir / "research" / "source-index.md"
    trace = task_dir / "research" / "original-plan-trace.md"
    if not source.is_file() and not trace.is_file():
        errors.append(
            "Missing research/source-index.md (or legacy original-plan-trace.md)"
        )

    boot = task_dir / "research" / "plan-boot.md"
    if boot.is_file():
        boot_text = boot.read_text(encoding="utf-8")
        if "原计划已读" not in boot_text and "原计划" not in boot_text:
            errors.append("plan-boot.md must document original plan read (原计划已读)")

    master = task_dir / "MASTER.plan.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8")
        if "原计划" not in text and "source-index" not in text.lower():
            errors.append(
                "MASTER.plan.md missing original plan linkage (原计划 / source-index)"
            )
        if "### 1.6" not in text and "§1.6" not in text and "### 1.3" not in text:
            errors.append("MASTER.plan.md missing §1.6 original plan merge table")
        if "### 1.5" not in text and "停止条件" not in text:
            errors.append("MASTER.plan.md missing §1.5 stop conditions (停止条件)")
        else:
            _validate_stop_conditions(text, errors)
        if "### 5.1" in text or "测试契约" in text:
            for label in ("测试文件路径", "测试目的", "成功怎么测", "失败怎么测"):
                if label not in text:
                    errors.append(f"MASTER §5 test contract missing: {label}")
        if _strict_source_context_enabled(task_dir) and "Source Context Index" not in text:
            if "source-index" not in text.lower():
                errors.append("MASTER.plan.md missing source-index linkage")


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


def _ordered_plan_phases(phases: dict | set[str]) -> list[str]:
    keys = set(phases.keys()) if isinstance(phases, dict) else set(phases)
    order = (
        "boot",
        "P0-index",
        "1a",
        "2a",
        "2b",
        "3",
        "3.5",
        "1b",
        "4",
        "5a",
        "5b",
        "5c",
        "5d",
        "5e",
    )
    out = [p for p in order if p in keys]
    out.extend(sorted(keys - set(out)))
    return out


def plan_phase_help(repo_root: Path | None = None) -> str:
    """CLI help for validate-plan-phase; phase ids from plan-skill-paths.yaml."""
    if repo_root is None:
        repo_root = _find_repo_root(Path.cwd())
    phases = _load_plan_paths(repo_root).get("phases", {})
    return "Plan phase id: " + ", ".join(_ordered_plan_phases(phases))


def validate_plan_phase(task_dir: Path, phase: str, *, repo_root: Path | None = None) -> list[str]:
    """Validate one Plan phase checkpoint."""
    if repo_root is None:
        repo_root = _find_repo_root(task_dir)

    errors: list[str] = []
    cfg = _load_plan_paths(repo_root)
    phases = cfg.get("phases", {})
    if phase not in phases:
        valid = ", ".join(_ordered_plan_phases(phases))
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

    if phase in ("P0i", "P0-index"):
        from .manifest_protocol import validate_manifest_phase_p0i

        validate_manifest_phase_p0i(task_dir, repo_root, errors)

    if phase == "5c":
        from .manifest_protocol import validate_manifest_phase_5c

        validate_manifest_phase_5c(task_dir, repo_root, errors)

    if phase == "5e":
        _validate_plan_consolidation_v4(task_dir, errors)
        _validate_prd_thin_index_v4(task_dir, errors)
        _validate_execution_index_section4_v4(task_dir, errors)

    return errors


def _consolidation_status_for_draft(consolidation_text: str, draft_name: str) -> str | None:
    for line in consolidation_text.splitlines():
        if draft_name not in line or "|" not in line:
            continue
        match = _CONSOLIDATION_STATUS.search(line)
        if match:
            return match.group(1).lower()
    return None


def _consolidation_table_rows(sec4: str) -> list[str]:
    rows: list[str] = []
    for line in sec4.splitlines():
        if "|" not in line:
            continue
        stripped = line.strip()
        if stripped.startswith("|--") or stripped.startswith("| --"):
            continue
        if stripped.startswith("| 来源") or stripped.startswith("| ---"):
            continue
        if stripped.count("|") >= 3:
            rows.append(stripped)
    return rows


def _validate_plan_consolidation_v4(task_dir: Path, errors: list[str]) -> None:
    consolidation = task_dir / "research" / "plan-consolidation.md"
    if not consolidation.is_file():
        errors.append("Missing research/plan-consolidation.md (Plan Phase 5e)")
        return
    text = consolidation.read_text(encoding="utf-8")
    if _CONSOLIDATION_MARKER not in text:
        errors.append(f"plan-consolidation.md must contain {_CONSOLIDATION_MARKER!r}")

    research = task_dir / "research"
    index_path = task_dir / "EXECUTION_INDEX.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
    sec4 = _extract_section(index_text, "4.")
    sec6 = _extract_section(index_text, "6.")
    present_drafts: list[str] = []

    for name in _CONSOLIDATION_DRAFTS:
        if not (research / name).is_file():
            continue
        present_drafts.append(name)
        if name not in text:
            errors.append(
                f"plan-consolidation.md must list research/{name} with merged|pointer|n/a"
            )
            continue
        status = _consolidation_status_for_draft(text, name)
        if status is None:
            errors.append(
                f"plan-consolidation.md: research/{name} missing status merged|pointer|n/a"
            )
            continue
        if status == "pointer" and name not in _POINTER_ALLOWED_DRAFTS:
            errors.append(
                f"Triad gate: research/{name} marked pointer; "
                "merge into frozen (INDEX §4) or INDEX §3 must-read"
            )
        elif status == "merged" and sec4:
            stem = name.removesuffix(".md")
            if name not in sec4 and stem not in sec4:
                errors.append(
                    f"Triad gate: research/{name} merged but missing from INDEX §4"
                )

    for rel in _paths_from_jsonl(task_dir / "implement.jsonl"):
        norm = rel.replace("\\", "/")
        if norm.startswith("research/") or "/research/" in norm:
            errors.append(
                f"Triad gate: implement.jsonl must not list Plan draft {rel!r}"
            )

    if present_drafts and index_text and not _TRIAD_EXECUTE_HINT.search(f"{sec4}\n{sec6}"):
        errors.append(
            "Triad gate: INDEX §4 or §6 must state Execute does not read research/*"
        )

    audit_path = research / "integration-audit.md"
    if audit_path.is_file() and "PASS_WITH_GAPS" in audit_path.read_text(encoding="utf-8"):
        if "Execute" not in text and "GAP" not in text.upper():
            errors.append(
                "integration-audit.md is PASS_WITH_GAPS but plan-consolidation.md "
                "must list remaining Execute GAPs"
            )


def _validate_prd_thin_index_v4(task_dir: Path, errors: list[str]) -> None:
    prd = task_dir / "prd.md"
    if not prd.is_file():
        return
    text = prd.read_text(encoding="utf-8")
    if "thin-index: true" in text.lower():
        return
    if "frozen/" in text and len(text.splitlines()) <= _PRD_THIN_MAX_LINES:
        return
    errors.append(
        "prd.md must be thin index for v4 (≤25 lines with frozen/ reference, "
        "or thin-index: true)"
    )


def _validate_execution_index_section4_v4(task_dir: Path, errors: list[str]) -> None:
    index = task_dir / "EXECUTION_INDEX.md"
    if not index.is_file():
        return
    text = index.read_text(encoding="utf-8")
    sec4 = _extract_section(text, "4.")
    if not sec4:
        errors.append("EXECUTION_INDEX.md missing §4 已并入冻结任务卡")
        return

    research = task_dir / "research"
    has_mergeable_drafts = any(
        (research / name).is_file()
        for name in _CONSOLIDATION_DRAFTS
        if name not in ("integration-audit.md",)
    )
    if has_mergeable_drafts and not _consolidation_table_rows(sec4):
        errors.append(
            "EXECUTION_INDEX.md §4 empty but research drafts exist (Phase 5e inline registry)"
        )


def validate_plan_freeze_v4(task_dir: Path, repo_root: Path) -> list[str]:
    """Plan protocol v4: frozen task card + EXECUTION_INDEX + AUDIT.plan.md."""
    from .execution_index import (
        generate_manifests,
        validate_execution_index_structure,
        validate_frozen_task_card,
        validate_manifests_match_index,
    )
    from .plan_protocol import execute_ssot_rel, plan_protocol_version

    errors: list[str] = []
    if plan_protocol_version(task_dir) != "4":
        return ["internal: validate_plan_freeze_v4 called for non-v4 task"]

    cfg = _load_plan_paths(repo_root)
    boot_marker = cfg.get("boot_marker", _BOOT_MARKER)

    boot = task_dir / "research" / "plan-boot.md"
    if not boot.is_file():
        errors.append("Missing research/plan-boot.md (Plan Phase P0 boot)")
    elif boot_marker not in boot.read_text(encoding="utf-8"):
        errors.append(f"plan-boot.md must contain {boot_marker!r}")

    reads_path = task_dir / "research" / "plan-skill-reads.jsonl"
    if not reads_path.is_file():
        errors.append("Missing research/plan-skill-reads.jsonl")
    else:
        reads = _load_skill_reads(task_dir)
        read_skills = _skills_from_reads(reads)
        for skill in cfg.get("freeze_required_skills", []):
            if skill not in read_skills:
                errors.append(f"plan-skill-reads.jsonl missing required skill: {skill}")
        one_of = cfg.get("freeze_phase3_one_of", [])
        if one_of and not read_skills.intersection(set(one_of)):
            errors.append(f"plan-skill-reads.jsonl missing Phase 3 skill (one of {one_of})")

    validate_execution_index_structure(task_dir, errors)
    validate_frozen_task_card(task_dir, errors)

    _validate_plan_consolidation_v4(task_dir, errors)
    _validate_prd_thin_index_v4(task_dir, errors)
    _validate_execution_index_section4_v4(task_dir, errors)

    audit = task_dir / "AUDIT.plan.md"
    if not audit.is_file():
        errors.append("AUDIT.plan.md missing (v4 requires thin audit matrix)")
    else:
        audit_text = audit.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", audit_text):
            errors.append("AUDIT.plan.md has unresolved {{placeholders}}")
        if "EXECUTION_INDEX" not in audit_text and "execution_index" not in audit_text.lower():
            errors.append("AUDIT.plan.md must reference EXECUTION_INDEX.md (v4 trace)")

    freeze = task_dir / "plan.freeze.md"
    if not freeze.is_file():
        errors.append("plan.freeze.md missing (required for v4 freeze)")
    else:
        freeze_text = freeze.read_text(encoding="utf-8")
        if "3.0v4" not in freeze_text and "协议 v4" not in freeze_text:
            errors.append("plan.freeze.md missing §3.0v4 v4 freeze checklist")
        sec3 = _extract_section(freeze_text, "3.")
        if sec3 and re.search(r"- \[ \]", sec3):
            errors.append("plan.freeze.md §3 has unchecked items")

    gen_errors = generate_manifests(task_dir, repo_root)
    errors.extend(gen_errors)
    validate_manifests_match_index(task_dir, repo_root, errors)

    impl_jsonl = task_dir / "implement.jsonl"
    if impl_jsonl.is_file():
        first = _first_jsonl_file(impl_jsonl)
        frozen_rel = execute_ssot_rel(task_dir, repo_root)
        if frozen_rel and first and frozen_rel not in first and "frozen/" not in (first or ""):
            errors.append(
                f"implement.jsonl first entry must be frozen task card (got {first!r})"
            )
        paths = _paths_from_jsonl(impl_jsonl)
        for rel in paths:
            if not _path_exists(task_dir, repo_root, rel):
                errors.append(f"implement.jsonl references missing file: {rel}")

    audit_jsonl = task_dir / "audit.jsonl"
    if audit_jsonl.is_file():
        first = _first_jsonl_file(audit_jsonl)
        if first and "AUDIT.plan.md" not in first:
            errors.append(f"audit.jsonl first entry must be AUDIT.plan.md (got {first!r})")

    _validate_plan_freeze_template(task_dir, errors)

    from .manifest_protocol import (
        validate_check_subset_implement,
        validate_implement_negative_list,
        validate_plan_manifest_audit,
        validate_trace_implement_sync,
    )

    if _manifest_protocol_enabled_v4(task_dir):
        validate_trace_implement_sync(task_dir, repo_root, errors)
        validate_check_subset_implement(task_dir, errors)
        validate_implement_negative_list(task_dir, errors)
        validate_plan_manifest_audit(task_dir, errors)

    errors.extend(_deprecated_loop_meta_errors(task_dir, repo_root))
    _validate_loop_engineering_freeze_v4(task_dir, repo_root, errors)
    _validate_repo_loop_gates(repo_root, errors)
    return errors


def _validate_loop_engineering_freeze_v4(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """v4 loop: context_pack + implement slots; no MASTER required."""
    if not (repo_root / "specs/context/authority_graph.yaml").is_file():
        return
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from context_router import generate_task_loop_artifacts
        from loop_engineering_common import loop_required, validate_context_pack
    except ImportError:
        return
    if not loop_required(task_dir):
        return
    pack_path = task_dir / "context_pack.json"
    if not pack_path.is_file():
        for err in generate_task_loop_artifacts(task_dir):
            errors.append(f"context_router: {err}")
    if pack_path.is_file():
        try:
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
            for err in validate_context_pack(pack):
                errors.append(err)
        except json.JSONDecodeError:
            errors.append("context_pack.json is invalid JSON")
    impl = task_dir / "implement.jsonl"
    if impl.is_file():
        paths = _paths_from_jsonl(impl)
        if len(paths) >= 3 and "context_pack.json" not in paths[2] and "context_pack.json" not in paths[1]:
            if "context_pack.json" not in paths:
                errors.append("implement.jsonl must include context_pack.json (v4 slot 3)")
        if not any("trellis-execute" in p for p in paths[:5]):
            errors.append(
                "implement.jsonl must include trellis-execute/SKILL.md (v4 boot)"
            )


def validate_plan_freeze(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Return validation errors; empty list means pass."""
    if repo_root is None:
        repo_root = _find_repo_root(task_dir)

    from .plan_protocol import plan_protocol_version

    if plan_protocol_version(task_dir) == "4":
        return validate_plan_freeze_v4(task_dir, repo_root)

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

    section9 = _extract_section(text, "9.")
    section8 = _extract_section(text, "8.")
    section_steps = section9 or section8
    # Legacy plans put Execute steps in §8 and testing tiers in §9; prefer the block with RED/GREEN gates.
    if section9 and not (
        "RED 命令" in section9 or "RED/GREEN" in section9 or "RED / GREEN" in section9
    ):
        if section8 and ("RED 命令" in section8 or "RED/GREEN" in section8):
            section_steps = section8
    if section_steps:
        legacy = "TDD 全文" in section_steps or "legacy-execute-evidence" in text
        if not legacy:
            has_step_gates = (
                ("RED 命令" in section_steps and "GREEN 命令" in section_steps)
                or "RED / GREEN" in section_steps
                or "RED/GREEN" in section_steps
            )
            if not has_step_gates:
                errors.append(
                    "MASTER §9 missing RED/GREEN commands (RED 命令+GREEN 命令 or RED/GREEN column)"
                )
            test_defs = re.findall(r"def test_\w+", section_steps)
            if len(test_defs) > 2:
                errors.append(
                    f"MASTER steps embed {len(test_defs)} test functions; "
                    "move bodies to research/ (max 2 tracer examples in MASTER)"
                )
        elif not list(task_dir.glob("research/*evidence*.md")):
            errors.append("Legacy MASTER steps (TDD 全文): require research/*evidence*.md for Execute")

    section9 = _extract_section(text, "9.")
    if section9:
        plan_skills = (
            "writing-plans",
            "to-issues",
            "planning-and-task-breakdown",
            "trellis-plan",
            "doubt-driven-development",
        )
        for m in re.finditer(r"绑定 Execute Skill\s*\|([^|\n]+)", section9):
            cell = m.group(1)
            for skill in plan_skills:
                if skill in cell:
                    errors.append(f"MASTER §9 binds Plan-only skill in Execute column: {skill}")

    section_slices = _extract_section(text, "8.")
    if section_slices and ("垂直切片" in section_slices or "SLICE-" in section_slices):
        if "交付物" not in section_slices and "完标准" not in section_slices:
            errors.append("MASTER §8 vertical slices missing 交付物/完标准 column")

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
    from .plan_protocol import plan_protocol_version

    has_plan = (task_dir / "MASTER.plan.md").is_file() or (
        plan_protocol_version(task_dir) == "4"
        and (task_dir / "EXECUTION_INDEX.md").is_file()
    )
    if not has_plan:
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
