"""Shared helpers for loop engineering task-flow tooling."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_GRAPH_PATH = REPO_ROOT / "specs/context/authority_graph.yaml"
TEST_CATALOG_PATH = REPO_ROOT / "tests/test_catalog.yaml"
FEATURE_MATRIX_PATH = REPO_ROOT / "specs/verification/feature_verification_matrix.yaml"
CONTRACT_COVERAGE_PATH = REPO_ROOT / "specs/verification/contract_coverage.yaml"
GLOBAL_RULES = [
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md",
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md",
]

REQUIRED_CATALOG_FIELDS = (
    "purpose",
    "type",
    "verifies",
    "command",
    "failure_meaning",
)


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def path_exists(rel: str) -> bool:
    norm = rel.replace("\\", "/")
    candidate = REPO_ROOT / norm
    return candidate.is_file() or candidate.is_dir()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def load_authority_graph() -> dict[str, Any]:
    return load_yaml(AUTHORITY_GRAPH_PATH)


def load_test_catalog() -> dict[str, Any]:
    return load_yaml(TEST_CATALOG_PATH)


def load_feature_matrix() -> dict[str, Any]:
    return load_yaml(FEATURE_MATRIX_PATH)


def load_contract_coverage() -> dict[str, Any]:
    return load_yaml(CONTRACT_COVERAGE_PATH)


def discover_test_modules() -> list[str]:
    out: list[str] = []
    for path in sorted(REPO_ROOT.glob("tests/**/test_*.py")):
        out.append(repo_relative(path))
    return out


def validate_context_pack(pack: dict) -> list[str]:
    errors: list[str] = []
    for item in pack.get("source_authorities") or []:
        path = str(item.get("path", ""))
        if path and not path_exists(path):
            errors.append(f"context_pack source authority missing: {path}")
    for item in pack.get("tests") or []:
        path = str(item.get("path", ""))
        if path and not path_exists(path):
            errors.append(f"context_pack test path missing: {path}")
    return errors


def module_docstring(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return ""
    doc = ast.get_docstring(tree) or ""
    return doc.strip().splitlines()[0] if doc.strip() else ""


def infer_test_type(rel: str, purpose: str) -> str:
    lowered = f"{rel} {purpose}".lower()
    if "gate" in lowered or "policy" in lowered or "staged" in lowered:
        return "policy-contract"
    if "contract" in lowered or "schema" in lowered:
        return "contract"
    if "smoke" in lowered:
        return "smoke"
    if "audit" in lowered or "registry" in lowered or "manifest" in lowered:
        return "protocol"
    if "e2e" in lowered or "integration" in lowered or "flow" in lowered:
        return "integration"
    return "runtime-contract"


def default_catalog_entry(rel: str) -> dict[str, Any]:
    path = REPO_ROOT / rel
    purpose = module_docstring(path) or f"Regression coverage for {Path(rel).stem}"
    return {
        "purpose": purpose,
        "type": infer_test_type(rel, purpose),
        "verifies": {"docs": [], "specs": [], "rules": []},
        "command": f"uv run python -m pytest {rel} -q",
        "failure_meaning": f"Regression in {Path(rel).stem}; inspect purpose and linked authorities.",
    }


def infer_task_touched_paths(task_dir: Path) -> list[str]:
    """Repo-relative paths referenced in MASTER.plan.md and implement.jsonl."""
    paths: list[str] = []
    master = task_dir / "MASTER.plan.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8")
        for token in ("backend/", "tests/", "scripts/", "docs/", "specs/"):
            start = 0
            while True:
                idx = text.find(token, start)
                if idx < 0:
                    break
                end = idx
                while end < len(text) and text[end] not in (" ", "`", ")", "\n", "|", '"', "'"):
                    end += 1
                candidate = text[idx:end].rstrip(".,;:")
                if candidate.count("/") >= 1:
                    paths.append(candidate)
                start = end
    impl = task_dir / "implement.jsonl"
    if impl.is_file():
        for line in impl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in ("path", "file"):
                val = row.get(key)
                if val:
                    paths.append(str(val).replace("\\", "/"))
    return sorted(set(paths))


def deprecated_loop_meta_errors(task_dir: Path) -> list[str]:
    task_json = task_dir / "task.json"
    if not task_json.is_file():
        return []
    meta = load_json(task_json).get("meta") or {}
    errors: list[str] = []
    if "loop_engineering_exempt" in meta:
        errors.append("deprecated meta.loop_engineering_exempt — use meta.task_track (simple|debt-lite)")
    if "loop_engineering_version" in meta:
        errors.append("deprecated meta.loop_engineering_version — use meta.task_track: complex")
    return errors


def authority_graph_coverage_gaps(task_dir: Path) -> list[str]:
    """Implementation paths in task with no matching authority_graph module."""
    graph = load_authority_graph()
    if not graph.get("modules"):
        return []
    gaps: list[str] = []
    for rel in infer_task_touched_paths(task_dir):
        if not rel.startswith(("backend/", "scripts/")):
            continue
        if not modules_for_paths([rel], graph):
            gaps.append(rel)
    return sorted(set(gaps))


def task_track(task_dir: Path) -> str:
    """Trellis task track: complex (MASTER+loop) | debt-lite | simple."""
    task_json = task_dir / "task.json"
    meta = load_json(task_json).get("meta") or {} if task_json.is_file() else {}
    track = str(meta.get("task_track", "")).lower()
    if track in ("complex", "debt-lite", "simple"):
        return track
    if (task_dir / "MASTER.plan.md").is_file():
        return "complex"
    return "simple"


def loop_required(task_dir: Path) -> bool:
    return task_track(task_dir) == "complex"


def loop_engineering_enabled(task_dir: Path) -> bool:
    return loop_required(task_dir)


def discover_unmapped_backend_packages() -> list[str]:
    """Top-level backend/app packages with no authority_graph implementation glob."""
    graph = load_authority_graph()
    patterns: list[str] = []
    for cfg in (graph.get("modules") or {}).values():
        patterns.extend(str(p) for p in (cfg.get("implementation") or []))
    app_dir = REPO_ROOT / "backend" / "app"
    if not app_dir.is_dir():
        return []
    unmapped: list[str] = []
    for child in sorted(app_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        probe = f"backend/app/{child.name}/__init__.py"
        if not any(glob_match(pat, probe) for pat in patterns):
            unmapped.append(child.name)
    return unmapped


def extract_master_ac_ids(task_dir: Path) -> list[str]:
    import re

    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return []
    text = master.read_text(encoding="utf-8")
    section = text.split("## 2.", 1)[1].split("## 3.", 1)[0] if "## 2." in text else text
    header = re.compile(r"^###\s+AC[-\s]?([A-Z0-9._-]+)", re.I | re.M)
    table = re.compile(r"\|\s*AC[-\s]?([A-Z0-9._-]+)\s*\|", re.I)
    return sorted(set(header.findall(section)) | set(table.findall(section)))


def write_loop_evidence_stubs(task_dir: Path, pack: dict[str, Any]) -> tuple[Path, Path]:
    """ponytail: minimal loop_manifest + evidence_index stubs; enrich during Execute."""
    manifest_path = task_dir / "loop_manifest.json"
    evidence_path = task_dir / "evidence_index.json"
    if not manifest_path.is_file():
        acs = [{"id": ac_id, "status": "pending", "repair_items": []} for ac_id in extract_master_ac_ids(task_dir)]
        manifest_path.write_text(
            json.dumps(
                {"task": task_dir.name, "modules": pack.get("modules") or [], "acs": acs},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    if not evidence_path.is_file():
        evidence_path.write_text(
            json.dumps({"execute": {}, "audit": {}}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return manifest_path, evidence_path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    while current.name and not (current / ".trellis").is_dir():
        if current.parent == current:
            break
        current = current.parent
    return current


def glob_match(pattern: str, rel: str) -> bool:
    from fnmatch import fnmatch

    norm = rel.replace("\\", "/")
    pat = pattern.replace("\\", "/")
    if pat.endswith("/**"):
        prefix = pat[:-3]
        return norm == prefix.rstrip("/") or norm.startswith(prefix)
    return fnmatch(norm, pat)


def modules_for_paths(paths: list[str], graph: dict[str, Any]) -> list[str]:
    modules = graph.get("modules") or {}
    matched: list[str] = []
    for name, cfg in modules.items():
        impl_patterns = cfg.get("implementation") or []
        test_patterns = cfg.get("tests") or []
        for rel in paths:
            norm = rel.replace("\\", "/")
            if any(glob_match(p, norm) for p in impl_patterns + test_patterns):
                if name not in matched:
                    matched.append(name)
    return matched


def collect_module_authorities(module_name: str, graph: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    cfg = (graph.get("modules") or {}).get(module_name) or {}
    out: list[dict[str, str]] = []
    for path in cfg.get("docs") or []:
        out.append({"type": "design", "path": path, "reason": f"{module_name} design authority"})
    for path in cfg.get("contracts") or []:
        out.append({"type": "contract", "path": path, "reason": f"{module_name} contract"})
    for path in cfg.get("rules") or []:
        out.append({"type": "policy", "path": path, "reason": f"{module_name} rule"})
    for path in cfg.get("implementation_tasks") or []:
        out.append({"type": "task-card", "path": path, "reason": f"{module_name} implementation task"})
    tests = []
    for path in cfg.get("tests") or []:
        tests.append({"path": path, "purpose": f"{module_name} regression"})
    return {
        "source_authorities": out,
        "tests": tests,
        "forbidden_claims": list(cfg.get("forbidden_claims") or []),
        "required_evidence": list(cfg.get("required_evidence") or []),
    }
