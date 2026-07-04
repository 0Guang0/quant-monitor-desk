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


from .md_utils import extract_md_section as _extract_section

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
        "freeze_required_skills": raw.get("freeze_required_skills")
        or raw.get("freeze_required_skills_v40_legacy")
        or [],
        "freeze_required_skills_v41": raw.get("freeze_required_skills_v41") or [],
        "freeze_required_skills_v42": raw.get("freeze_required_skills_v42") or [],
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


def _manifest_protocol_enabled_v4(task_dir: Path) -> bool:
    from .plan_protocol import is_plan_protocol_v4, load_task_json

    if not is_plan_protocol_v4(task_dir):
        return False
    ver = str((load_task_json(task_dir).get("meta") or {}).get("manifest_protocol_version", ""))
    return ver != "0"


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
    from .paths import get_repo_root

    if repo_root is None:
        repo_root = get_repo_root()
    phases = _load_plan_paths(repo_root).get("phases", {})
    return "Plan phase id: " + ", ".join(_ordered_plan_phases(phases))


def validate_plan_phase(
    task_dir: Path,
    phase: str,
    *,
    repo_root: Path | None = None,
    allow_archived: bool = False,
) -> list[str]:
    """Validate one Plan phase checkpoint."""
    from .paths import get_repo_root
    from .plan_protocol import is_plan_protocol_v4
    from .task_archive import is_active_legacy_v3, is_archived_task, legacy_freeze_error

    if repo_root is None:
        repo_root = get_repo_root()

    if is_archived_task(task_dir) and not allow_archived:
        return []
    if is_active_legacy_v3(task_dir):
        return [legacy_freeze_error()]
    if phase == "5e" and not is_plan_protocol_v4(task_dir):
        from .plan_protocol import is_execution_bundle_v42

        if is_execution_bundle_v42(task_dir):
            if not (task_dir / "EXECUTION_PLAN.md").is_file():
                return ["plan phase 5e requires EXECUTION_PLAN.md (v4.2)"]
            if not (task_dir / "EXECUTION_INDEX.md").is_file():
                return ["plan phase 5e requires EXECUTION_INDEX.md (v4.2)"]
        else:
            return ["plan phase 5e requires protocol v4/v4.1/v4.2 (EXECUTION_INDEX.md + frozen/)"]

    from .plan_protocol import is_execution_bundle_v42

    if is_execution_bundle_v42(task_dir) and phase != "5e":
        return []

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

    if not is_execution_bundle_v42(task_dir):
        for skill in phase_cfg.get("skills", []):
            if skill not in read_skills:
                errors.append(f"plan-skill-reads.jsonl missing skill for phase {phase}: {skill}")

        skills_any = phase_cfg.get("skills_any", [])
        if skills_any and not read_skills.intersection(set(skills_any)):
            errors.append(f"plan-skill-reads.jsonl missing one of {skills_any} for phase {phase}")

    artifacts_to_check = phase_cfg.get("artifacts", [])
    if phase == "5e":
        from .plan_protocol import is_execution_bundle_v41, is_execution_bundle_v42

        if is_execution_bundle_v42(task_dir):
            artifacts_to_check = phase_cfg.get("artifacts", [])
        elif is_execution_bundle_v41(task_dir):
            artifacts_to_check = phase_cfg.get("legacy_v41_artifacts", [])
        else:
            artifacts_to_check = phase_cfg.get("artifacts", [])

    for rel in artifacts_to_check:
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
        from .plan_protocol import is_execution_bundle_v41, is_execution_bundle_v42

        if is_execution_bundle_v42(task_dir):
            _validate_execution_bundle_v42(task_dir, errors, repo_root=repo_root)
        elif is_execution_bundle_v41(task_dir):
            _validate_execution_bundle_v41(task_dir, errors, repo_root=repo_root)
        if not is_execution_bundle_v42(task_dir):
            _validate_plan_consolidation_v4(task_dir, errors)
        _validate_prd_thin_index_v4(task_dir, errors)
        if not is_execution_bundle_v41(task_dir) and not is_execution_bundle_v42(task_dir):
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


_V42_PLAN_ROOT = "EXECUTION_PLAN.md"
_V41_ENTRY_REL = "research/00-EXECUTION-ENTRY.md"
_V41_EXTERNAL_REL = "research/EXTERNAL-INDEX.md"
_V41_PLAN_ROOT = "EXECUTION_PLAN.md"
_V41_GITNEXUS_ARTIFACTS = ("project-overview.md", "gitnexus-summary.md")
_V41_CLARIFICATION_ARTIFACTS = (
    "grill-me-session.md",
    "interview-me-session.md",
    "grill-with-docs-session.md",
    "idea-refine-session.md",
    "brainstorm-session.md",
)
_V41_BUNDLE_CORE = frozenset(
    {
        "plan-boot.md",
        "00-EXECUTION-ENTRY.md",
        "EXTERNAL-INDEX.md",
        "plan-consolidation.md",
        "project-overview.md",
        "gitnexus-summary.md",
    }
)
_V41_PLAN_ONLY = frozenset({"plan-boot.md", "integration-audit.md", "plan-manifest-audit.md"})
_V41_PHASE5E_SKILL_GATE = frozenset(
    {"gitnexus-plan-1a", "gitnexus-plan-1b", "trellis-research"}
)
_OPEN_QUESTION_UNCHECKED = re.compile(r"^\s*-\s*\[\s\]", re.MULTILINE)


def _freeze_required_skills(cfg: dict, *, protocol: str) -> list[str]:
    key = {
        "4.2": "freeze_required_skills_v42",
        "4.1": "freeze_required_skills_v41",
    }.get(protocol, "freeze_required_skills")
    return list(dict.fromkeys(cfg.get(key) or []))


def _validate_execution_bundle_v41(
    task_dir: Path, errors: list[str], *, repo_root: Path | None = None
) -> None:
    """v4.1 mechanical gate: ENTRY / EXTERNAL / ADR / GitNexus / trellis-research."""
    from .plan_protocol import execution_entry_rel, load_task_json

    if repo_root is None:
        from .paths import get_repo_root

        repo_root = get_repo_root()

    meta = load_task_json(task_dir).get("meta") or {}
    entry_meta = str(meta.get("execute_entry", "")).strip() or _V41_ENTRY_REL
    if entry_meta != _V41_ENTRY_REL:
        errors.append(
            f"task.json meta.execute_entry must be {_V41_ENTRY_REL!r} "
            f"(got {entry_meta!r})"
        )

    entry_path = task_dir / entry_meta.replace("\\", "/")
    if not entry_path.is_file():
        errors.append(f"Missing {_V41_ENTRY_REL} (v4.1 Execute entry)")
        return
    entry_text = entry_path.read_text(encoding="utf-8")

    external_path = task_dir / _V41_EXTERNAL_REL
    if not external_path.is_file():
        errors.append(f"Missing {_V41_EXTERNAL_REL} (v4.1 external index)")
    else:
        ext_text = external_path.read_text(encoding="utf-8")
        for sec in ("§A", "§B", "§C"):
            if sec not in ext_text:
                errors.append(f"EXTERNAL-INDEX.md missing section marker {sec}")

    if not (task_dir / _V41_PLAN_ROOT).is_file():
        errors.append(f"Missing {_V41_PLAN_ROOT} (v4.1 thin plan root)")

    sec4 = _extract_section(entry_text, "4.")
    if not sec4:
        errors.append("00-EXECUTION-ENTRY.md missing §4 ADR index")
    elif "ADR" not in sec4 and "docs/decisions" not in sec4:
        errors.append("00-EXECUTION-ENTRY.md §4 must reference ADR(s) or docs/decisions")

    if not re.search(r"5\.2", entry_text):
        errors.append("00-EXECUTION-ENTRY.md missing §5.2 开工必读")
    if not re.search(r"5\.3", entry_text):
        errors.append("00-EXECUTION-ENTRY.md missing §5.3 情境路由")
    if not re.search(r"5\.1", entry_text):
        errors.append("00-EXECUTION-ENTRY.md missing §5.1 文件地图")

    research = task_dir / "research"
    for name in sorted(p.name for p in research.glob("*.md")):
        if name in _V41_BUNDLE_CORE or name in _V41_PLAN_ONLY:
            continue
        if name not in entry_text:
            errors.append(f"00-EXECUTION-ENTRY.md §5.1 must list research/{name}")

    for artifact in _V41_GITNEXUS_ARTIFACTS:
        if not (research / artifact).is_file():
            errors.append(f"Missing research/{artifact} (GitNexus required)")

    has_trellis_research = bool(list(research.glob("reference-adoption-*.md")))
    if not has_trellis_research:
        for path in research.glob("*.md"):
            if path.name in _V41_BUNDLE_CORE or path.name.startswith("plan-"):
                continue
            if path.name.endswith("-session.md"):
                continue
            has_trellis_research = True
            break
    if not has_trellis_research:
        errors.append(
            "Missing trellis-research output "
            "(research/reference-adoption-*.md or research/<topic>.md)"
        )

    reads = _load_skill_reads(task_dir)
    read_skills = _skills_from_reads(reads)
    for skill in sorted(_V41_PHASE5E_SKILL_GATE):
        if skill not in read_skills:
            errors.append(f"plan-skill-reads.jsonl missing required skill: {skill}")

    _validate_ambiguity_resolution_v41(task_dir, errors)

    entry_rel = execution_entry_rel(task_dir, repo_root)
    impl = task_dir / "implement.jsonl"
    if impl.is_file() and entry_rel:
        paths = _paths_from_jsonl(impl)
        if len(paths) >= 2 and entry_rel not in paths[1].replace("\\", "/"):
            errors.append(
                f"implement.jsonl slot 2 must be {entry_rel!r} (v4.1 Execute entry)"
            )


def _validate_execution_bundle_v42(
    task_dir: Path, errors: list[str], *, repo_root: Path | None = None
) -> None:
    """v4.2: full EXECUTION_PLAN; routing lives in EXECUTION_INDEX.md §3."""
    from .paths import get_repo_root
    from .plan_protocol import execution_entry_rel, execution_index_rel, load_task_json

    if repo_root is None:
        repo_root = get_repo_root()

    meta = load_task_json(task_dir).get("meta") or {}
    if str(meta.get("plan_protocol_version", "")).strip() != "4.2":
        errors.append(
            "task.json meta.plan_protocol_version must be '4.2' (explicit; heuristic does not gate)"
        )
    entry_meta = str(meta.get("execute_entry", "")).strip() or _V42_PLAN_ROOT
    if entry_meta != _V42_PLAN_ROOT:
        errors.append(
            f"task.json meta.execute_entry must be {_V42_PLAN_ROOT!r} (got {entry_meta!r})"
        )

    plan_path = task_dir / _V42_PLAN_ROOT
    if not plan_path.is_file():
        errors.append(f"Missing {_V42_PLAN_ROOT} (v4.2 execute plan SSOT)")
    else:
        plan_text = plan_path.read_text(encoding="utf-8")
        if len(plan_text.strip()) < 200:
            errors.append(
                f"{_V42_PLAN_ROOT} too short for v4.2 (must be substantive plan)"
            )
        if "仅 GAP + 指向 ENTRY" in plan_text:
            errors.append(
                f"{_V42_PLAN_ROOT} must be v4.2 full plan, not v4.1 thin pointer"
            )

    index_path = task_dir / "EXECUTION_INDEX.md"
    if not index_path.is_file():
        errors.append("Missing EXECUTION_INDEX.md (v4.2 machine index)")
    else:
        from .execution_index import parse_manifest_rows

        if not parse_manifest_rows(index_path.read_text(encoding="utf-8")):
            errors.append(
                "EXECUTION_INDEX.md §3 manifest table empty (v4.2 Phase 5e routing)"
            )

    audit_path = task_dir / "AUDIT.plan.md"
    if not audit_path.is_file():
        errors.append("Missing AUDIT.plan.md (v4.2 audit matrix)")

    entry_rel = execution_entry_rel(task_dir, repo_root)
    index_rel = execution_index_rel(task_dir, repo_root)
    impl = task_dir / "implement.jsonl"
    if impl.is_file() and entry_rel:
        paths = _paths_from_jsonl(impl)
        if len(paths) >= 1 and entry_rel not in paths[0].replace("\\", "/"):
            errors.append(
                f"implement.jsonl slot 1 must be {entry_rel!r} (v4.2 Execute plan)"
            )
        if index_rel and len(paths) >= 2 and index_rel not in paths[1].replace("\\", "/"):
            errors.append(
                f"implement.jsonl slot 2 must be {index_rel!r} (v4.2 manifest index)"
            )


def _validate_ambiguity_resolution_v41(task_dir: Path, errors: list[str]) -> None:
    """Open Questions with unchecked items require a clarification artifact or ADR."""
    research = task_dir / "research"
    open_text = ""
    for pattern in ("plan-spec*.md", "plan-task*.md", "plan-implementation*.md"):
        for path in research.glob(pattern):
            open_text += path.read_text(encoding="utf-8") + "\n"
    if "Open Questions" not in open_text and "开放问题" not in open_text:
        return
    if not _OPEN_QUESTION_UNCHECKED.search(open_text):
        return
    has_clarification = any((research / name).is_file() for name in _V41_CLARIFICATION_ARTIFACTS)
    entry = task_dir / _V41_ENTRY_REL
    has_adr = entry.is_file() and "docs/decisions" in entry.read_text(encoding="utf-8")
    if not has_clarification and not has_adr:
        errors.append(
            "Unresolved Open Questions: use grill-me / interview-me / idea-refine / "
            "trellis-brainstorm and write research/*-session.md or ADR"
        )


def _validate_plan_consolidation_v4(task_dir: Path, errors: list[str]) -> None:
    from .plan_protocol import is_execution_bundle_v41, is_execution_bundle_v42

    if is_execution_bundle_v42(task_dir):
        return
    v41 = is_execution_bundle_v41(task_dir)
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

    if v41:
        skip_self = _V41_BUNDLE_CORE | {"plan-consolidation.md"} | _V41_PLAN_ONLY
        for path in sorted(research.glob("*.md")):
            name = path.name
            if name in skip_self:
                continue
            if name not in text and name.removesuffix(".md") not in text:
                errors.append(
                    f"plan-consolidation.md must register research/{name} (v4.1 bundle)"
                )
    else:
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
        if not v41 and (
            norm.startswith("research/") or "/research/" in norm
        ):
            errors.append(
                f"Triad gate: implement.jsonl must not list Plan draft {rel!r}"
            )

    if not v41 and present_drafts and index_text and not _TRIAD_EXECUTE_HINT.search(
        f"{sec4}\n{sec6}"
    ):
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
    from .plan_protocol import (
        execute_ssot_rel,
        is_execution_bundle_v41,
        is_execution_bundle_v42,
        is_plan_protocol_v4,
        plan_protocol_version,
    )

    errors: list[str] = []
    if not is_plan_protocol_v4(task_dir):
        return ["internal: validate_plan_freeze_v4 called for non-v4 task"]

    protocol = plan_protocol_version(task_dir)
    v42 = is_execution_bundle_v42(task_dir)
    v41 = is_execution_bundle_v41(task_dir)

    cfg = _load_plan_paths(repo_root)
    boot_marker = cfg.get("boot_marker", _BOOT_MARKER)

    if not v42:
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
            if v41:
                required = _freeze_required_skills(cfg, protocol="4.1")
            else:
                required = _freeze_required_skills(cfg, protocol="4")
                one_of = cfg.get("freeze_phase3_one_of", [])
                if one_of and not read_skills.intersection(set(one_of)):
                    errors.append(
                        f"plan-skill-reads.jsonl missing Phase 3 skill (one of {one_of})"
                    )
            for skill in required:
                if skill not in read_skills:
                    errors.append(f"plan-skill-reads.jsonl missing required skill: {skill}")

    validate_execution_index_structure(task_dir, errors)
    if not v42:
        validate_frozen_task_card(task_dir, errors)

    if v42:
        _validate_execution_bundle_v42(task_dir, errors, repo_root=repo_root)
    elif v41:
        _validate_execution_bundle_v41(task_dir, errors, repo_root=repo_root)
    if not v42:
        _validate_plan_consolidation_v4(task_dir, errors)
        _validate_prd_thin_index_v4(task_dir, errors)
    if not v41 and not v42:
        _validate_execution_index_section4_v4(task_dir, errors)

    audit = task_dir / "AUDIT.plan.md"
    if not audit.is_file():
        errors.append("AUDIT.plan.md missing (v4 requires thin audit matrix)")
    else:
        audit_text = audit.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", audit_text):
            errors.append("AUDIT.plan.md has unresolved {{placeholders}}")
        trace_ok = (
            "EXECUTION_INDEX" in audit_text
            or "execution_index" in audit_text.lower()
            or (v42 and "EXECUTION_PLAN" in audit_text)
            or (v41 and "00-EXECUTION-ENTRY" in audit_text)
        )
        if not trace_ok:
            errors.append(
                "AUDIT.plan.md must reference EXECUTION_INDEX.md or "
                "EXECUTION_PLAN.md (v4.2) / 00-EXECUTION-ENTRY.md (v4.1 trace)"
            )

    freeze = task_dir / "plan.freeze.md"
    if not v42:
        if not freeze.is_file():
            errors.append("plan.freeze.md missing (required for v4 freeze)")
        else:
            freeze_text = freeze.read_text(encoding="utf-8")
            if v41:
                if "3.0v4.1" not in freeze_text and "协议 v4.1" not in freeze_text:
                    errors.append("plan.freeze.md missing §3.0v4.1 v4.1 freeze checklist")
            elif "3.0v4" not in freeze_text and "协议 v4" not in freeze_text:
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
        ssot_rel = execute_ssot_rel(task_dir, repo_root)
        if ssot_rel and first and ssot_rel not in first.replace("\\", "/"):
            label = "EXECUTION_PLAN.md" if v42 else "frozen task card"
            errors.append(
                f"implement.jsonl first entry must be {label} (got {first!r})"
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

    if not v42:
        _validate_plan_freeze_template(task_dir, errors)

    from .manifest_protocol import validate_manifest_freeze_v4

    if _manifest_protocol_enabled_v4(task_dir) and not v42:
        validate_manifest_freeze_v4(task_dir, repo_root, errors)

    errors.extend(_deprecated_loop_meta_errors(task_dir, repo_root))
    if not v42:
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
        from loop_engineering_common import infer_task_touched_paths, loop_required, validate_context_pack
    except ImportError as exc:
        errors.append(f"loop_engineering import failed: {exc}")
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
            if not (pack.get("modules") or pack.get("source_authorities")):
                touched = infer_task_touched_paths(task_dir)
                if any(p.startswith(("backend/", "scripts/")) for p in touched):
                    errors.append(
                        "context_pack.json has empty modules/source_authorities "
                        "(re-run context_router --task)"
                    )
        except json.JSONDecodeError:
            errors.append("context_pack.json is invalid JSON")
    impl = task_dir / "implement.jsonl"
    if impl.is_file():
        paths = _paths_from_jsonl(impl)
        if not any(p.endswith("context_pack.json") for p in paths):
            errors.append("implement.jsonl must include context_pack.json (v4 slot 3)")
        if not any("trellis-execute" in p for p in paths[:5]):
            errors.append(
                "implement.jsonl must include trellis-execute/SKILL.md (v4 boot)"
            )


def validate_plan_freeze(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    """Return validation errors; empty list means pass."""
    from .paths import get_repo_root
    from .plan_protocol import is_plan_protocol_v4, load_task_json
    from .task_archive import (
        has_task_plan_artifacts,
        is_active_legacy_v3,
        is_archived_task,
        legacy_freeze_error,
    )

    if repo_root is None:
        repo_root = get_repo_root()

    if is_archived_task(task_dir):
        return []

    if not (task_dir / "task.json").is_file():
        if has_task_plan_artifacts(task_dir):
            return ["missing task.json (required when plan artifacts present)"]
        return []

    meta = load_task_json(task_dir).get("meta") or {}
    track = str(meta.get("task_track", "")).lower()
    if track in ("debt-lite", "simple") and not is_plan_protocol_v4(task_dir):
        return []

    if is_plan_protocol_v4(task_dir):
        return validate_plan_freeze_v4(task_dir, repo_root)

    if is_active_legacy_v3(task_dir):
        return [legacy_freeze_error()]

    meta = load_task_json(task_dir).get("meta") or {}
    if str(meta.get("plan_protocol_version", "")).strip() == "3":
        has_v4 = (task_dir / "EXECUTION_INDEX.md").is_file() and any(
            (task_dir / "frozen").glob("*.md")
        )
        if has_v4:
            return [
                "plan_protocol_version 3 conflicts with EXECUTION_INDEX.md + frozen/ "
                "(set meta to 4/4.1 or archive v3)"
            ]
    return []


def validate_plan_freeze_warnings(task_dir: Path, repo_root: Path) -> list[str]:
    """Non-blocking freeze warnings (authority_graph gaps, etc.)."""
    warnings: list[str] = []
    from .plan_protocol import is_plan_protocol_v4

    has_plan = is_plan_protocol_v4(task_dir) and (task_dir / "EXECUTION_INDEX.md").is_file()
    if not has_plan:
        return warnings
    scripts = repo_root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from loop_engineering_common import authority_graph_coverage_gaps, loop_required
    except ImportError as exc:
        warnings.append(f"loop_engineering import failed: {exc}")
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
    except ImportError as exc:
        return [f"loop_engineering import failed: {exc}"]
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
    except ImportError as exc:
        errors.append(f"loop_engineering import failed: {exc}")
        return
    for err in check_catalog():
        errors.append(f"repo test_catalog: {err}")
    for err in check_matrix():
        errors.append(f"repo verification_matrix: {err}")
    for err in check_migration_map_coverage():
        errors.append(f"repo docs_specs_index: {err}")


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
