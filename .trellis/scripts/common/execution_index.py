"""EXECUTION_INDEX.md parsing and manifest generation (Plan protocol v4)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .plan_protocol import (
    execution_entry_rel,
    execution_index_path,
    execution_index_rel,
    execute_ssot_rel,
    frozen_task_card_path,
    is_execution_bundle_v41,
    is_execution_bundle_v42,
    is_plan_protocol_v4,
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
    if not is_plan_protocol_v4(task_dir):
        return ["plan_protocol_version is not v4; use legacy manifests"]

    index_path = execution_index_path(task_dir)
    if not index_path.is_file():
        return ["missing EXECUTION_INDEX.md"]
    index_rel = execution_index_rel(task_dir, repo_root)
    if not index_rel:
        return ["cannot resolve EXECUTION_INDEX repo-relative path"]

    index_text = index_path.read_text(encoding="utf-8")
    rows = parse_manifest_rows(index_text)

    if is_execution_bundle_v42(task_dir):
        entry_rel = execution_entry_rel(task_dir, repo_root)
        if not entry_rel:
            return ["missing EXECUTION_PLAN.md (v4.2 execute_entry)"]
        implement: list[str] = [
            _jsonl_line(entry_rel, "extract: Execute plan SSOT | for: Boot slot 1"),
            _jsonl_line(index_rel, "extract: manifest index | for: Boot slot 2"),
        ]
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
            _jsonl_line(entry_rel, "extract: Execute plan trace | for: A5 scope"),
            _jsonl_line(index_rel, "extract: manifest index | for: A1/A5/A8"),
        ]
        check: list[str] = [
            _jsonl_line(index_rel, "extract: manifest trace | for: A1"),
        ]
    else:
        frozen = frozen_task_card_path(task_dir)
        if not frozen:
            return ["missing frozen/*.md task card"]
        frozen_rel = execute_ssot_rel(task_dir, repo_root)
        if not frozen_rel:
            return ["cannot resolve frozen card repo-relative path"]

        if is_execution_bundle_v41(task_dir):
            entry_rel = execution_entry_rel(task_dir, repo_root)
            if not entry_rel:
                return ["missing research/00-EXECUTION-ENTRY.md (v4.1 execute_entry)"]
            slot2_rel = entry_rel
            slot2_reason = "extract: Execute bundle entry | for: Boot slot 2"
        else:
            slot2_rel = index_rel
            slot2_reason = "extract: Execute/Audit manifest index | for: Boot slot 2"

        implement = [
            _jsonl_line(frozen_rel, "extract: Execute SSOT frozen task card | for: Boot slot 1"),
            _jsonl_line(slot2_rel, slot2_reason),
        ]
        pack = task_dir / "context_pack.json"
        if pack.is_file() and index_rel:
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

        audit = [
            _jsonl_line(
                f".trellis/tasks/{task_dir.name}/AUDIT.plan.md",
                "extract: Audit SSOT | for: A1-A8 boot",
            ),
            _jsonl_line(frozen_rel, "extract: frozen task card trace | for: A5 scope"),
            _jsonl_line(index_rel, "extract: manifest index | for: A1/A5/A8"),
        ]

        check = [
            _jsonl_line(frozen_rel, "extract: spec scope | for: A1 trellis-check"),
            _jsonl_line(index_rel, "extract: manifest trace | for: A1"),
        ]

    seen_impl: set[str] = set()
    seen_audit: set[str] = set()
    seen_check: set[str] = set()

    _pytest_ac = re.compile(r"(?:pytest\s+)?tests/[a-zA-Z0-9_./-]+\.py")

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

    for m in _pytest_ac.finditer(index_text):
        test_path = m.group(0).replace("pytest ", "").strip()
        if (repo_root / test_path).is_file():
            add_unique(
                implement,
                seen_impl,
                test_path,
                "extract: AC test | for: EXECUTION_INDEX §2",
            )

    (task_dir / "implement.jsonl").write_text("\n".join(implement) + "\n", encoding="utf-8")
    (task_dir / "audit.jsonl").write_text("\n".join(audit) + "\n", encoding="utf-8")
    (task_dir / "check.jsonl").write_text("\n".join(check) + "\n", encoding="utf-8")
    return errors


def _extract_md_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _build_v42_thin_frozen_body(
    *,
    source_rel: str,
    plan_rel: str,
    stamp: str,
    title: str,
) -> str:
    """v4.2: audit snapshot + pointers; specs live in EXECUTION_PLAN.md."""
    return (
        f"<!-- FROZEN: Plan protocol v4.2 · thin pointer · source: {source_rel} · "
        f"frozen_at: {stamp} -->\n\n"
        f"# FROZEN — {title}\n\n"
        f"> **Execute SSOT：** `{plan_rel}`  \n"
        f"> **执行索引：** `EXECUTION_INDEX.md` §3 manifest  \n"
        f"> **活卡（冻结时点）：** `{source_rel}`  \n"
        f"> **禁止：** 在此复制 `EXECUTION_PLAN.md` 正文\n\n"
        "## 8. 边界 / 停止条件\n\n"
        f"见 `{plan_rel}` 与活卡「不在范围」；偏离铁律即停。\n\n"
        "## 9. 实现步骤\n\n"
        "切片 AC 与步骤：见 `EXECUTION_PLAN.md`；RED/GREEN 与证据：`EXECUTION_INDEX.md` §1。\n\n"
        "### 9.0 Boot\n\n"
        f"先 Read `{plan_rel}` 全文 + `implement.jsonl` 每一行 + `EXECUTION_INDEX.md` §1 当前 Step。\n"
    )


def _build_v41_thin_frozen_body(
    *,
    source_rel: str,
    entry_rel: str,
    stamp: str,
    title: str,
) -> str:
    """v4.1: audit snapshot + pointers only; specs live in ENTRY + research/."""
    return (
        f"<!-- FROZEN: Plan protocol v4.1 · thin pointer · source: {source_rel} · "
        f"frozen_at: {stamp} -->\n\n"
        f"# FROZEN — {title}\n\n"
        f"> **Execute SSOT：** `{entry_rel}`  \n"
        f"> **活卡（冻结时点）：** `{source_rel}`  \n"
        f"> **禁止：** 在此复制 `to-issues-slices.md` 或 `research/` 包正文\n\n"
        "## 8. 边界 / 停止条件\n\n"
        f"见 `{entry_rel}` §2 与活卡「不在范围」；偏离铁律即停。\n\n"
        "## 9. 实现步骤\n\n"
        "切片 AC 与步骤：`research/to-issues-slices.md`；RED/GREEN 与证据：`EXECUTION_INDEX.md` §1。\n\n"
        "### 9.0 Boot\n\n"
        f"先 Read `{entry_rel}` §5.2 + `EXTERNAL-INDEX.md` §A，再按 `to-issues-slices.md` 当前切片 § 执行。\n"
    )


def freeze_task_card(
    task_dir: Path,
    repo_root: Path,
    *,
    source_rel: str | None = None,
) -> list[str]:
    """Copy repo task card into frozen/ (v4.0) or write thin pointer (v4.1/v4.2)."""
    errors: list[str] = []
    meta = load_task_json(task_dir).get("meta") or {}
    v42 = is_execution_bundle_v42(task_dir)
    v41 = is_execution_bundle_v41(task_dir)
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
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if v42:
        plan_rel = str(meta.get("execute_entry", "")).strip() or "EXECUTION_PLAN.md"
        plan_path = task_dir / plan_rel.replace("\\", "/")
        if not plan_path.is_file():
            return [f"missing {plan_rel} (v4.2 requires plan before freeze-task-card)"]
        title = _extract_md_title(source.read_text(encoding="utf-8"), dest_name.removesuffix(".md"))
        body = _build_v42_thin_frozen_body(
            source_rel=src.replace("\\", "/"),
            plan_rel=plan_rel,
            stamp=stamp,
            title=title,
        )
    elif v41:
        entry_rel = str(meta.get("execute_entry", "")).strip() or "research/00-EXECUTION-ENTRY.md"
        entry_path = task_dir / entry_rel
        if not entry_path.is_file():
            return [f"missing {entry_rel} (v4.1 requires ENTRY before freeze-task-card)"]
        title = _extract_md_title(source.read_text(encoding="utf-8"), dest_name.removesuffix(".md"))
        body = _build_v41_thin_frozen_body(
            source_rel=src.replace("\\", "/"),
            entry_rel=entry_rel,
            stamp=stamp,
            title=title,
        )
    else:
        body = source.read_text(encoding="utf-8")
        header = (
            f"<!-- FROZEN: Plan protocol v4 · do not edit · source: {src} · "
            f"frozen_at: {stamp} -->\n\n"
        )
        if "FROZEN:" not in body[:200]:
            body = header + body
    dest.write_text(body, encoding="utf-8")

    data = load_task_json(task_dir)
    data.setdefault("meta", {})["frozen_task_card"] = f"frozen/{dest_name}"
    data["meta"]["frozen_at"] = stamp
    data["meta"]["source_task_card"] = src.replace("\\", "/")
    if v42:
        data["meta"]["plan_protocol_version"] = "4.2"
        data["meta"].setdefault("execute_entry", "EXECUTION_PLAN.md")
    elif v41:
        data["meta"]["plan_protocol_version"] = "4.1"
        data["meta"].setdefault("execute_entry", "research/00-EXECUTION-ENTRY.md")
    elif plan_protocol_version(task_dir) not in ("4.1", "4.2"):
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
    from .plan_protocol import is_execution_bundle_v41, is_execution_bundle_v42, load_task_json

    if is_execution_bundle_v42(task_dir):
        return

    card = frozen_task_card_path(task_dir)
    if not card:
        errors.append("missing frozen/*.md (v4 frozen task card)")
        return
    text = card.read_text(encoding="utf-8")
    if is_execution_bundle_v41(task_dir):
        entry = str((load_task_json(task_dir).get("meta") or {}).get("execute_entry", "")).strip()
        entry = entry or "research/00-EXECUTION-ENTRY.md"
        if entry not in text and "00-EXECUTION-ENTRY" not in text:
            errors.append(f"v4.1 frozen card must point to Execute entry ({entry})")
        if "thin pointer" not in text.lower() and "薄指针" not in text:
            errors.append("v4.1 frozen card must be thin pointer (re-run freeze-task-card)")
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
