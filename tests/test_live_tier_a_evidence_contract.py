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
