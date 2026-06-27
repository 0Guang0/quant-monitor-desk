"""R3G-02 pre-production adversarial audit — fail-closed go/no-go over R3G-01 evidence."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.provider_catalog import load_provider_catalog, provider_for_source
from backend.app.datasources.source_registry import SourceNotFoundError, SourceRegistry
from backend.app.ops.sandbox_clean_write.audit_decision import (
    AuditDecision,
    AuditFinding,
    AuditResult,
)
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    RehearsalPlanError,
    load_candidate_set,
    validate_source_caps,
)
from backend.app.ops.sandbox_clean_write.rehearsal_report import required_report_fields
from backend.app.ops.sandbox_clean_write.rehearsal_runner import _resolve_path as _resolve

_CATALOG: dict[str, Any] | None = None
_REGISTRY: SourceRegistry | None = None

GUARDRAIL_SCAN_ROOTS = (PROJECT_ROOT / "backend" / "app", PROJECT_ROOT / "scripts")
FORBIDDEN_REFERENCE_IMPORT_ROOTS = frozenset(
    {"openbb", "EasyXT", "JQ2PTrade", "TradingAgents", "agents_for_openbb"}
)
FORBIDDEN_TRADING_DEF_NAMES = frozenset(
    {"order", "buy", "sell", "order_value", "order_target", "order_target_value", "cancel_order"}
)
STRATEGY_METRIC_KEYS = frozenset(
    {"sharpe_ratio", "max_drawdown", "total_return", "backtest_pnl", "trade_count"}
)
DH_PROFILE_EVIDENCE_FILES = (
    "validation_report_summary.json",
    "data_health_profile_report.json",
)
CN_EQUITY_DOMAIN = "cn_equity_daily_bar"
BAR_DOMAINS = frozenset({CN_EQUITY_DOMAIN})
METADATA_DOMAINS = frozenset({"cn_announcements"})
REQUIRED_BAR_FIELDS = frozenset({"open", "high", "low", "close", "volume"})
GUARDRAILS_PATH = PROJECT_ROOT / "specs/contracts/reference_adoption_guardrails.yaml"
PROVIDER_CATALOG_PATH = PROJECT_ROOT / "specs/datasource_registry/provider_catalog.yaml"
SOURCE_REGISTRY_PATH = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES_PATH = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
SANDBOX_CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
AUDIT_SCAN_SKIP = frozenset({"adversarial_audit.py"})
R3F_PROFILE_EVIDENCE = "data_health_profile_report.json"
_REF_PROJECT_DIR = "\u53c2\u8003\u9879\u76ee"
_SYS_PATH_INSERT = "sys.path." + "insert"
_SYS_PATH_APPEND = "sys.path." + "append"


@dataclass(frozen=True)
class AdversarialAuditRequest:
    rehearsal_report: Path
    sandbox_db: Path
    evidence_dir: Path


def _rel_evidence_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_guardrail_patterns(category: str) -> tuple[str, ...]:
    if not GUARDRAILS_PATH.is_file():
        return ()
    raw = yaml.safe_load(GUARDRAILS_PATH.read_text(encoding="utf-8")) or {}
    block = (raw.get("forbidden_adoption") or {}).get(category) or {}
    return tuple(str(x) for x in (block.get("examples") or ()))


def _forbidden_trading_def_names() -> frozenset[str]:
    return FORBIDDEN_TRADING_DEF_NAMES | frozenset(
        _load_guardrail_patterns("real_trading_or_order_api")
    )


def _trading_substring_patterns() -> tuple[str, ...]:
    return tuple(
        p
        for p in _load_guardrail_patterns("real_trading_or_order_api")
        if p not in FORBIDDEN_TRADING_DEF_NAMES
    )


def _loaded_catalog() -> dict[str, Any]:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = load_provider_catalog()
    return _CATALOG


def _loaded_registry() -> SourceRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = SourceRegistry()
        _REGISTRY.load()
    return _REGISTRY


def _collect_imports(py_path: Path) -> set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _scan_file_patterns(py_path: Path, patterns: tuple[str, ...]) -> list[str]:
    lowered = py_path.read_text(encoding="utf-8").lower()
    return [p for p in patterns if re.search(rf"\b{re.escape(p.lower())}\b", lowered)]


def _scan_runtime_guardrails() -> list[AuditFinding]:
    """Static guardrail scan — ponytail: O(files) rglob over backend/scripts; shared module extract deferred."""
    findings: list[AuditFinding] = []
    scheduler_patterns = _load_guardrail_patterns("scheduler_or_execution_hook")
    openbb_patterns = _load_guardrail_patterns("copied_openbb_runtime_source")
    agent_patterns = _load_guardrail_patterns("round3g_agent_triggered_write")
    trading_names = _forbidden_trading_def_names()
    trading_patterns = _trading_substring_patterns()

    for root in GUARDRAIL_SCAN_ROOTS:
        if not root.is_dir():
            continue
        for py_file in root.rglob("*.py"):
            if "tests" in py_file.parts or py_file.name in AUDIT_SCAN_SKIP:
                continue
            rel = _rel_evidence_path(py_file)
            text = py_file.read_text(encoding="utf-8")
            for imp in _collect_imports(py_file):
                top = imp.split(".", 1)[0]
                if top in FORBIDDEN_REFERENCE_IMPORT_ROOTS:
                    findings.append(
                        AuditFinding(
                            code="runtime_import_from_reference_project",
                            message=f"forbidden import root {top} in {rel}",
                            evidence_paths=(rel,),
                        )
                    )
                if top == "openbb" or imp.startswith("openbb."):
                    findings.append(
                        AuditFinding(
                            code="copied_openbb_runtime_source",
                            message=f"openbb runtime import in {rel}",
                            evidence_paths=(rel,),
                        )
                    )
            if _REF_PROJECT_DIR in text and (
                _SYS_PATH_INSERT in text or _SYS_PATH_APPEND in text
            ):
                findings.append(
                    AuditFinding(
                        code="runtime_import_from_reference_project",
                        message=f"sys.path mutation with reference project dir in {rel}",
                        evidence_paths=(rel,),
                    )
                )
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in trading_names:
                        findings.append(
                            AuditFinding(
                                code="jq2ptrade_disallowed_api_surface",
                                message=f"forbidden trading API def {node.name}() in {rel}",
                                evidence_paths=(rel,),
                            )
                        )
            trading_hits = _scan_file_patterns(py_file, trading_patterns)
            if trading_hits:
                findings.append(
                    AuditFinding(
                        code="jq2ptrade_disallowed_api_surface",
                        message=f"forbidden trading API pattern(s) in {rel}: {trading_hits}",
                        evidence_paths=(rel,),
                    )
                )
            sched_hits = _scan_file_patterns(py_file, scheduler_patterns)
            if sched_hits:
                findings.append(
                    AuditFinding(
                        code="jq2ptrade_disallowed_api_surface",
                        message=f"scheduler/exec hook pattern(s) in {rel}: {sched_hits}",
                        evidence_paths=(rel,),
                    )
                )
            openbb_hits = _scan_file_patterns(py_file, openbb_patterns)
            if openbb_hits:
                findings.append(
                    AuditFinding(
                        code="copied_openbb_runtime_source",
                        message=f"copied OpenBB pattern(s) in {rel}: {openbb_hits}",
                        evidence_paths=(rel,),
                    )
                )
            agent_hits = _scan_file_patterns(py_file, agent_patterns)
            if agent_hits:
                findings.append(
                    AuditFinding(
                        code="agent_triggered_write_path",
                        message=f"agent-triggered write pattern(s) in {rel}: {agent_hits}",
                        evidence_paths=(rel,),
                    )
                )
    return findings


def _provider_entry_for(source_id: str) -> dict[str, Any] | None:
    if not PROVIDER_CATALOG_PATH.is_file():
        return None
    return provider_for_source(source_id, _loaded_catalog())


def _source_registry_entry(source_id: str) -> dict[str, Any] | None:
    if not SOURCE_REGISTRY_PATH.is_file():
        return None
    try:
        rec = _loaded_registry().get(source_id)
    except SourceNotFoundError:
        return None
    return {"source_id": rec.source_id}


def _contract_candidate_caps() -> dict[str, Any]:
    if not SANDBOX_CONTRACT_PATH.is_file():
        return {}
    raw = yaml.safe_load(SANDBOX_CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    return raw.get("candidate_caps") or {}


def _source_capabilities_domain(source_id: str, domain: str) -> dict[str, Any] | None:
    if not SOURCE_CAPABILITIES_PATH.is_file():
        return None
    raw = yaml.safe_load(SOURCE_CAPABILITIES_PATH.read_text(encoding="utf-8")) or {}
    source_block = raw.get(source_id) or {}
    domains = source_block.get("domains") or {}
    entry = domains.get(domain)
    return entry if isinstance(entry, dict) else None


def _is_bar_source(src: dict[str, Any]) -> bool:
    return str(src.get("domain") or "") in BAR_DOMAINS


def _is_metadata_source(src: dict[str, Any]) -> bool:
    return str(src.get("domain") or "") in METADATA_DOMAINS


def _audit_lineage_coverage(
    src: dict[str, Any], *, report_path: Path
) -> tuple[list[AuditFinding], list[AuditFinding]]:
    """§3.3 bar-source lineage coverage — 0.0 BLOCK, <1.0 WARN."""
    if not _is_bar_source(src):
        return [], []
    source_id = str(src.get("source_id") or "")
    fetch_cov = float(src.get("source_fetch_id_coverage") or 0.0)
    content_cov = float(src.get("content_hash_coverage") or 0.0)
    evidence = (str(report_path),)
    if fetch_cov <= 0.0 or content_cov <= 0.0:
        return [
            AuditFinding(
                code="missing_rehearsal_report",
                message=(
                    f"zero lineage coverage for bar source {source_id}: "
                    f"fetch={fetch_cov}, content={content_cov}"
                ),
                evidence_paths=evidence,
            )
        ], []
    if fetch_cov < 1.0 or content_cov < 1.0:
        return [], [
            AuditFinding(
                code="incomplete_lineage_coverage",
                message=(
                    f"partial lineage coverage for {source_id}: "
                    f"fetch={fetch_cov}, content={content_cov}"
                ),
                evidence_paths=evidence,
            )
        ]
    return [], []


def _audit_synthetic_admission(
    src: dict[str, Any], *, report_path: Path
) -> tuple[list[AuditFinding], list[AuditFinding]]:
    """§3.3 synthetic admission — PASSED+synthetic BLOCK; synthetic alone WARN."""
    if not src.get("synthetic_admission"):
        return [], []
    source_id = str(src.get("source_id") or "")
    validation = str(src.get("validation_status") or "").upper()
    evidence = (str(report_path),)
    if validation == "PASSED":
        return [
            AuditFinding(
                code="write_manager_or_db_validation_gate_bypass",
                message=f"synthetic_admission with validation_status=PASSED for {source_id}",
                evidence_paths=evidence,
            )
        ], []
    return [], [
        AuditFinding(
            code="synthetic_admission_flagged",
            message=f"synthetic_admission requires manual review for {source_id}",
            evidence_paths=evidence,
        )
    ]


def _audit_row_counts(
    src: dict[str, Any], *, report_path: Path
) -> tuple[list[AuditFinding], list[AuditFinding]]:
    """§3.3 substantive row/coverage counts."""
    source_id = str(src.get("source_id") or "")
    evidence = (str(report_path),)
    blocking: list[AuditFinding] = []
    warnings: list[AuditFinding] = []
    if _is_metadata_source(src):
        staged = int(src.get("staged_row_count") or 0)
        if staged <= 0:
            blocking.append(
                AuditFinding(
                    code="missing_rehearsal_report",
                    message=f"metadata source {source_id} has staged_row_count={staged}",
                    evidence_paths=evidence,
                )
            )
    elif _is_bar_source(src):
        clean = int(src.get("sandbox_clean_row_count") or 0)
        if clean <= 0:
            warnings.append(
                AuditFinding(
                    code="zero_sandbox_clean_rows",
                    message=f"bar source {source_id} dry_run sandbox_clean_row_count={clean}",
                    evidence_paths=evidence,
                )
            )
    return blocking, warnings


def _audit_bar_evidence_substance(evidence_dir: Path, source_id: str) -> list[AuditFinding]:
    """§3.1 EasyXT checklist — read bars.json OHLCV substance when present on disk."""
    bars_path = evidence_dir / source_id / "bars.json"
    if not bars_path.is_file():
        return []
    try:
        payload = json.loads(bars_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"invalid bars.json for {source_id}",
                evidence_paths=(str(bars_path),),
            )
        ]
    rows = payload.get("rows") or []
    if not rows:
        return [
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"empty bar data in evidence for {source_id}",
                evidence_paths=(str(bars_path),),
            )
        ]
    first = rows[0]
    missing = REQUIRED_BAR_FIELDS - {str(k) for k in first.keys()}
    if missing:
        return [
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"bars.json missing OHLCV fields {sorted(missing)} for {source_id}",
                evidence_paths=(str(bars_path),),
            )
        ]
    try:
        high = float(first["high"])
        low = float(first["low"])
        if high < low:
            return [
                AuditFinding(
                    code="missing_data_health_profile_evidence",
                    message=f"OHLC relation violation in bars.json sample for {source_id}",
                    evidence_paths=(str(bars_path),),
                )
            ]
    except (KeyError, TypeError, ValueError):
        return [
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"non-numeric OHLC in bars.json for {source_id}",
                evidence_paths=(str(bars_path),),
            )
        ]
    return []


def _audit_dh_evidence_content(
    evidence_dir: Path, src: dict[str, Any]
) -> tuple[list[AuditFinding], list[AuditFinding]]:
    """§3.1 read validation_report_summary + DH profile path (P1-01, P2-04)."""
    domain = str(src.get("domain") or "")
    source_id = str(src.get("source_id") or "")
    if domain != CN_EQUITY_DOMAIN:
        return [], []
    blocking: list[AuditFinding] = []
    warnings: list[AuditFinding] = []
    dh_summary = src.get("data_health_summary") or {}
    has_structured = _has_structured_dh_profile(src)
    profile_path = evidence_dir / source_id / R3F_PROFILE_EVIDENCE
    has_r3f_profile = profile_path.is_file()
    if not str(dh_summary.get("gate_rationale") or "").strip() and not has_r3f_profile:
        blocking.append(
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=(
                    f"missing gate_rationale and no R3F profile evidence for {source_id}"
                ),
                evidence_paths=(str(evidence_dir / source_id),),
            )
        )
    val_path = evidence_dir / source_id / "validation_report_summary.json"
    if val_path.is_file():
        try:
            val_payload = json.loads(val_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blocking.append(
                AuditFinding(
                    code="missing_data_health_profile_evidence",
                    message=f"invalid validation_report_summary.json for {source_id}",
                    evidence_paths=(str(val_path),),
                )
            )
        else:
            if "allow_clean_write" not in val_payload:
                blocking.append(
                    AuditFinding(
                        code="missing_data_health_profile_evidence",
                        message=f"validation_report_summary missing allow_clean_write for {source_id}",
                        evidence_paths=(str(val_path),),
                    )
                )
            elif len(val_payload) <= 1:
                warnings.append(
                    AuditFinding(
                        code="thin_validation_summary",
                        message=f"validation_report_summary lacks issue summary for {source_id}",
                        evidence_paths=(str(val_path),),
                    )
                )
    elif not has_structured:
        blocking.append(
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"missing validation_report_summary.json for {source_id}",
                evidence_paths=(str(val_path),),
            )
        )
    elif has_structured and int(dh_summary.get("validation_fail_count") or 0) > 0:
        blocking.append(
            AuditFinding(
                code="missing_data_health_profile_evidence",
                message=f"structured DH profile reports validation_fail_count>0 for {source_id}",
                evidence_paths=(str(evidence_dir / source_id),),
            )
        )
    blocking.extend(_audit_bar_evidence_substance(evidence_dir, source_id))
    return blocking, warnings


def _fred_authorization_evidence(evidence_dir: Path, source_id: str) -> bool:
    sub = evidence_dir / source_id
    if not sub.is_dir():
        return False
    for path in sub.iterdir():
        name = path.name.lower()
        if "authorization" in name and path.suffix in {".yaml", ".yml", ".json"}:
            return True
    return (sub / "fred_evidence.json").is_file()


def _audit_provider_metadata(
    per_source: list[dict[str, Any]],
    *,
    evidence_dir: Path,
    candidate_set: str,
) -> tuple[list[AuditFinding], list[AuditFinding]]:
    """§3.4 provider architecture — catalog, registry, auth, caps."""
    blocking: list[AuditFinding] = []
    warnings: list[AuditFinding] = []
    caps = _contract_candidate_caps()
    for src in per_source:
        source_id = str(src.get("source_id") or "")
        domain = str(src.get("domain") or "")
        provider = _provider_entry_for(source_id)
        if provider is None:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=f"provider catalog missing metadata for {source_id}",
                    evidence_paths=(str(PROVIDER_CATALOG_PATH),),
                )
            )
            continue
        allowed = provider.get("allowed_domains") or []
        if domain and domain not in allowed:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=f"domain {domain!r} not in provider allowed_domains for {source_id}",
                    evidence_paths=(str(PROVIDER_CATALOG_PATH),),
                )
            )
        if provider.get("runtime_source_copy_allowed"):
            blocking.append(
                AuditFinding(
                    code="copied_openbb_runtime_source",
                    message=f"runtime_source_copy_allowed=true for {source_id}",
                    evidence_paths=(str(PROVIDER_CATALOG_PATH),),
                )
            )
        if provider.get("production_default_enabled") is True:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=f"production_default_enabled=true for {source_id}",
                    evidence_paths=(str(PROVIDER_CATALOG_PATH),),
                )
            )
        contract_source_caps = caps.get(source_id) or {}
        if "enabled_by_default" in contract_source_caps:
            expected_enabled = contract_source_caps["enabled_by_default"]
            if provider.get("enabled_by_default") != expected_enabled:
                warnings.append(
                    AuditFinding(
                        code="provider_enabled_by_default_mismatch",
                        message=(
                            f"catalog enabled_by_default={provider.get('enabled_by_default')!r} "
                            f"!= contract {expected_enabled!r} for {source_id}"
                        ),
                        evidence_paths=(str(PROVIDER_CATALOG_PATH), str(SANDBOX_CONTRACT_PATH)),
                    )
                )
        requires_auth = bool(provider.get("requires_user_authorization"))
        cap_domain = _source_capabilities_domain(source_id, domain)
        if cap_domain is not None:
            cap_requires_auth = bool(cap_domain.get("requires_auth"))
            if cap_requires_auth != requires_auth:
                warnings.append(
                    AuditFinding(
                        code="provider_auth_posture_mismatch",
                        message=(
                            f"capabilities requires_auth={cap_requires_auth} != "
                            f"catalog requires_user_authorization={requires_auth} for {source_id}"
                        ),
                        evidence_paths=(str(SOURCE_CAPABILITIES_PATH), str(PROVIDER_CATALOG_PATH)),
                    )
                )
        source_caps = caps.get(source_id) or {}
        if source_id == "fred":
            max_series = int(source_caps.get("r3g01_max_series") or 3)
        else:
            max_series = int(source_caps.get("r3g01_max_symbols") or 3)
        reported = int(src.get("symbol_or_series_count") or 0)
        if reported > max_series:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=f"{source_id} reported count {reported} exceeds contract cap {max_series}",
                    evidence_paths=(str(SANDBOX_CONTRACT_PATH),),
                )
            )
        if requires_auth and source_id == "fred":
            contract_requires = bool(contract_source_caps.get("requires_user_authorization"))
            if contract_requires != requires_auth:
                blocking.append(
                    AuditFinding(
                        code="uncapped_candidate_set",
                        message=(
                            f"fred auth posture mismatch: contract={contract_requires} "
                            f"catalog={requires_auth}"
                        ),
                        evidence_paths=(str(SANDBOX_CONTRACT_PATH), str(PROVIDER_CATALOG_PATH)),
                    )
                )
            if not _fred_authorization_evidence(evidence_dir, source_id):
                warnings.append(
                    AuditFinding(
                        code="fred_authorization_evidence_missing",
                        message=f"fred requires_user_authorization but no auth evidence for {source_id}",
                        evidence_paths=(str(evidence_dir / source_id),),
                    )
                )
        registry = _source_registry_entry(source_id)
        if registry is None:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=f"source_registry missing entry for {source_id}",
                    evidence_paths=(str(SOURCE_REGISTRY_PATH),),
                )
            )
        if candidate_set:
            candidate = _candidate_from_source_report(src, candidate_set=candidate_set)
            if candidate is not None and candidate.metadata_only != (domain in METADATA_DOMAINS):
                warnings.append(
                    AuditFinding(
                        code="provider_domain_posture_mismatch",
                        message=f"metadata_only posture mismatch for {source_id}",
                        evidence_paths=(str(SANDBOX_CONTRACT_PATH),),
                    )
                )
    return blocking, warnings


def _dh_profile_evidence(evidence_dir: Path, source_id: str) -> Path | None:
    sub = evidence_dir / source_id
    if not sub.is_dir():
        return None
    for name in DH_PROFILE_EVIDENCE_FILES:
        path = sub / name
        if path.is_file():
            return path
    return None


def _has_structured_dh_profile(src: dict[str, Any]) -> bool:
    dh_summary = src.get("data_health_summary") or {}
    required_keys = (
        "overall_status",
        "validation_pass_count",
        "validation_warn_count",
        "validation_fail_count",
        "sandbox_clean_write_gate_ready",
    )
    return all(key in dh_summary for key in required_keys)


def _calendar_approximate(dh_summary: dict[str, Any]) -> bool:
    rationale = str(dh_summary.get("gate_rationale") or "").lower()
    if "approximate" in rationale or "official calendar" in rationale:
        return True
    if int(dh_summary.get("calendar_gap_violation_count") or 0) > 0:
        return dh_summary.get("overall_status") in {"WARN", "WARNING"}
    return False


def _has_strategy_metrics(report: dict[str, Any]) -> bool:
    return bool(STRATEGY_METRIC_KEYS.intersection(report.keys()))


def _candidate_from_source_report(src: dict[str, Any], *, candidate_set: str) -> RehearsalCandidate | None:
    source_id = str(src.get("source_id") or "")
    domain = str(src.get("domain") or "")
    if not source_id or not domain:
        return None
    try:
        frozen = load_candidate_set(candidate_set)
    except RehearsalPlanError:
        return None
    match = next((c for c in frozen if c.source_id == source_id), None)
    if match is None:
        return None
    count = int(src.get("symbol_or_series_count") or len(match.symbols_or_series))
    symbols = match.symbols_or_series[:count] if count <= len(match.symbols_or_series) else match.symbols_or_series
    return RehearsalCandidate(
        source_id=source_id,
        domain=domain,
        operation=match.operation,
        symbols_or_series=symbols,
        window_days=match.window_days,
        metadata_only=match.metadata_only,
    )


def _finalize(
    blocking: list[AuditFinding],
    warnings: list[AuditFinding],
    evidence_paths: list[str],
) -> AuditResult:
    unique_paths = tuple(dict.fromkeys(evidence_paths))
    if blocking:
        return AuditResult(
            decision=AuditDecision.BLOCK_PRODUCTION_WRITE,
            blocking_reasons=tuple(blocking),
            warning_reasons=tuple(warnings),
            evidence_paths=unique_paths,
            production_mutation_allowed=False,
        )
    if warnings:
        return AuditResult(
            decision=AuditDecision.WARN_ALLOW_WITH_MANUAL_APPROVAL,
            blocking_reasons=(),
            warning_reasons=tuple(warnings),
            evidence_paths=unique_paths,
            production_mutation_allowed=False,
        )
    return AuditResult(
        decision=AuditDecision.PASS_ALLOW_LIMITED_PROD_WRITE,
        blocking_reasons=(),
        warning_reasons=(),
        evidence_paths=unique_paths,
        production_mutation_allowed=False,
    )


def run_adversarial_audit(request: AdversarialAuditRequest) -> AuditResult:
    """Run five-dimension adversarial audit over R3G-01 artifacts (audit-only)."""
    blocking: list[AuditFinding] = []
    warnings: list[AuditFinding] = []
    evidence_paths: list[str] = []

    report_path = _resolve(request.rehearsal_report)
    evidence_dir = _resolve(request.evidence_dir)
    sandbox_db = _resolve(request.sandbox_db)

    if not report_path.is_file():
        blocking.append(
            AuditFinding(
                code="missing_rehearsal_report",
                message=f"rehearsal report not found: {report_path}",
                evidence_paths=(str(report_path),),
            )
        )
        return _finalize(blocking, warnings, [str(report_path)])

    evidence_paths.append(str(report_path))
    if not evidence_dir.is_dir():
        blocking.append(
            AuditFinding(
                code="missing_rehearsal_report",
                message=f"evidence_dir not found or not a directory: {evidence_dir}",
                evidence_paths=(str(evidence_dir),),
            )
        )
        return _finalize(blocking, warnings, evidence_paths)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("production_mutation_allowed"):
        blocking.append(
            AuditFinding(
                code="write_manager_or_db_validation_gate_bypass",
                message="rehearsal report claims production_mutation_allowed=true",
                evidence_paths=(str(report_path),),
            )
        )

    per_source = report.get("per_source_reports") or []
    if not per_source:
        blocking.append(
            AuditFinding(
                code="missing_rehearsal_report",
                message="rehearsal report missing per_source_reports",
                evidence_paths=(str(report_path),),
            )
        )
        return _finalize(blocking, warnings, evidence_paths)

    required = required_report_fields()
    candidate_set = str(report.get("candidate_set") or "")
    if candidate_set:
        try:
            validate_set = load_candidate_set(candidate_set)
            for candidate in validate_set:
                validate_source_caps(candidate)
        except RehearsalPlanError as exc:
            blocking.append(
                AuditFinding(
                    code="uncapped_candidate_set",
                    message=str(exc),
                    evidence_paths=(str(report_path),),
                )
            )

    for src in per_source:
        missing_fields = [f for f in required if f not in src]
        if missing_fields:
            blocking.append(
                AuditFinding(
                    code="missing_rehearsal_report",
                    message=f"per-source report missing fields: {missing_fields}",
                    evidence_paths=(str(report_path),),
                )
            )
        if not src.get("write_manager_operation_id") or not src.get("rollback_artifact_path"):
            blocking.append(
                AuditFinding(
                    code="missing_rehearsal_report",
                    message="report omits write/rollback proof",
                    evidence_paths=(str(report_path),),
                )
            )
        rollback_raw = str(src.get("rollback_artifact_path") or "")
        if rollback_raw:
            rollback_path = Path(rollback_raw)
            if not rollback_path.is_absolute():
                rollback_path = PROJECT_ROOT / rollback_path
            if not rollback_path.is_file():
                blocking.append(
                    AuditFinding(
                        code="missing_rehearsal_report",
                        message=f"rollback artifact file missing: {rollback_path}",
                        evidence_paths=(rollback_raw,),
                    )
                )
            else:
                evidence_paths.append(str(rollback_path.resolve()))
        else:
            rollback_source_id = str(src.get("source_id") or "")
            rollback_path = _resolve(Path(str(src.get("rollback_artifact_path"))))
            if not rollback_path.is_file():
                blocking.append(
                    AuditFinding(
                        code="missing_rehearsal_report",
                        message=(
                            f"rollback artifact not found on disk for {rollback_source_id}: "
                            f"{rollback_path}"
                        ),
                        evidence_paths=(str(rollback_path),),
                    )
                )
        if _has_strategy_metrics(src):
            blocking.append(
                AuditFinding(
                    code="write_manager_or_db_validation_gate_bypass",
                    message="report contains strategy/backtest metrics",
                    evidence_paths=(str(report_path),),
                )
            )

        cov_block, cov_warn = _audit_lineage_coverage(src, report_path=report_path)
        blocking.extend(cov_block)
        warnings.extend(cov_warn)

        syn_block, syn_warn = _audit_synthetic_admission(src, report_path=report_path)
        blocking.extend(syn_block)
        warnings.extend(syn_warn)

        row_block, row_warn = _audit_row_counts(src, report_path=report_path)
        blocking.extend(row_block)
        warnings.extend(row_warn)

        dh_block, dh_warn = _audit_dh_evidence_content(evidence_dir, src)
        blocking.extend(dh_block)
        warnings.extend(dh_warn)

        domain = str(src.get("domain") or "")
        source_id = str(src.get("source_id") or "")
        if domain == CN_EQUITY_DOMAIN and not _has_structured_dh_profile(src):
            dh_path = _dh_profile_evidence(evidence_dir, source_id)
            if dh_path is None:
                blocking.append(
                    AuditFinding(
                        code="missing_data_health_profile_evidence",
                        message=f"missing data-health profile evidence for {source_id}",
                        evidence_paths=(str(evidence_dir / source_id),),
                    )
                )
            else:
                evidence_paths.append(str(dh_path))
        elif _dh_profile_evidence(evidence_dir, source_id) is not None:
            evidence_paths.append(str(_dh_profile_evidence(evidence_dir, source_id)))

        dh_summary = src.get("data_health_summary") or {}
        if _calendar_approximate(dh_summary):
            warnings.append(
                AuditFinding(
                    code="approximate_calendar_evidence",
                    message=f"calendar checks approximate for {source_id}: {dh_summary.get('gate_rationale', '')}",
                    evidence_paths=(str(report_path),),
                )
            )

        if candidate_set:
            candidate = _candidate_from_source_report(src, candidate_set=candidate_set)
            if candidate is not None:
                try:
                    validate_source_caps(candidate)
                except RehearsalPlanError as exc:
                    blocking.append(
                        AuditFinding(
                            code="uncapped_candidate_set",
                            message=str(exc),
                            evidence_paths=(str(report_path),),
                        )
                    )
            reported_count = int(src.get("symbol_or_series_count") or 0)
            if candidate is not None and reported_count > len(candidate.symbols_or_series):
                blocking.append(
                    AuditFinding(
                        code="uncapped_candidate_set",
                        message=f"{source_id} symbol_or_series_count {reported_count} exceeds capped set",
                        evidence_paths=(str(report_path),),
                    )
                )

    prov_block, prov_warn = _audit_provider_metadata(
        per_source, evidence_dir=evidence_dir, candidate_set=candidate_set
    )
    blocking.extend(prov_block)
    warnings.extend(prov_warn)
    blocking.extend(_scan_runtime_guardrails())

    if sandbox_db.is_file():
        evidence_paths.append(str(sandbox_db))
    if evidence_dir.is_dir():
        evidence_paths.append(str(evidence_dir))

    return _finalize(blocking, warnings, evidence_paths)
