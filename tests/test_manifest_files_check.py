"""MANIFEST.json 文件存在性对抗性审计测试。

覆盖范围：MANIFEST.json 登记路径在磁盘上必须存在（B3V-REG / VR-DOC-001）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_manifest_files import check_manifest  # noqa: E402

MANIFEST = PROJECT_ROOT / "MANIFEST.json"
FINAL_AUDIT_REPORT = "FINAL_AUDIT_REPORT.md"


def test_checkManifest_reportsMissingFinalAuditReportUntilRegRestores() -> None:
    """覆盖范围：MANIFEST 幽灵文件检测
    测试对象：check_manifest 对 FINAL_AUDIT_REPORT.md
    目的/目标：在 B3V-REG restore-or-replace 前，checker 必须能检出缺失项（非静默通过）
    验证点：errors 含 missing file: FINAL_AUDIT_REPORT.md（若文件仍缺失）
    失败含义：manifest 与文件树漂移无法被 CI 发现，VR-DOC-001 可被表面关闭
    """
    errors = check_manifest(MANIFEST)
    report_path = PROJECT_ROOT / FINAL_AUDIT_REPORT
    if report_path.is_file():
        missing_final = [e for e in errors if FINAL_AUDIT_REPORT in e]
        assert not missing_final, f"report exists but checker still errors: {missing_final}"
    else:
        assert any(FINAL_AUDIT_REPORT in e for e in errors), (
            f"expected missing {FINAL_AUDIT_REPORT} in errors, got: {errors}"
        )


def test_checkManifest_noOtherMissingFiles() -> None:
    """覆盖范围：MANIFEST.json 全集存在性（除已知 VR-DOC-001 项外）
    测试对象：check_manifest 全量 errors
    目的/目标：除 FINAL_AUDIT_REPORT 外不得有其它 missing file 项
    验证点：过滤 FINAL_AUDIT_REPORT 后 errors 为空
    失败含义：README/MANIFEST 与真实文件树不一致，文档闭合不可信
    """
    errors = check_manifest(MANIFEST)
    other_missing = [
        e for e in errors if e.startswith("missing file:") and FINAL_AUDIT_REPORT not in e
    ]
    assert other_missing == [], f"unexpected manifest gaps: {other_missing}"
