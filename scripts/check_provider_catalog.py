#!/usr/bin/env python3
"""provider_catalog.yaml 与 registry/capabilities/contracts 静态对齐（正式 scripts · production_gate 子步）

仅纯 YAML / catalog 交叉断言。runtime loader 行为测仍留在
tests/test_provider_catalog.py。

运行：
  uv run python scripts/check_provider_catalog.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.datasources.provider_catalog import load_provider_catalog  # noqa: E402
from backend.app.datasources.source_registry import (  # noqa: E402
    SCHEMA_CHECK_LICENSE_TYPES,
    SCHEMA_CHECK_SOURCE_TYPES,
)
from tests.contract_gate_support import load_yaml  # noqa: E402

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
SOURCE_CAPABILITY_CONTRACT = PROJECT_ROOT / "specs/contracts/source_capability_contract.yaml"
DATASOURCE_SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"

REQUIRED_PROVIDER_FIELDS = frozenset(
    {
        "provider_id",
        "source_ids",
        "source_type",
        "license_type",
        "license_or_terms",
        "allowed_domains",
        "enabled_by_default",
        "status",
        "production_default_candidate",
        "production_default_enabled",
        "requires_user_authorization",
        "requires_local_client",
        "validation_only",
        "max_default_symbols_or_series",
        "max_default_window_days",
        "reference_architecture",
        "runtime_source_copy_allowed",
    }
)
VALID_CATALOG_STATUS = frozenset(
    {"active", "sandbox_candidate", "proposed_disabled_source", "READY_WITH_EVIDENCE"}
)
PROPOSED_EXTERNAL_SOURCE_IDS = frozenset(
    {"mootdx", "eastmoney", "sina_finance", "ths_ifind"}
)
LOCAL_TERMINAL_SOURCE_IDS = frozenset({"qmt_xtdata", "tdx_pytdx", "qmt_xqshare"})


def _registry_by_id() -> dict[str, dict]:
    registry = load_yaml(SOURCE_REGISTRY)
    return {s["source_id"]: s for s in registry.get("sources") or []}


def _catalog_providers() -> list[dict]:
    return list(load_provider_catalog().get("providers") or [])


def _catalog_source_to_provider() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for entry in _catalog_providers():
        for sid in entry.get("source_ids") or []:
            mapping[sid] = entry
    return mapping


def _run() -> list[str]:
    errors: list[str] = []
    registry_ids = {s["source_id"] for s in load_yaml(SOURCE_REGISTRY).get("sources") or []}
    catalog_map = _catalog_source_to_provider()
    providers = _catalog_providers()

    if set(catalog_map.keys()) != registry_ids:
        errors.append(
            f"registry/catalog source sets differ: "
            f"only_registry={sorted(registry_ids - set(catalog_map))} "
            f"only_catalog={sorted(set(catalog_map) - registry_ids)}"
        )
    if len(providers) != len(registry_ids):
        errors.append(
            f"len(providers)={len(providers)} != len(registry)={len(registry_ids)}"
        )

    for entry in providers:
        pid = entry.get("provider_id", "<unknown>")
        absent = REQUIRED_PROVIDER_FIELDS - set(entry.keys())
        if absent:
            errors.append(f"{pid}: missing fields {sorted(absent)}")
        if entry.get("source_type") not in SCHEMA_CHECK_SOURCE_TYPES:
            errors.append(f"{pid}: invalid source_type={entry.get('source_type')!r}")
        if entry.get("license_type") not in SCHEMA_CHECK_LICENSE_TYPES:
            errors.append(f"{pid}: invalid license_type={entry.get('license_type')!r}")
        if entry.get("status") not in VALID_CATALOG_STATUS:
            errors.append(f"{pid}: invalid status={entry.get('status')!r}")
        if entry.get("runtime_source_copy_allowed") is not False:
            errors.append(f"{pid}: runtime_source_copy_allowed must be false")

    for sid in PROPOSED_EXTERNAL_SOURCE_IDS:
        entry = catalog_map.get(sid)
        if entry is None:
            errors.append(f"proposed external missing from catalog: {sid}")
            continue
        if entry.get("enabled_by_default"):
            errors.append(f"{sid}: enabled_by_default")
        if entry.get("production_default_enabled"):
            errors.append(f"{sid}: production_default_enabled")

    has_distinct_candidate = False
    for entry in providers:
        candidate = bool(entry.get("production_default_candidate"))
        enabled = bool(entry.get("production_default_enabled"))
        if candidate and not enabled:
            has_distinct_candidate = True
        if enabled:
            errors.append(
                f"{entry.get('provider_id')}: production_default_enabled must stay false"
            )
    if not has_distinct_candidate:
        errors.append("expected production_default_candidate without enabled")

    fred = catalog_map.get("fred")
    if fred is None:
        errors.append("fred missing from catalog")
    else:
        if fred.get("requires_user_authorization") is not True:
            errors.append("fred.requires_user_authorization must be true")
        if fred.get("enabled_by_default") is not False:
            errors.append("fred.enabled_by_default must be false")
    for sid in LOCAL_TERMINAL_SOURCE_IDS:
        entry = catalog_map.get(sid)
        if entry is None:
            errors.append(f"local terminal missing from catalog: {sid}")
        elif entry.get("enabled_by_default") is not False:
            errors.append(f"{sid}: enabled_by_default must be false")

    openbb = catalog_map.get("openbb_provider_reference")
    if openbb is None:
        errors.append("openbb_provider_reference missing from catalog")
    else:
        if openbb.get("runtime_source_copy_allowed") is not False:
            errors.append("openbb runtime_source_copy_allowed must be false")
        if openbb.get("reference_architecture") != "openbb_provider_architecture":
            errors.append("openbb reference_architecture mismatch")
        if openbb.get("status") != "proposed_disabled_source":
            errors.append(f"openbb status={openbb.get('status')!r}")

    caps = load_yaml(SOURCE_CAPABILITIES).get("sources") or {}
    for sid, cap_entry in caps.items():
        cap_status = cap_entry.get("status")
        if cap_status is None:
            continue
        cat = catalog_map.get(sid)
        if cat is None:
            errors.append(f"{sid}: in capabilities but missing from catalog")
            continue
        if cat.get("status") != cap_status:
            errors.append(
                f"{sid}: catalog status={cat.get('status')!r} cap={cap_status!r}"
            )

    registry = _registry_by_id()
    for sid, reg in registry.items():
        cat = catalog_map.get(sid)
        if cat is None:
            continue
        reg_enabled = bool(reg.get("enabled_by_default", False))
        cat_enabled = bool(cat.get("enabled_by_default", False))
        if cat_enabled and not reg_enabled:
            errors.append(f"{sid}: catalog enabled_by_default looser than registry")
        if bool(reg.get("validation_only", False)) != bool(cat.get("validation_only", False)):
            errors.append(f"{sid}: validation_only mismatch")
        needs_auth = bool(reg.get("requires_user_setup") or reg.get("auth_required"))
        if needs_auth and not cat.get("requires_user_authorization"):
            errors.append(f"{sid}: requires_user_authorization missing")
        if cat.get("source_type") != reg.get("source_type"):
            errors.append(f"{sid}: source_type drift")
        if cat.get("license_type") != reg.get("license_type"):
            errors.append(f"{sid}: license_type drift")

    expected = "specs/datasource_registry/provider_catalog.yaml"
    cap_contract = load_yaml(SOURCE_CAPABILITY_CONTRACT)
    svc_contract = load_yaml(DATASOURCE_SERVICE_CONTRACT)
    if cap_contract.get("provider_catalog_path") != expected:
        errors.append("source_capability_contract.provider_catalog_path mismatch")
    if svc_contract.get("provider_catalog_path") != expected:
        errors.append("datasource_service_contract.provider_catalog_path mismatch")
    if not (PROJECT_ROOT / expected).is_file():
        errors.append(f"missing {expected}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: provider catalog YAML alignment")
        return 0
    print("FAIL: provider catalog YAML alignment")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
