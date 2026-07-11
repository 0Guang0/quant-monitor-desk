#!/usr/bin/env python3
"""PortErrorStatus ↔ FetchResult 失败态对齐（阶段性 · 非业务 pytest）

功能：
  核对 PortErrorStatus.__args__ 与约定集合一致，且去掉 USER_AUTH_REQUIRED
  后为 CONTRACT_STATUSES 子集。对应原
  tests/test_data_adapter_contract.py::test_portErrorStatus_doesNotDriftFromFetchStatusFailures。

业务价值：
  防止 adapter 端口错误码与 FetchResult 状态漂移，映射层静默不一致。

退役 / 清理时间（满足任一即可删本文件）：
  1. PortErrorStatus 与 FetchResult.status 已由单一 SSOT（typed enum / codegen）生成；或
  2. 本检查已 promote 进正式 scripts/check_* + production_gate。

运行：
  uv run python phase-scripts/check_port_error_status_parity.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.datasources.adapters.fetch_port import PortErrorStatus  # noqa: E402

# Mirror tests/test_data_adapter_contract.py CONTRACT_STATUSES (FetchResult layer).
CONTRACT_STATUSES = [
    "SUCCESS",
    "EMPTY_RESPONSE",
    "NOT_PUBLISHED_YET",
    "DISABLED_SOURCE",
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
]

EXPECTED_PORT_STATUSES = {
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "EMPTY_RESPONSE",
    "NOT_PUBLISHED_YET",
    "DISABLED_SOURCE",
    "USER_AUTH_REQUIRED",
    "FAILED",
}


def check_port_error_status_parity(violations: list[str]) -> None:
    actual = set(PortErrorStatus.__args__)
    if actual != EXPECTED_PORT_STATUSES:
        violations.append(
            f"PortErrorStatus.__args__ drift: actual={sorted(actual)} "
            f"expected={sorted(EXPECTED_PORT_STATUSES)}"
        )
    port_layer_only = {"USER_AUTH_REQUIRED"}
    remainder = EXPECTED_PORT_STATUSES - port_layer_only
    if not remainder.issubset(set(CONTRACT_STATUSES)):
        violations.append(
            f"port statuses minus USER_AUTH_REQUIRED not subset of CONTRACT_STATUSES: "
            f"{sorted(remainder - set(CONTRACT_STATUSES))}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_port_error_status_parity(violations)

    if not violations:
        print("PASS: port error status parity")
        return 0

    print("FAIL: port error status parity")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
