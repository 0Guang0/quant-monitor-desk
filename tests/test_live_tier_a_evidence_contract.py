"""M-DATA-03 S-R2-EVIDENCE — live_tier_a_evidence_v1 contract tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.ops.tier_a_live_acceptance import (
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
    build_live_tier_a_evidence_manifest,
    fail_external_adr_ref,
    manifest_failure_class,
    source_bindings,
    write_live_tier_a_evidence_manifest,
)
from backend.app.ops.tier_a_live_incremental_dispatch import LiveIncrementalOutcome
from tests.contract_gate_support import PROJECT_ROOT

EVIDENCE_CONTRACT = PROJECT_ROOT / "specs/contracts/live_tier_a_evidence_v1.yaml"


def _load_contract() -> dict[str, Any]:
    return yaml.safe_load(EVIDENCE_CONTRACT.read_text(encoding="utf-8")) or {}


def _sample_outcome(source_id: str) -> LiveIncrementalOutcome:
    binding = source_bindings()[source_id]
    return LiveIncrementalOutcome(
        source_id=source_id,
        sync_status="COMPLETED",
        inspect_status="PASS",
        clean_table=binding["clean_table"],
        clean_row_count=1,
        detail="contract test fixture",
    )


def test_liveTierAEvidenceContract_hasElevenSourceBindings() -> None:
    """覆盖范围：live_tier_a_evidence_v1 source_bindings
    测试对象：specs/contracts/live_tier_a_evidence_v1.yaml
    目的/目标：契约登记 11 源且与 TIER_A_SOURCES 一致
    验证点：len(bindings)==11；键集合等于 TIER_A_SOURCES
    失败含义：验收层源清单与 live tier router 漂移
    """
    bindings = source_bindings()
    assert len(bindings) == 11
    assert frozenset(bindings) == TIER_A_SOURCES


@pytest.mark.parametrize(
    ("report_class", "manifest_class"),
    [
        ("PASS", "none"),
        ("FAIL_FIXABLE", "fixable_technical"),
        ("FAIL_EXTERNAL", "external_environment"),
    ],
)
def test_manifestFailureClass_usesCanonicalMapping(
    report_class: str, manifest_class: str
) -> None:
    """覆盖范围：failure_class_canonical.mapping
    测试对象：manifest_failure_class
    目的/目标：report/CLI 词汇与 manifest acceptance.failure_class 按契约映射
    验证点：三类 report 值映射到 manifest 枚举
    失败含义：验收报告与 manifest 失败分类不一致
    """
    assert manifest_failure_class(report_class) == manifest_class


@pytest.mark.parametrize("source_id", sorted(TIER_A_SOURCES))
def test_buildManifest_requiredTopLevelFieldsPerSource(source_id: str) -> None:
    """覆盖范围：envelope.required_top_level_fields × 11 source_bindings
    测试对象：build_live_tier_a_evidence_manifest
    目的/目标：每源 manifest 含契约顶层字段
    验证点：required_top_level_fields 全存在；schema_version 正确
    失败含义：某源证据信封缺字段，下游 F0/B2 无法消费
    """
    contract = _load_contract()
    required = contract["envelope"]["required_top_level_fields"]
    data_root = PROJECT_ROOT / ".audit-sandbox" / "m-data-03" / "contract-fixture"
    manifest = build_live_tier_a_evidence_manifest(
        source_id=source_id,
        data_root=data_root,
        run_id="run-contract",
        job_id="job-contract",
        outcome=_sample_outcome(source_id),
        report_failure_class="PASS",
    )
    for field in required:
        assert field in manifest, f"{source_id} missing top-level {field}"
    assert manifest["schema_version"] == SCHEMA_VERSION


@pytest.mark.parametrize("source_id", sorted(TIER_A_SOURCES))
def test_buildManifest_fetchRequiredFieldsPerSource(source_id: str) -> None:
    """覆盖范围：envelope.fetch.required_fields × 11 source_bindings
    测试对象：build_live_tier_a_evidence_manifest fetch 段
    目的/目标：每源 manifest fetch 含契约七字段且 status 合法
    验证点：required_fields 全存在；status ∈ status_enum
    失败含义：fetch 子结构缺位，下游无法对齐 raw_evidence
    """
    contract = _load_contract()
    fetch_spec = contract["envelope"]["fetch"]
    required = fetch_spec["required_fields"]
    status_enum = set(fetch_spec["status_enum"])
    data_root = PROJECT_ROOT / ".audit-sandbox" / "m-data-03" / "contract-fetch-fixture"
    manifest = build_live_tier_a_evidence_manifest(
        source_id=source_id,
        data_root=data_root,
        run_id="run-fetch",
        job_id="job-fetch",
        outcome=_sample_outcome(source_id),
        report_failure_class="PASS",
    )
    fetch = manifest["fetch"]
    for field in required:
        assert field in fetch, f"{source_id} missing fetch.{field}"
    assert fetch["status"] in status_enum


@pytest.mark.parametrize("source_id", sorted(TIER_A_SOURCES))
def test_buildManifest_acceptanceMatchesSourceBinding(source_id: str) -> None:
    """覆盖范围：source_bindings × acceptance 子结构
    测试对象：build_live_tier_a_evidence_manifest acceptance 段
    目的/目标：每源 clean_table/health/rule_set 与契约 binding 对齐
    验证点：acceptance 五字段等于 binding；disposition/failure_class 合法
    失败含义：manifest 绑定错域，F0/B2 profile 跑错表
    """
    contract = _load_contract()
    binding = contract["source_bindings"][source_id]
    acceptance_spec = contract["envelope"]["acceptance"]
    data_root = PROJECT_ROOT / ".audit-sandbox" / "m-data-03" / "contract-fixture"
    manifest = build_live_tier_a_evidence_manifest(
        source_id=source_id,
        data_root=data_root,
        run_id="run-binding",
        job_id="job-binding",
        outcome=_sample_outcome(source_id),
        report_failure_class="PASS",
    )
    acceptance = manifest["acceptance"]
    for field in (
        "clean_table",
        "rule_set_id",
        "health_domain",
        "health_profile_id",
    ):
        assert acceptance[field] == binding[field]
    assert acceptance["disposition"] in acceptance_spec["disposition_enum"]
    assert acceptance["failure_class"] in acceptance_spec["failure_class_enum"]
    forbidden = acceptance_spec["forbidden"]
    for value in forbidden:
        assert value not in json.dumps(acceptance).lower()


def test_fetchSchemaHash_fromRawBundleMetadata(tmp_path: Path) -> None:
    """覆盖范围：fetch.schema_hash 与 raw bundle 对齐
    测试对象：build_live_tier_a_evidence_manifest fetch.schema_hash
    目的/目标：manifest 读取 raw JSON schema_hash，禁止 source_id 占位 digest
    验证点：落盘 raw 含 schema_hash 时 manifest 一致
    失败含义：schema_hash 技术债未清，证据链不可审计
    """
    from backend.app.datasources.normalizers.evidence_bundle import schema_hash_for_version

    data_root = tmp_path / "sandbox"
    raw_dir = data_root / "raw" / "fred" / "2026-07-03"
    raw_dir.mkdir(parents=True)
    expected_hash = schema_hash_for_version("official_macro_evidence_v1")
    raw_path = raw_dir / "bundle.json"
    raw_path.write_text(
        json.dumps(
            {
                "schema_version": "official_macro_evidence_v1",
                "schema_hash": expected_hash,
                "source_id": "fred",
            }
        ),
        encoding="utf-8",
    )
    manifest = build_live_tier_a_evidence_manifest(
        source_id="fred",
        data_root=data_root,
        run_id="run-schema",
        job_id="job-schema",
        outcome=_sample_outcome("fred"),
        report_failure_class="PASS",
    )
    assert manifest["fetch"]["schema_hash"] == expected_hash
    assert manifest["fetch"]["schema_hash"] != __import__("hashlib").sha256(
        b"fred"
    ).hexdigest()


def test_failExternalAdrRef_matchesContractAuthority() -> None:
    """覆盖范围：FAIL_EXTERNAL adr_ref SSOT
    测试对象：fail_external_adr_ref
    目的/目标：adr_ref 从契约 authoritative_docs 解析，非硬编码常量
    验证点：返回值 == ADR-015；契约 fail_external_requires_adr 为 true
    失败含义：外部失败 ADR 与契约漂移，exit 0 路径不可信
    """
    contract = _load_contract()
    invariants = contract.get("invariants") or []
    merged: dict[str, Any] = {}
    if isinstance(invariants, list):
        for item in invariants:
            if isinstance(item, dict):
                merged.update(item)
    elif isinstance(invariants, dict):
        merged = invariants
    assert merged.get("fail_external_requires_adr") is True
    assert fail_external_adr_ref() == "ADR-015"


def test_writeManifest_persistsUnderEvidenceDir(tmp_path: Path) -> None:
    """覆盖范围：manifest 落盘路径
    测试对象：write_live_tier_a_evidence_manifest
    目的/目标：写入 live_tier_a_evidence_manifest.json 于 evidence_dir_relative
    验证点：文件存在；JSON 可解析；文件名符合 envelope
    失败含义：acceptance 无法定位 per-source 证据
    """
    data_root = tmp_path / "sandbox"
    data_root.mkdir()
    manifest = build_live_tier_a_evidence_manifest(
        source_id="fred",
        data_root=data_root,
        run_id="run-write",
        job_id="job-write",
        outcome=_sample_outcome("fred"),
        report_failure_class="PASS",
    )
    path = write_live_tier_a_evidence_manifest(manifest, data_root=data_root)
    assert path.name == MANIFEST_FILENAME
    assert path.is_file()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["source_id"] == "fred"
