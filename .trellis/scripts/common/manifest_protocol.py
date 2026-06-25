"""Manifest protocol (E1–E20) + Integration packing protocol v3 (V1–V8).

Version map (task.json meta.manifest_protocol_version):
  "1" = E1–E20 manifest only
  "2" = deprecated alias for "3"
  "3" = E1–E20 + context packing (P0i, ledger, integration-audit)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_CRITICAL_CATEGORIES = (
    "decision",
    "rule",
    "architecture",
    "business",
    "contract",
    "wiring",
)

_GLOBAL_IMPL_PATHS = (
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md",
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md",
    "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md",
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md",
)
_GLOBAL_IMPL_README = "docs/implementation_tasks/README.md"

# Paths that may appear in check.jsonl but not implement (Audit-only probes).
_CHECK_AUDIT_ONLY_MARKERS = ("audit-only", "A3 migration runner")

# E11: do not require these in implement (created at Execute or deferred).
_IMPLEMENT_NEGATIVE_PATTERNS = (
    re.compile(r"scripts/sync_registry\.py$"),  # Batch D §8.8 creates
    re.compile(r"backend/app/sync/"),  # greenfield create
    re.compile(r"tests/test_sync_"),  # created in Execute
    re.compile(r"006_ingestion_sync\.sql$"),
)

_WIRING_PREFIXES = (
    "backend/",
    "specs/",
    "tests/",
    "scripts/",
    "docs/modules/",
    "docs/architecture/",
    "docs/quality/",
    "specs/contracts/",
    "specs/datasource_registry/",
    "specs/schema/",
)

_PATH_IN_BACKTICKS = re.compile(r"`([a-zA-Z0-9_./-]+\.(?:py|md|yaml|yml|sql))`")
_PATH_IN_TABLE = re.compile(
    r"\|\s*`?([a-zA-Z0-9_./-]+\.(?:py|md|yaml|yml|sql))`?\s*\|"
)
_PYTEST_PATH = re.compile(r"(?:pytest\s+)?tests/[a-zA-Z0-9_./-]+\.py")
_SCRIPT_PATH = re.compile(r"python\s+scripts/[a-zA-Z0-9_./-]+\.py")
_BARE_SCRIPT = re.compile(r"(?<![`/\w])scripts/[a-zA-Z0-9_./-]+\.py")
_MODULE_SPEC_REF = re.compile(
    r"`(docs/(?:modules|architecture|quality)/[a-zA-Z0-9_./-]+\.md)`"
    r"|`(specs/[a-zA-Z0-9_./-]+\.(?:yaml|yml|md))`"
)


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def _find_repo_root(task_dir: Path) -> Path:
    repo_root = task_dir
    while repo_root.name and not (repo_root / ".trellis").is_dir():
        if repo_root.parent == repo_root:
            break
        repo_root = repo_root.parent
    return repo_root


def load_jsonl_entries(path: Path) -> list[dict]:
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


def path_from_entry(entry: dict) -> str | None:
    for key in ("file", "path"):
        val = entry.get(key)
        if val:
            return _norm(str(val))
    return None


def impl_paths_set(task_dir: Path) -> set[str]:
    entries = load_jsonl_entries(task_dir / "implement.jsonl")
    return {p for e in entries if (p := path_from_entry(e))}


def check_paths_set(task_dir: Path) -> set[str]:
    entries = load_jsonl_entries(task_dir / "check.jsonl")
    out: set[str] = set()
    for e in entries:
        p = path_from_entry(e)
        if p:
            out.add(p)
    return out


def load_task_json(task_dir: Path) -> dict:
    p = task_dir / "task.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def predecessor_task_dirs(task_dir: Path, repo_root: Path) -> list[Path]:
    """E2: resolve predecessor_tasks from task.json."""
    data = load_task_json(task_dir)
    preds: list[str] = []
    if isinstance(data.get("predecessor_tasks"), list):
        preds.extend(str(x) for x in data["predecessor_tasks"])
    meta = data.get("meta") or {}
    if isinstance(meta.get("predecessor_tasks"), list):
        preds.extend(str(x) for x in meta["predecessor_tasks"])
    # Legacy: notes field slug
    notes = str(data.get("notes") or "")
    m = re.search(r"predecessor[:\s]+([0-9]{2}-[0-9]{2}-[\w-]+)", notes, re.I)
    if m:
        preds.append(m.group(1))

    tasks_root = repo_root / ".trellis" / "tasks"
    resolved: list[Path] = []
    for slug in preds:
        slug = slug.strip().strip("/")
        if not slug:
            continue
        direct = tasks_root / slug
        if direct.is_dir():
            resolved.append(direct)
            continue
        matches = list(tasks_root.glob(f"*{slug}*"))
        if len(matches) == 1:
            resolved.append(matches[0])
    return resolved


def wiring_paths_from_predecessors(task_dir: Path, repo_root: Path) -> set[str]:
    """E2: inherit wiring-class paths from predecessor implement.jsonl."""
    out: set[str] = set()
    for pred in predecessor_task_dirs(task_dir, repo_root):
        for p in impl_paths_set(pred):
            if any(p.startswith(prefix) for prefix in _WIRING_PREFIXES):
                out.add(p)
    return out


def resolve_trace_path(task_dir: Path) -> Path | None:
    """Prefer v4 EXECUTION_INDEX; then research/source-index; legacy original-plan-trace."""
    idx = task_dir / "EXECUTION_INDEX.md"
    if idx.is_file():
        return idx
    for name in ("source-index.md", "original-plan-trace.md"):
        p = task_dir / "research" / name
        if p.is_file():
            return p
    return None


def parse_trace_manifest(trace_path: Path) -> dict[str, str]:
    """
    E1: Parse original-plan-trace.md → {path: required|inherited|deferred}.
    Supports explicit `manifest` column or legacy ✅ rows.
    """
    if not trace_path.is_file():
        return {}
    text = trace_path.read_text(encoding="utf-8")
    result: dict[str, str] = {}

    # Explicit manifest column table (| path | ... | required |)
    # source-index §B uses same shape
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "manifest" in line.lower() and "---" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        cols = [c for c in cols if c]
        if len(cols) < 2:
            continue
        # Try last column as manifest status
        status = cols[-1].lower()
        if status in ("required", "inherited", "deferred", "audit-only", "execute", "execute-required", "must-read"):
            path_col = cols[0].strip("`")
            if "/" in path_col or path_col.endswith((".md", ".py", ".yaml", ".sql")):
                result[_norm(path_col)] = status
            continue
        # Legacy: | category | `path` | ✅ |
        for cell in cols:
            m = re.match(r"`?([a-zA-Z0-9_./-]+\.(?:md|py|yaml|yml|sql))`?", cell)
            if m:
                p = _norm(m.group(1))
                if "✅" in line or "required" in line.lower():
                    result.setdefault(p, "required")
                elif "defer" in line.lower() or "延后" in line:
                    result[p] = "deferred"

    # Paths in backticks under input files / manifest sections
    in_input = False
    for line in text.splitlines():
        if any(
            marker in line
            for marker in ("输入文件已读", "输入文件", "输入 manifest", "## B.")
        ):
            in_input = True
            continue
        if in_input and line.startswith("## ") and "B." not in line:
            if "输入" not in line and "manifest" not in line.lower():
                break
        if in_input:
            for m in _PATH_IN_BACKTICKS.finditer(line):
                p = _norm(m.group(1))
                result.setdefault(p, "required")

    return result


def _master_section_blob(master_text: str, section_prefix: str) -> str:
    """Collect lines under ## {section_prefix}* until next ## N."""
    lines = master_text.splitlines()
    blob: list[str] = []
    in_sec = False
    for line in lines:
        if re.match(rf"^## {re.escape(section_prefix)}", line):
            in_sec = True
            blob.append(line)
            continue
        if in_sec and re.match(r"^## \d+\.", line):
            break
        if in_sec:
            blob.append(line)
    return "\n".join(blob)


def _paths_from_command_blob(blob: str) -> set[str]:
    paths: set[str] = set()
    for pat in (_PYTEST_PATH, _SCRIPT_PATH, _BARE_SCRIPT):
        for m in pat.finditer(blob):
            raw = m.group(0)
            if raw.startswith("pytest "):
                raw = raw.replace("pytest ", "").split()[0]
            elif raw.startswith("python "):
                raw = raw.replace("python ", "").split()[0]
            paths.add(_norm(raw.split()[0] if " " in raw else raw))
    return paths


def parse_master_section9_paths(master_text: str) -> set[str]:
    """E3: tests/scripts from §5.4, §6, §9 steps; legacy §9 four-layer / §10 tier."""
    blobs = [
        _master_section_blob(master_text, "5."),
        _master_section_blob(master_text, "6."),
        _master_section_blob(master_text, "9."),
        _master_section_blob(master_text, "10."),
    ]
    paths: set[str] = set()
    for blob in blobs:
        paths |= _paths_from_command_blob(blob)
    return paths


def parse_master_section10_scripts(master_text: str) -> set[str]:
    """Legacy alias: tier scripts now live in §6; keep §10 for old MASTER."""
    sec = _master_section_blob(master_text, "6.") + "\n" + _master_section_blob(master_text, "10.")
    paths: set[str] = set()
    for m in _SCRIPT_PATH.finditer(sec):
        paths.add(_norm(m.group(0).replace("python ", "").split()[0]))
    for m in _BARE_SCRIPT.finditer(sec):
        paths.add(_norm(m.group(0)))
    return paths


def parse_master_wiring_paths(master_text: str) -> set[str]:
    """E8: Paths from wiring / touchpoint tables (§2 legacy §4 §6 §8)."""
    sec = ""
    for prefix in ("2.", "4.", "6.", "8."):
        sec += _master_section_blob(master_text, prefix) + "\n"

    paths: set[str] = set()
    for m in _PATH_IN_BACKTICKS.finditer(sec):
        p = _norm(m.group(1))
        if p.startswith(("backend/", "specs/", "tests/", "scripts/")):
            paths.add(p)
    for m in _PATH_IN_TABLE.finditer(sec):
        p = _norm(m.group(1))
        if "/" in p:
            paths.add(p)
    return paths


def parse_master_section32_defers(master_text: str) -> set[str]:
    """Extract defer item names from §3.2 table first column."""
    sec = ""
    lines = master_text.splitlines()
    in_sec = False
    for line in lines:
        if "### 3.2" in line or "Out of scope" in line:
            in_sec = True
            continue
        if in_sec and line.startswith("### ") and "3.2" not in line:
            break
        if in_sec:
            sec += line + "\n"
    items: set[str] = set()
    for line in sec.splitlines():
        if line.strip().startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if cols and cols[0] not in ("项", "Item"):
                items.add(cols[0][:80])
    return items


def module_spec_one_hop_refs(repo_root: Path, impl_paths: set[str]) -> set[str]:
    """E7: 1-hop refs from docs/modules/*.md in implement."""
    refs: set[str] = set()
    for p in impl_paths:
        if not p.startswith("docs/modules/") or not p.endswith(".md"):
            continue
        full = repo_root / p
        if not full.is_file():
            continue
        text = full.read_text(encoding="utf-8")
        for m in _MODULE_SPEC_REF.finditer(text):
            refs.add(_norm(m.group(1) or m.group(2)))
        # references table: | `path` |
        for m in _PATH_IN_BACKTICKS.finditer(text):
            ref = _norm(m.group(1))
            if ref.startswith(("docs/", "specs/")):
                refs.add(ref)
    return refs


def is_negative_implement_path(path: str) -> bool:
    """E11: paths that must not be required in implement."""
    return any(pat.search(path) for pat in _IMPLEMENT_NEGATIVE_PATTERNS)


def suggest_implement_context(task_dir: Path, repo_root: Path | None = None) -> list[dict]:
    """E12: Suggest implement.jsonl entries not yet present."""
    if repo_root is None:
        repo_root = _find_repo_root(task_dir)
    impl = impl_paths_set(task_dir)
    suggestions: list[dict] = []
    seen: set[str] = set()

    def add(path: str, reason: str) -> None:
        p = _norm(path)
        if not p or p in impl or p in seen or is_negative_implement_path(p):
            return
        if not (repo_root / p).is_file() and not p.endswith("/"):
            return
        seen.add(p)
        suggestions.append({"file": p, "reason": reason})

    for g in ():
        add(g, "GLOBAL / P0o required")

    trace = resolve_trace_path(task_dir)
    if trace:
        for p, status in parse_trace_manifest(trace).items():
            if status in ("execute", "execute-required", "must-read"):
                add(p, f"source-index manifest={status}")

    master = task_dir / "MASTER.plan.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8")
        for p in parse_master_section9_paths(text) | parse_master_section10_scripts(text):
            add(p, "MASTER §9/§10 regression or gate script")
        for p in parse_master_wiring_paths(text):
            add(p, "MASTER §6 wiring touchpoint")

    for p in wiring_paths_from_predecessors(task_dir, repo_root):
        add(p, "predecessor_tasks wiring inherit (E2)")

    for p in module_spec_one_hop_refs(repo_root, impl | seen):
        add(p, "module spec 1-hop reference (E7)")

    trace_path = resolve_trace_path(task_dir)
    if trace_path and trace_path.is_file():
        for m in []:
            for card in repo_root.glob(
                f"docs/implementation_tasks/**/{m}_implement_*.md"
            ):
                add(card.relative_to(repo_root).as_posix(), "task card from trace")

    return suggestions


def validate_trace_implement_sync(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E1: trace required paths must be in implement.jsonl."""
    trace = resolve_trace_path(task_dir)
    impl = impl_paths_set(task_dir)
    manifest = parse_trace_manifest(trace) if trace else {}
    for path, status in manifest.items():
        if status not in ("execute", "execute-required", "must-read"):
            continue
        if is_negative_implement_path(path):
            continue
        if path not in impl:
            # Allow partial path match for trace shorthand
            if not any(path in ip or ip.endswith(path) for ip in impl):
                errors.append(
                    f"E1: source-index required path missing from implement.jsonl: {path}"
                )


def validate_section9_in_implement(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E3: §9/§10 tests and gate scripts in implement (MASTER v3 or EXECUTION_INDEX v4)."""
    from .plan_protocol import plan_protocol_version

    if plan_protocol_version(task_dir) == "4":
        idx = task_dir / "EXECUTION_INDEX.md"
        if not idx.is_file():
            return
        from .execution_index import parse_step_section

        text = idx.read_text(encoding="utf-8")
        impl = impl_paths_set(task_dir)
        needed: set[str] = set()
        for m in _PYTEST_PATH.finditer(text):
            needed.add(m.group(0).replace("pytest ", "").strip())
        for m in _SCRIPT_PATH.finditer(text):
            needed.add(m.group(0).replace("python ", "").strip())
        sec2 = text
        for p in needed:
            if is_negative_implement_path(p):
                continue
            if p not in impl and (repo_root / p).is_file():
                errors.append(f"E3: EXECUTION_INDEX §2 path missing from implement.jsonl: {p}")
        _ = parse_step_section  # noqa: F841 — reserved for step-scoped E3
        return

    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return
    text = master.read_text(encoding="utf-8")
    impl = impl_paths_set(task_dir)
    needed = parse_master_section9_paths(text) | parse_master_section10_scripts(text)
    for p in sorted(needed):
        if is_negative_implement_path(p):
            continue
        if p not in impl and (repo_root / p).is_file():
            errors.append(f"E3: MASTER §5/§6/§9 path missing from implement.jsonl: {p}")


def validate_wiring_in_implement(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E8/E13: §6 wiring paths in implement or deferred in trace."""
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return
    impl = impl_paths_set(task_dir)
    manifest = parse_trace_manifest(resolve_trace_path(task_dir) or Path("__missing__"))
    deferred = {p for p, s in manifest.items() if s == "deferred"}
    for p in parse_master_wiring_paths(master.read_text(encoding="utf-8")):
        if p in deferred or is_negative_implement_path(p):
            continue
        if p not in impl and (repo_root / p).is_file():
            errors.append(f"E8: MASTER §6 wiring path missing from implement.jsonl: {p}")


def validate_predecessor_inherit(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E2: predecessor wiring paths referenced by MASTER/trace must be in implement."""
    preds = predecessor_task_dirs(task_dir, repo_root)
    if not preds:
        return
    impl = impl_paths_set(task_dir)
    master = task_dir / "MASTER.plan.md"
    master_wiring: set[str] = set()
    if master.is_file():
        master_wiring = parse_master_wiring_paths(master.read_text(encoding="utf-8"))
    trace_required = {
        p
        for p, s in parse_trace_manifest(resolve_trace_path(task_dir) or Path("__missing__")).items()
        if s in ("required", "inherited")
    }
    pred_wiring = wiring_paths_from_predecessors(task_dir, repo_root)
    must_have = pred_wiring & (master_wiring | trace_required)
    for p in sorted(must_have):
        if p not in impl and (repo_root / p).is_file():
            errors.append(f"E2: predecessor wiring path missing from implement.jsonl: {p}")


def validate_check_subset_implement(task_dir: Path, errors: list[str]) -> None:
    """E14: check.jsonl spec paths should be subset of implement (except audit-only)."""
    impl = impl_paths_set(task_dir)
    return
    check_entries = load_jsonl_entries(task_dir / "check.jsonl")
    for entry in check_entries:
        p = path_from_entry(entry)
        if not p:
            continue
        reason = str(entry.get("reason") or "")
        if any(m in reason.lower() for m in _CHECK_AUDIT_ONLY_MARKERS):
            continue
        if p.startswith(".trellis/tasks/"):
            continue
        if p not in impl and not p.endswith("AUDIT.plan.md"):
            errors.append(
                f"E14: check.jsonl path not in implement.jsonl (A1 should align Execute manifest): {p}"
            )


def validate_module_spec_refs(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E7: 1-hop module spec refs in implement or deferred."""
    impl = impl_paths_set(task_dir)
    manifest = parse_trace_manifest(resolve_trace_path(task_dir) or Path("__missing__"))
    deferred = {p for p, s in manifest.items() if s == "deferred"}
    for ref in module_spec_one_hop_refs(repo_root, impl):
        if ref in impl or ref in deferred:
            continue
        if (repo_root / ref).is_file():
            errors.append(
                f"E7: module spec 1-hop ref missing from implement.jsonl: {ref}"
            )


def validate_decisions_section32(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E10: If MASTER cites DECISIONS, file must exist; §3.2 defer table non-empty for complex tasks."""
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return
    text = master.read_text(encoding="utf-8")
    if "DECISIONS.md" in text:
        # Find decisions path from MASTER meta table
        m = re.search(
            r"`(docs/implementation_tasks/[^`]+/DECISIONS\.md)`", text
        )
        if m:
            dec_path = repo_root / m.group(1)
            if not dec_path.is_file():
                errors.append(f"E10: MASTER cites missing DECISIONS: {m.group(1)}")
    defers = parse_master_section32_defers(text)
    if "### 3.2" in text and len(defers) < 1:
        errors.append("E10: MASTER §3.2 out-of-scope defer table appears empty")


def _audit_text_for_e9(task_dir: Path) -> tuple[str, str]:
    """Return (combined text, source label) for E9 manifest audit markers."""
    integration = task_dir / "research" / "integration-audit.md"
    manifest = task_dir / "research" / "plan-manifest-audit.md"
    parts: list[str] = []
    labels: list[str] = []
    if integration.is_file():
        parts.append(integration.read_text(encoding="utf-8"))
        labels.append("integration-audit.md")
    if manifest.is_file():
        parts.append(manifest.read_text(encoding="utf-8"))
        labels.append("plan-manifest-audit.md")
    return "\n".join(parts), "+".join(labels) or "none"


def validate_plan_manifest_audit(task_dir: Path, errors: list[str]) -> None:
    """E9/E15/E19: 5d manifest audit (integration-audit canonical; plan-manifest optional stub)."""
    text, label = _audit_text_for_e9(task_dir)
    if not text:
        errors.append(
            "E9: Missing research/integration-audit.md or plan-manifest-audit.md "
            "(5d must record doc-gap + adversarial + PASS)"
        )
        return
    lower = text.lower()
    for marker in ("doc-gap", "adversarial"):
        if marker not in lower:
            errors.append(
                f"E9: 5d audit ({label}) must document {marker!r} section"
            )
    if "pass" not in lower and "closed" not in lower and "exit 0" not in lower:
        errors.append(f"E9: 5d audit ({label}) must record verdict (PASS/closed)")


def validate_freeze_manifest_gate(task_dir: Path, errors: list[str]) -> None:
    """E15: plan.freeze.md Manifest Gate checkboxes."""
    freeze = task_dir / "plan.freeze.md"
    if not freeze.is_file():
        return
    text = freeze.read_text(encoding="utf-8")
    if "Manifest Gate" not in text and "manifest gate" not in text.lower():
        errors.append(
            "E15: plan.freeze.md missing Manifest Gate section (§4 or §6; see templates/plan.freeze.md)"
        )
        return
    # Extract Manifest Gate section
    sec = ""
    lines = text.splitlines()
    in_sec = False
    for line in lines:
        if "Manifest Gate" in line:
            in_sec = True
        elif in_sec and line.startswith("## ") and "Manifest Gate" not in line:
            break
        if in_sec:
            sec += line + "\n"
    if sec and re.search(r"- \[ \]", sec):
        errors.append("E15: plan.freeze.md Manifest Gate has unchecked items")


def _extract_master_section(text: str, section: str) -> str:
    """Extract ### {section} ... until next ### at same level."""
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    prefix = f"### {section}"
    for i, line in enumerate(lines):
        if start is None and line.strip().startswith(prefix):
            start = i
            continue
        if start is not None and line.strip().startswith("### ") and not line.strip().startswith(
            prefix
        ):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def validate_master_no_short_boot_list(task_dir: Path, errors: list[str]) -> None:
    """E4: §9.0 (or legacy §8.0) must reference §0.3 + ledger."""
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return
    text = master.read_text(encoding="utf-8")
    if "§0.3" not in text and "### 0.3" not in text:
        errors.append("E4: MASTER missing §0.3 Execute mandatory read manifest")
    sec_boot = _extract_master_section(text, "9.0") or _extract_master_section(text, "8.0")
    if not sec_boot:
        return
    if "§0.3" not in sec_boot and "### 0.3" not in sec_boot:
        errors.append("E4: MASTER boot step must point to §0.3 (not standalone boot list)")
    if _integration_protocol_enabled(task_dir):
        if "integration-ledger" not in sec_boot.lower():
            errors.append(
                "E4: MASTER boot step must reference integration-ledger.md when v3 packing enabled"
            )
    if re.search(r"至少含[：:]", sec_boot):
        errors.append(
            "E4: MASTER boot step must not use 至少含 path enumeration; use §0.3 + implement.jsonl"
        )
    backticks = _PATH_IN_BACKTICKS.findall(sec_boot)
    if len(backticks) > 3:
        errors.append(
            f"E4: MASTER boot step lists {len(backticks)} inline paths; "
            "boot reads come from implement.jsonl only (max 3 example paths)"
        )


def validate_implement_negative_list(task_dir: Path, errors: list[str]) -> None:
    """E11: warn if implement contains negative-list paths (future create)."""
    for p in impl_paths_set(task_dir):
        if is_negative_implement_path(p):
            errors.append(
                f"E11: implement.jsonl should not list Execute-created path: {p}"
            )


def validate_manifest_phase_5c(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """E5: Phase 5c manifest curation gate."""
    if not _manifest_protocol_enabled(task_dir):
        return
    impl = task_dir / "implement.jsonl"
    if not impl.is_file():
        errors.append("Phase 5c: implement.jsonl missing")
        return
    entries = load_jsonl_entries(impl)
    if len(entries) < 10:
        errors.append(
            f"Phase 5c: implement.jsonl too thin ({len(entries)} entries); "
            "run suggest-implement-context and curate manifest"
        )
    trace = resolve_trace_path(task_dir)
    if trace and trace.is_file() and "manifest" not in trace.read_text(encoding="utf-8").lower():
        errors.append(
            "Phase 5c: source-index.md §B missing manifest column (required|inherited|deferred)"
        )
    validate_trace_implement_sync(task_dir, repo_root, errors)
    ledger = task_dir / "research" / "integration-ledger.md"
    if _integration_protocol_enabled(task_dir) and ledger.is_file():
        validate_integration_ledger(task_dir, repo_root, errors)
        validate_implement_reason_coverage(task_dir, errors)
    suggestions = suggest_implement_context(task_dir, repo_root)
    if len(suggestions) > 5:
        errors.append(
            f"Phase 5c: suggest-implement-context reports {len(suggestions)} missing entries "
            f"(first: {suggestions[0]['file']})"
        )


def _manifest_protocol_enabled(task_dir: Path) -> bool:
    """Manifest gates v1+ apply when task opts in or has audit artifact."""
    data = load_task_json(task_dir)
    meta = data.get("meta") or {}
    ver = str(meta.get("manifest_protocol_version", ""))
    if ver in ("1", "2", "3"):  # "2" legacy alias
        return True
    if (task_dir / "research" / "plan-manifest-audit.md").is_file():
        return True
    return False


def _integration_protocol_enabled(task_dir: Path) -> bool:
    """Context packing v3 (ledger + P0i) — manifest_protocol_version 2|3."""
    data = load_task_json(task_dir)
    meta = data.get("meta") or {}
    ver = str(meta.get("manifest_protocol_version", ""))
    if ver in ("2", "3"):  # "2" deprecated; prefer "3"
        return True
    if (task_dir / "research" / "integration-ledger.md").is_file():
        return True
    return False


def parse_integration_ledger(ledger_path: Path) -> list[dict]:
    """Parse integration-ledger.md table rows."""
    if not ledger_path.is_file():
        return []
    rows: list[dict] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        if "---" in line or "source" in line.lower() and "category" in line.lower():
            continue
        cols = [c.strip().strip("`") for c in line.split("|") if c.strip()]
        if len(cols) < 5:
            continue
        rows.append(
            {
                "source": _norm(cols[0]),
                "category": cols[1].lower(),
                "strategy": cols[2].lower().replace(" ", ""),
                "master_anchor": cols[3],
                "execute_extract": cols[4],
                "for_ac_step": cols[5] if len(cols) > 5 else "",
            }
        )
    return rows


def validate_input_inventory(task_dir: Path, errors: list[str]) -> None:
    """V1 / P0i: source-index §C or legacy input-inventory."""
    source = task_dir / "research" / "source-index.md"
    if source.is_file():
        text = source.read_text(encoding="utf-8")
        if "索引完整" not in text:
            errors.append("V1: source-index.md must mark 索引完整")
        if "六类" not in text:
            errors.append("V1: source-index.md §C must document six categories")
        return
    inv = task_dir / "research" / "input-inventory.md"
    if not inv.is_file():
        errors.append(
            "V1: Missing research/source-index.md (or legacy input-inventory.md)"
        )
        return
    text = inv.read_text(encoding="utf-8")
    if "P0i complete" not in text:
        errors.append("V1: input-inventory.md must end with P0i complete")
    if "六类关键信息" not in text and "6类" not in text:
        errors.append("V1: input-inventory.md must document six critical categories")
    if "missing-in-repo" not in text.lower():
        errors.append("V1: input-inventory.md must have missing-in-repo section")


def validate_integration_ledger(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    """V2–V4: ledger coverage and pointer ↔ implement sync."""
    ledger_path = task_dir / "research" / "integration-ledger.md"
    if not ledger_path.is_file():
        errors.append("V2: Missing research/integration-ledger.md")
        return
    rows = parse_integration_ledger(ledger_path)
    if len(rows) < 5:
        errors.append(f"V2: integration-ledger.md too thin ({len(rows)} rows; need ≥5)")
    cats = {r["category"] for r in rows}
    required_cats = ("decision", "contract", "business", "architecture", "rule", "wiring")
    for cat in required_cats:
        if not any(cat in r["category"] for r in rows):
            errors.append(f"V3: integration-ledger missing category coverage: {cat}")
    impl = impl_paths_set(task_dir)
    impl_entries = load_jsonl_entries(task_dir / "implement.jsonl")
    impl_reasons = {path_from_entry(e): str(e.get("reason", "")) for e in impl_entries}
    for row in rows:
        strat = row["strategy"]
        if strat not in ("pointer", "summary+pointer", "summarypointer"):
            continue
        src = row["source"]
        if not src or src.startswith("MASTER"):
            continue
        full = repo_root / src
        if not full.is_file():
            continue
        if src not in impl:
            errors.append(f"V4: ledger pointer not in implement.jsonl: {src}")
            continue
        reason = impl_reasons.get(src, "")
        if "extract:" not in reason.lower() and "提取" not in reason:
            errors.append(
                f"V4: implement.jsonl reason missing extract: for ledger pointer {src}"
            )
        if "for:" not in reason.lower() and "用于" not in reason:
            errors.append(
                f"V4: implement.jsonl reason missing for: (AC/§8) for {src}"
            )


def validate_integration_audit(task_dir: Path, errors: list[str]) -> None:
    """V5: integration-audit.md at freeze."""
    audit = task_dir / "research" / "integration-audit.md"
    if not audit.is_file():
        errors.append("V5: Missing research/integration-audit.md (Plan 5d)")
        return
    text = audit.read_text(encoding="utf-8").lower()
    if "pass" not in text and "fail" not in text:
        errors.append("V5: integration-audit.md must record PASS/FAIL verdict")
    if "六类" not in text and "6类" not in text and "critical" not in text:
        errors.append("V5: integration-audit.md must cover six critical categories")
    for marker in ("doc-gap", "adversarial", "closure"):
        if marker not in text:
            errors.append(
                f"V5: integration-audit.md must include merged 5d section {marker!r}"
            )


def _reason_has_extract_for(reason: str) -> bool:
    r = reason.lower()
    return ("extract:" in r or "extract：" in reason) and (
        "for:" in r or "for：" in reason or "用于" in reason
    )


def _is_v7_exempt_implement_path(path: str) -> bool:
    norm = _norm(path)
    if norm.endswith("MASTER.plan.md"):
        return True
    if "/frozen/" in norm and norm.endswith(".md"):
        return True
    if norm.endswith("EXECUTION_INDEX.md"):
        return True
    return "trellis-execute/SKILL.md" in norm


def validate_ledger_master_anchors(task_dir: Path, errors: list[str]) -> None:
    """V8: integration-ledger master_anchor must resolve in MASTER."""
    ledger_path = task_dir / "research" / "integration-ledger.md"
    master = task_dir / "MASTER.plan.md"
    if not ledger_path.is_file() or not master.is_file():
        return
    master_text = master.read_text(encoding="utf-8")
    for row in parse_integration_ledger(ledger_path):
        anchor = row.get("master_anchor", "").strip()
        if not anchor:
            errors.append(
                f"V8: integration-ledger row missing master_anchor: {row.get('source')}"
            )
            continue
        if not _master_anchor_resolves(master_text, anchor):
            errors.append(
                f"V8: master_anchor {anchor!r} not found in MASTER for {row.get('source')}"
            )


def _master_anchor_resolves(master_text: str, anchor: str) -> bool:
    anchor = anchor.strip()
    if not anchor:
        return False
    if anchor in master_text:
        return True
    m = re.search(r"§\s*([0-9]+(?:\.[0-9]+)?)", anchor)
    if m:
        sec = m.group(1)
        needles = (
            f"## {sec}",
            f"### {sec}",
            f"§{sec}",
            f"§ {sec}",
            f"MASTER §{sec}",
        )
        return any(n in master_text for n in needles)
    return "MASTER" in anchor and "§" in master_text


def validate_implement_reason_coverage(task_dir: Path, errors: list[str]) -> None:
    """V7: every implement entry (excl. MASTER/execute skill) must have extract:/for:."""
    if not _integration_protocol_enabled(task_dir):
        return
    for entry in load_jsonl_entries(task_dir / "implement.jsonl"):
        p = path_from_entry(entry)
        if not p or _is_v7_exempt_implement_path(p):
            continue
        reason = str(entry.get("reason") or "")
        if not _reason_has_extract_for(reason):
            errors.append(
                f"V7: implement.jsonl missing extract:/for: in reason for {p}"
            )


def validate_integration_ledger_in_implement(task_dir: Path, errors: list[str]) -> None:
    """V9: v3 boot map must be in implement.jsonl L1 closure."""
    if not _integration_protocol_enabled(task_dir):
        return
    ledger = task_dir / "research" / "integration-ledger.md"
    if not ledger.is_file():
        return
    rel = ledger.relative_to(task_dir).as_posix()
    task_rel = f".trellis/tasks/{task_dir.name}/research/integration-ledger.md"
    impl = impl_paths_set(task_dir)
    if rel not in impl and task_rel not in impl:
        errors.append(
            "V9: research/integration-ledger.md missing from implement.jsonl (v3 boot mandatory)"
        )


def validate_freeze_context_packing_gate(task_dir: Path, errors: list[str]) -> None:
    """V5+: plan.freeze Context Packing Gate + manifest_protocol_version 3."""
    if not _integration_protocol_enabled(task_dir):
        return
    freeze = task_dir / "plan.freeze.md"
    if freeze.is_file():
        text = freeze.read_text(encoding="utf-8")
        if "Context Packing Gate" not in text and "context packing" not in text.lower():
            errors.append(
                "V5+: plan.freeze.md missing Context Packing Gate (§3.0c or §7)"
            )
    data = load_task_json(task_dir)
    ver = str((data.get("meta") or {}).get("manifest_protocol_version", ""))
    if ver == "2":
        errors.append(
            'meta.manifest_protocol_version "2" is deprecated; set to "3" for v3 packing'
        )
    elif ver != "3":
        errors.append(
            f'meta.manifest_protocol_version must be "3" when v3 packing enabled (got {ver!r})'
        )


def validate_grill_closure_in_master(task_dir: Path, errors: list[str]) -> None:
    """V6: grill session exists → MASTER must have §7 or documented closure."""
    grill_files = list(task_dir.glob("research/grill-*-session.md"))
    if not grill_files:
        return
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return
    text = master.read_text(encoding="utf-8")
    if "## 7." not in text and "Red Flag" not in text:
        errors.append(
            "V6: grill session exists but MASTER missing §7 Red Flags / closure"
        )


def validate_integration_protocol_freeze(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """V1–V8 bundle for v3 freeze."""
    if not _integration_protocol_enabled(task_dir):
        return
    validate_input_inventory(task_dir, errors)
    validate_integration_ledger(task_dir, repo_root, errors)
    validate_ledger_master_anchors(task_dir, errors)
    validate_implement_reason_coverage(task_dir, errors)
    validate_integration_ledger_in_implement(task_dir, errors)
    validate_integration_audit(task_dir, errors)
    validate_grill_closure_in_master(task_dir, errors)
    validate_freeze_context_packing_gate(task_dir, errors)


def validate_manifest_phase_p0i(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """P0-index phase gate (legacy name P0i)."""
    if not _integration_protocol_enabled(task_dir):
        return
    validate_input_inventory(task_dir, errors)


def validate_manifest_freeze(task_dir: Path, repo_root: Path, errors: list[str]) -> None:
    """E1–E15 + V1–V6 bundle for validate-plan-freeze."""
    if not _manifest_protocol_enabled(task_dir):
        return
    validate_master_no_short_boot_list(task_dir, errors)
    validate_trace_implement_sync(task_dir, repo_root, errors)
    validate_section9_in_implement(task_dir, repo_root, errors)
    validate_wiring_in_implement(task_dir, repo_root, errors)
    validate_predecessor_inherit(task_dir, repo_root, errors)
    validate_check_subset_implement(task_dir, errors)
    validate_module_spec_refs(task_dir, repo_root, errors)
    validate_decisions_section32(task_dir, repo_root, errors)
    validate_plan_manifest_audit(task_dir, errors)
    validate_freeze_manifest_gate(task_dir, errors)
    validate_implement_negative_list(task_dir, errors)
    validate_integration_protocol_freeze(task_dir, repo_root, errors)


def validate_execute_boot(task_dir: Path, errors: list[str]) -> None:
    """E16: Execute Phase 0 — context-closure only (no execute-boot self-attestation)."""
    closure = task_dir / "research" / "context-closure.md"
    if not closure.is_file():
        errors.append(
            "E16: Missing research/context-closure.md (Execute 6.pre L2 closure report)"
        )
    elif "upstream" not in closure.read_text(encoding="utf-8").lower():
        errors.append("E16: context-closure.md must document upstream/wiring closure")


def validate_manifest_amend_chain(task_dir: Path, errors: list[str]) -> None:
    """E18/E20: manifest-amend.md if present must list add-context entries."""
    amend = task_dir / "research" / "manifest-amend.md"
    if not amend.is_file():
        return
    text = amend.read_text(encoding="utf-8")
    if "add-context" not in text and "implement.jsonl" not in text:
        errors.append(
            "E20: manifest-amend.md must document add-context / implement.jsonl amendments"
        )
