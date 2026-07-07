from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_authority_acceptance_language import build_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_authorityAcceptanceLanguageGuard_reportsStageVocabulary(
    tmp_path: Path,
) -> None:
    """覆盖范围：authority docs/contracts 中的执行阶段词检测
    测试对象：check_authority_acceptance_language.build_report
    目的/目标：权威文件若重新出现 Phase/阶段/BATCH 口径，guard 必须能报告出来
    验证点：violation_count==1；rule=execution_stage_vocabulary；定位到 fixture 行
    失败含义：阶段计划可能再次渗入产品权威口径，后续执行者会误判最终目标
    """
    doc = tmp_path / "authority.md"
    doc.write_text("# Authority\n\nPhase 2: use mock first\n", encoding="utf-8")

    report = build_report([doc], root=tmp_path)

    assert report["status"] == "FAIL"
    assert report["violation_count"] == 1
    assert report["violations"][0]["rule"] == "execution_stage_vocabulary"
    assert report["violations"][0]["line"] == 3


def test_authorityAcceptanceLanguageGuard_rejectsMockAsAcceptanceSuccess(
    tmp_path: Path,
) -> None:
    """覆盖范围：mock/replay/dry_run/not_implemented 被写成验收成功的检测
    测试对象：check_authority_acceptance_language.build_report
    目的/目标：非 live 模式只能作为诚实分类，不能被权威文件描述成产品验收通过
    验证点：mock PASS 触发 non_live_mode_as_acceptance_success；否定句不触发
    失败含义：mock 或 dry-run 结果可能再次被当作成品验收完成证据
    """
    bad = tmp_path / "bad.md"
    good = tmp_path / "good.md"
    bad.write_text("mock PASS closes production acceptance\n", encoding="utf-8")
    good.write_text("mock cannot count as product acceptance success\n", encoding="utf-8")

    report = build_report([bad, good], root=tmp_path)

    assert report["status"] == "FAIL"
    assert report["violation_count"] == 1
    assert report["violations"][0]["rule"] == "non_live_mode_as_acceptance_success"
    assert report["violations"][0]["path"] == "bad.md"


def test_authorityAcceptanceLanguageGuard_cliStrictFailsOnViolations(
    tmp_path: Path,
) -> None:
    """覆盖范围：authority language guard 的 CLI 严格模式
    测试对象：scripts/check_authority_acceptance_language.py --strict --format json
    目的/目标：清理完成后可把 guard 升级为 gate，违规时机器可读且 exit 非零
    验证点：returncode==1；stdout JSON 可解析；status=FAIL
    失败含义：guard 只能人工阅读，无法接入 CI 或生产 gate
    """
    doc = tmp_path / "authority.md"
    doc.write_text("dry_run SUCCESS completes acceptance\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_authority_acceptance_language.py",
            "--format",
            "json",
            "--strict",
            str(doc),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "FAIL"
    assert payload["violation_count"] == 1
