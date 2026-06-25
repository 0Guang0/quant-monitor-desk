"""EXECUTION_INDEX.md parsing and manifest generation (Plan protocol v4)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .plan_protocol import (
    execution_index_path,
    execution_index_rel,
    execute_ssot_rel,
    frozen_task_card_path,
    load_task_json,
    plan_protocol_version,
)

_MANIFEST_STATUSES = frozenset(
    {
        "must-read",
        "execute-required",
        "execute",
        "required",
        "audit-only",
        "deferred",
        "inherited",
        "summary-ok",
    }
)
_EXECUTE_AUDIENCES = frozenset({"execute", "both", "exec", "执行"})
_AUDIT_AUDIENCES = frozenset({"audit", "both", "审计"})


def _section(text: str, header: str) -> str:
    """Block under ## {header} until next ##."""
    lines = text.splitlines()
    start: int | None = None
    prefix = f"## {header}"
    for i, line in enumerate(lines):
        if start is None and line.strip().startswith(prefix):
            start = i + 1
            continue
        if start is not None and line.strip().startswith("## "):
            return "\n".join(lines[start:i])
    if start is not None:
        return "\n".join(lines[start:])
    return ""


def parse_manifest_rows(index_text: str) -> list[dict[str, str]]:
    """Parse §3 必须读原文 table rows."""
    sec = _section(index_text, "3. 必须读原文")
    if not sec:
        sec = _section(index_text, "3.")
    rows: list[dict[str, str]] = []
    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "---" in line or "path" in line.lower() and "manifest" in line.lower():
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        path = cells[0].strip("`").strip()
        if not path or path.lower() == "path":
            continue
        row = {
            "path": path.replace("\\", "/"),
            "manifest": cells[1] if len(cells) > 1 else "must-read",
            "audience": cells[2] if len(cells) > 2 else "both",
            "extract": cells[3] if len(cells) > 3 else "",
            "for": cells[4] if len(cells) > 4 else "",
        }
        rows.append(row)
    return rows


def parse_step_section(index_text: str) -> str:
    for header in ("1. 步骤与证据", "1."):
        sec = _section(index_text, header)
        if sec and ("RED" in sec or "步骤" in sec):
            return sec
    return ""


def _audience_matches(audience: str, targets: frozenset[str]) -> bool:
    a = audience.lower().strip()
    return a in targets or any(t in a for t in targets)


def _manifest_for_execute(status: str) -> bool:
    s = status.lower().strip()
    return s in ("must-read", "execute-required", "execute", "required")


def _manifest_for_audit(status: str) -> bool:
    s = status.lower().strip()
    return s in ("must-read", "audit-only", "required", "execute-required")


def _jsonl_line(path: str, reason: str) -> str:
    return json.dumps({"file": path, "reason": reason}, ensure_ascii=False)


def generate_manifests(task_dir: Path, repo_root: Path) -> list[str]:
    """Write implement.jsonl, audit.jsonl, check.jsonl from EXECUTION_INDEX §3. Returns errors."""
    errors: list[str] = []
    if plan_protocol_version(task_dir) != "4":
        return ["plan_protocol_version is not 4; use legacy manifests"]

    index_path = execution_index_path(task_dir)
    if not index_path.is_file():
        return ["missing EXECUTION_INDEX.md"]
    frozen = frozen_task_card_path(task_dir)
    if not frozen:
        return ["missing frozen/*.md task card"]

    frozen_rel = execute_ssot_rel(task_dir, repo_root)
    index_rel = execution_index_rel(task_dir, repo_root)
    if not frozen_rel or not index_rel:
        return ["cannot resolve frozen card or index repo-relative path"]

    index_text = index_path.read_text(encoding="utf-8")
    rows = parse_manifest_rows(index_text)

    implement: list[str] = [
        _jsonl_line(frozen_rel, "extract: Execute SSOT frozen task card | for: Boot slot 1"),
        _jsonl_line(index_rel, "extract: Execute/Audit manifest index | for: Boot slot 2"),
    ]
    pack_rel = execution_index_rel(task_dir, repo_root)
    pack = task_dir / "context_pack.json"
    if pack.is_file() and pack_rel:
        implement.append(
            _jsonl_line(
                f".trellis/tasks/{task_dir.name}/context_pack.json",
                "extract: authority graph routing | for: Boot slot 3",
            )
        )
    implement.append(
        _jsonl_line(
            ".cursor/skills/trellis-execute/SKILL.md",
            "extract: Phase 0 boot | for: §9.0 Boot",
        )
    )

    audit: list[str] = [
        _jsonl_line(
            f".trellis/tasks/{task_dir.name}/AUDIT.plan.md",
            "extract: Audit SSOT | for: A1-A8 boot",
        ),
        _jsonl_line(frozen_rel, "extract: frozen task card trace | for: A5 scope"),
        _jsonl_line(index_rel, "extract: manifest index | for: A1/A5/A8"),
    ]

    check: list[str] = [
        _jsonl_line(frozen_rel, "extract: spec scope | for: A1 trellis-check"),
        _jsonl_line(index_rel, "extract: manifest trace | for: A1"),
    ]

    seen_impl: set[str] = set()
    seen_audit: set[str] = set()
    seen_check: set[str] = set()

    def add_unique(bucket: list[str], seen: set[str], path: str, reason: str) -> None:
        norm = path.replace("\\", "/")
        if norm in seen:
            return
        seen.add(norm)
        bucket.append(_jsonl_line(norm, reason))

    for row in rows:
        path = row["path"]
        manifest = row.get("manifest", "must-read")
        audience = row.get("audience", "both")
        extract = row.get("extract") or "context"
        for_target = row.get("for") or "manifest"
        reason = f"extract: {extract} | for: {for_target}"
        if _audience_matches(audience, _EXECUTE_AUDIENCES) and _manifest_for_execute(
            manifest
        ):
            add_unique(implement, seen_impl, path, reason)
        if _audience_matches(audience, _AUDIT_AUDIENCES) and _manifest_for_audit(
            manifest
        ):
            add_unique(audit, seen_audit, path, reason)
        if manifest.lower() == "audit-only":
            add_unique(check, seen_check, path, f"extract: {extract} | for: A1 audit-only")
        elif _manifest_for_execute(manifest) and "specs/contracts" in path:
            add_unique(check, seen_check, path, reason)

    (task_dir / "implement.jsonl").write_text("\n".join(implement) + "\n", encoding="utf-8")
    (task_dir / "audit.jsonl").write_text("\n".join(audit) + "\n", encoding="utf-8")
    (task_dir / "check.jsonl").write_text("\n".join(check) + "\n", encoding="utf-8")
    return errors


def freeze_task_card(
    task_dir: Path,
    repo_root: Path,
    *,
    source_rel: str | None = None,
) -> list[str]:
    """Copy repo task card into frozen/ with freeze header. Returns errors."""
    errors: list[str] = []
    meta = load_task_json(task_dir).get("meta") or {}
    src = (source_rel or meta.get("source_task_card") or "").strip()
    if not src:
        index_path = execution_index_path(task_dir)
        if index_path.is_file():
            m = re.search(
                r"\|\s*source_card\s*\|\s*`?([^`|]+)`?\s*\|",
                index_path.read_text(encoding="utf-8"),
                re.I,
            )
            if m:
                src = m.group(1).strip()
    if not src:
        return ["source_task_card not set in task.json meta or EXECUTION_INDEX §0"]
    source = repo_root / src.replace("\\", "/")
    if not source.is_file():
        return [f"source task card not found: {src}"]

    frozen_dir = task_dir / "frozen"
    frozen_dir.mkdir(parents=True, exist_ok=True)
    dest_name = source.name
    dest = frozen_dir / dest_name
    body = source.read_text(encoding="utf-8")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (
        f"<!-- FROZEN: Plan protocol v4 · do not edit · source: {src} · frozen_at: {stamp} -->\n\n"
    )
    if "FROZEN:" not in body[:200]:
        body = header + body
    dest.write_text(body, encoding="utf-8")

    data = load_task_json(task_dir)
    data.setdefault("meta", {})["frozen_task_card"] = f"frozen/{dest_name}"
    data["meta"]["frozen_at"] = stamp
    data["meta"]["source_task_card"] = src.replace("\\", "/")
    data["meta"]["plan_protocol_version"] = "4"
    (task_dir / "task.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return errors


def validate_execution_index_structure(task_dir: Path, errors: list[str]) -> None:
    index_path = execution_index_path(task_dir)
    if not index_path.is_file():
        errors.append("missing EXECUTION_INDEX.md (v4 Execute/Audit index)")
        return
    text = index_path.read_text(encoding="utf-8")
    if re.search(r"\{\{[^}]+\}\}", text):
        errors.append("EXECUTION_INDEX.md has unresolved {{placeholders}}")
    for header in ("0. 冻结元数据", "1. 步骤与证据", "3. 必须读原文"):
        if header not in text and not re.search(
            rf"##\s*{re.escape(header.split('.')[0])}\.", text
        ):
            errors.append(f"EXECUTION_INDEX.md missing section: {header}")
    steps = parse_step_section(text)
    if steps and not (
        "RED" in steps and ("GREEN" in steps or "绿" in steps)
    ):
        errors.append("EXECUTION_INDEX.md §1 missing RED/GREEN columns")


def validate_frozen_task_card(task_dir: Path, errors: list[str]) -> None:
    card = frozen_task_card_path(task_dir)
    if not card:
        errors.append("missing frozen/*.md (v4 frozen task card)")
        return
    text = card.read_text(encoding="utf-8")
    if "## 9." not in text and "实现步骤" not in text:
        errors.append("frozen task card missing §9 实现步骤")
    if "停止条件" not in text and "## 8." not in text:
        errors.append("frozen task card missing §8 边界/停止条件")


def validate_manifests_match_index(
    task_dir: Path, repo_root: Path, errors: list[str]
) -> None:
    """After generate_manifests, ensure §3 execute rows appear in implement.jsonl."""
    index_path = execution_index_path(task_dir)
    impl_path = task_dir / "implement.jsonl"
    if not index_path.is_file() or not impl_path.is_file():
        return
    rows = parse_manifest_rows(index_path.read_text(encoding="utf-8"))
    impl_text = impl_path.read_text(encoding="utf-8")
    for row in rows:
        if not _audience_matches(row.get("audience", ""), _EXECUTE_AUDIENCES):
            continue
        if not _manifest_for_execute(row.get("manifest", "")):
            continue
        path = row["path"]
        if path not in impl_text and path.replace("/", "\\") not in impl_text:
            errors.append(
                f"v4 manifest drift: EXECUTION_INDEX §3 path missing from implement.jsonl: {path}"
            )


def cmd_freeze_task_card(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1
    source = getattr(args, "source", None)
    errors = freeze_task_card(task_dir, repo_root, source_rel=source)
    if errors:
        for err in errors:
            print(colored(f"  - {err}", Colors.RED))
        return 1
    gen_errors = generate_manifests(task_dir, repo_root)
    if gen_errors:
        for err in gen_errors:
            print(colored(f"  - {err}", Colors.RED))
        return 1
    print(colored("freeze-task-card: frozen/*.md + manifests updated", Colors.GREEN))
    return 0


def cmd_generate_manifests(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1
    errors = generate_manifests(task_dir, repo_root)
    if errors:
        for err in errors:
            print(colored(f"  - {err}", Colors.RED))
        return 1
    print(colored("generate-manifests: implement/audit/check.jsonl written", Colors.GREEN))
    return 0
