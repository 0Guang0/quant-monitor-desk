# R3FR-02 + R3FR-06: EasyXT Data Health Profile + `qmd data health` Runtime

## Goal

- 完整 `market_bar_p0` 只读 profile engine（`run_data_health_profile`）
- `qmd data health` 去掉 `not_implemented_phase_c`，接到同一 runner

## Acceptance

- [x] AC-1..AC-9：profile rules、runner、capped 输出、CLI JSON 信封、契约、护栏、全量回归
- [x] `tests/test_data_health_easyxt_profiles.py` + `tests/test_qmd_data_cli.py` 全绿

## Evidence

- Commit: `ecf64f06` on `refactor/round3fr-data-health-cli`
- Commands: `uv run pytest -q`, `uv run python scripts/loop_maintain.py`
