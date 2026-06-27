# Audit Repair Manifest — R3H-01（零遗留）

> 来源：`research/audit-evidence/a1.md`–`a8.md` · `audit.report.md`  
> 完成标准：每条登记 **CLOSED** + 证据；`uv run pytest -q` exit 0；`loop_maintain` OK

## A4（全部 P1–P3）

- [x] P1-01 契约字段：`source_capabilities.yaml` 与 port 输出对齐（bundle vs row fields）；`test_r3h01_capabilityFields_matchPortOutput`
- [x] P1-02 cftc/bis/world_bank cap 负例 pytest
- [x] P1-03 FRED `MAX_SERIES` cap 负例
- [x] P1-04 未授权断言收紧为 `USER_AUTH_REQUIRED` only
- [x] P1-05 `read_fred_evidence_bundle` 缺 hash 时 fail-closed + corrupt-bundle 负例
- [x] P1-06 六源 route DISABLED 断言对称（`selected_source_id is None` + `enabled is False`）
- [x] P2-01 `test_*_capsMatchRegistry` 六源 parity
- [x] P2-02 cap `max_rows<=0` 消息/状态码改进
- [x] P2-03 us_treasury yield 观测行字段对齐
- [x] P2-04 route DISABLED 测试去重（parametrize 单入口）
- [x] P2-05 `contract_coverage.yaml` 官方源负例登记
- [x] P3-01 FRED `MAX_WINDOW_DAYS` 负例或 parity
- [x] P3-02 弱化 `len(observations)==3` 硬编码
- [x] P3-03 （保留 ops re-export — 已正确，登记 CLOSED-by-design）

## A8（G-01–G-11）

- [x] G-01 Layer smoke 负例（缺 content_hash/source_fetch_id）
- [x] G-02–G-04 cap 负例（与 P1-02 合并验收）
- [x] G-05 FRED series/window cap（与 P1-03/P3-01）
- [x] G-06 cftc/bis/world_bank route READY 正例
- [x] G-07 SEC Form4 + BIS credit_gap route 测；credit_gap replay 或删死代码
- [x] G-08 `schema_hash`/`fetch_log` 实现+断言（若活卡 §5 要求）
- [x] G-09 hash/id 断言绑 fixture 常量
- [x] G-10 route DISABLED 断言完整（与 P1-06）
- [x] G-11 删除/替换 `assert True` boot 骨架

## A2 Ponytail

- [x] 六 port 共享 `_finalize_bundle`/`_reject_over_cap` helper
- [x] 删 `read_bis_credit_gap_evidence_bundle` 或补 replay+测
- [x] 泛型 `read_evidence_bundle` 或合并 read\_\*
- [x] 简化 `SecEdgarLiveFetchPort`（factory reject 对齐 treasury）
- [x] 删 `bis_port` 未用 `MAX_SERIES`
- [x] `live_evidence_bridge` 直接 import normalizer

## A3 Low

- [x] SEC 弱 UA（无联系信息）自动化负例
- [x] `_resolve_raw_path` PROJECT_ROOT jail（若改动面小）

## A5

- [x] 加厚 `execute-evidence/9.5–9.8` green.txt（命令+时间戳+输出）

## A6 NB

- [x] cftc/bis/wb cap 测（与上合并）
- [x] 文档登记 pilot vs L2 FRED cap 分层（comment 或 evidence）

## A1

- [x] 合入前 GitNexus `analyze` 笔记更新 `gitnexus-audit-summary.md`（若 analyze 可跑）
