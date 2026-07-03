# Audit A2 — Ponytail（wave4-r3-dcp-05-tier-a）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **diff 基线：** `git diff master...HEAD`（93 files · +7062 / −105）

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                 | 证据                                                                                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --stat`  | 93 files changed, 7062 insertions(+), 105 deletions(−)                                                                                                                                                   |
| S00 触及           | `015_dcp05_tier_a_clean.sql` (+72) · `clean_write_targets.py` (+33 net) · `incremental_source_registry.py` (+60)                                                                                         |
| ≥20 行新增后端模块 | `macro_incremental_common.py` (+505) · `cninfo_incremental_run.py` (+373) · `deribit_incremental_run.py` (+365) · `sec_edgar_incremental_run.py` (+355) · `alpha_vantage_incremental_run.py` (+270) · 等 |
| DOUBT 搜索范围     | `backend/app/ops/*incremental*` · `clean_write_targets.py` · `incremental_source_registry.py` · `015_*.sql` · 对照 `fred_incremental_*` / `baostock_incremental_run.py`                                  |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                   | ponytail 梯级                 | 备注                                                                                    |
| ---------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------- |
| `clean_write_targets.py:25-34` MACRO_DOMAINS 缺 ADR 三别名 | 梯级 1（YAGNI 与 ADR 不一致） | ADR-028 §Decision-2 列全、实现未列全；见 A2-P2-001                                      |
| `us_treasury_incremental_watermark.py` 全文 (~29 LOC)      | 梯级 2（复用 common）         | 仅 re-export + 一行 wrapper；见 A2-P2-002                                               |
| `bis_incremental_watermark.py` 全文 (~35 LOC)              | 梯级 2                        | 同上；`watermark_start_year` 可留 run 模块                                              |
| `world_bank_incremental_watermark.py` 全文 (~36 LOC)       | 梯级 2                        | 同上                                                                                    |
| `cftc_incremental_watermark.py` 全文 (~38 LOC)             | 梯级 2                        | `read_since_dates_for_markets` 可内联 run                                               |
| `cninfo_incremental_watermark.py:41-63`                    | 梯级 2                        | 重复 `enabled_source_registry`；见 A2-P2-003                                            |
| `sec_edgar_incremental_watermark.py:43-65`                 | 梯级 2                        | 同上                                                                                    |
| `deribit_incremental_watermark.py:46-68`                   | 梯级 2                        | 同上                                                                                    |
| `alpha_vantage_incremental_run.py:137-159`                 | 梯级 2                        | 同上                                                                                    |
| `sec_edgar_incremental_run.py:157-204` validation patch    | 梯级 2 + A4 重叠              | ~48 LOC；见 A2-P3-002                                                                   |
| `cninfo_incremental_run.py:174-222` validation patch       | 梯级 2 + A4 重叠              | ~49 LOC                                                                                 |
| `deribit_incremental_run.py:164-211` validation patch      | 梯级 2 + A4 重叠              | ~48 LOC                                                                                 |
| `sec_edgar_incremental_run.py:227-240` FetchProxy          | 梯级 2                        | 与 `MacroIncrementalFetchProxy` 同形；见 A2-P3-001                                      |
| `alpha_vantage_incremental_run.py:162-171` route bundle    | 梯级 2                        | 与 `macro_incremental_common._load_incremental_route_bundle` 同形                       |
| `015_dcp05_tier_a_clean.sql` 全文                          | —（不计 bloat）               | ENTRY/S00 explicit AC；四表对称 staging 为 R3H-06 惯例                                  |
| `incremental_source_registry.py` 全文                      | —（PASS）                     | 表驱动 + `TIER_A_SOURCES` drift guard；60 LOC 合理                                      |
| `macro_incremental_common.py` 全文 (+505)                  | —（PASS）                     | 4 宏观源 + CLI/tests 多消费者；`plan-doubt-review` D4 已 reconcile；有 `ponytail:` 注释 |
| `baostock_incremental_run.py` (+99)                        | —（PASS）                     | 薄编排对照样本                                                                          |

### S00 专项（migration 015 + clean_write_targets + ADR-028）

| 工件                               | 裁决                                                                                                                                                  |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **migration 015**                  | **最小正确**：仅 ADR 要求的两组 clean+staging（SEC / crypto）；无多余表或索引                                                                         |
| **incremental_source_registry**    | **最小正确**：11 行 canonical domain + drift guard                                                                                                    |
| **clean_write_targets 矩阵**       | **结构合理**（BAR / METADATA / US_DISCLOSURE / CRYPTO / MACRO 分支清晰）；**但与 ADR-028 §Decision-2 不完全一致**（缺 3 个 macro 别名，见 A2-P2-001） |
| **BAR 扩域**（`etf_daily_bar` 等） | ADR 明示要求；非 DCP-05 11 源增量路径未用，但属计划内 SSOT，**不算 bloat**                                                                            |

### A4 交叉引用

- `_sec_edgar` / `_cninfo` / `_deribit` `_incremental_validation_patch` 与 `macro_incremental_common.macro_incremental_validation_patch`（`151-199`）及 `fred_incremental_run._macro_incremental_validation_patch` 同型重复 → A2-P3-002

---

## §维度裁决

**FAIL**

（§计划内 2 条 + §计划外 4 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                            | 锚点                                                                                                                                                              | 根因                                                                                                                                                                                                                                                                | 修复方案                                                                                                                                | 验证                                                                                                                                                                             |
| --------- | --- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-001 | P2  | ADR-028 MACRO 别名矩阵未落全    | `backend/app/ops/sandbox_clean_write/clean_write_targets.py:25-34` · `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md:14`                           | ADR §Decision-2 要求 `MACRO_DOMAINS` 含 `inflation_expectation`、`credit_gap`、`global_macro_reference`；实现仅 5 个别名。ports（`us_treasury_port` / `bis_port` / `world_bank_port`）已支持这些 domain，但 `resolve_clean_write_target` 会 `CleanWriteTargetError` | 在 `MACRO_DOMAINS` 补全三域名 **或** 修订 ADR-028 并注明 DCP-05 仅 canonical 域、次域波次外置                                           | `uv run pytest tests/test_r3h06_clean_schema.py tests/test_tierA_incremental_registry.py -q`；对三 domain 各加一条 `resolve_clean_write_target` 断言                             |
| A2-P2-002 | P2  | 四份宏观 watermark 薄 shim 可删 | `backend/app/ops/us_treasury_incremental_watermark.py` · `bis_incremental_watermark.py` · `world_bank_incremental_watermark.py` · `cftc_incremental_watermark.py` | 各文件 ~29–38 LOC，主体为从 `macro_incremental_common` re-export + `enabled_*` 一行包装；仅 bis `watermark_start_year`、cftc `read_since_dates_for_markets` 有源特异逻辑                                                                                            | 常量与特异 helper 移入对应 `*_incremental_run.py`；run/tests 直接 `from macro_incremental_common import …`；删除四 shim 文件并改 import | `uv run pytest tests/test_us_treasury_incremental_watermark.py tests/test_bis_incremental_e2e.py tests/test_world_bank_incremental_e2e.py tests/test_cftc_incremental_e2e.py -q` |

---

## 计划外发现

| ID        | P   | 标题                                         | 锚点                                                                                                                                                                                                | 根因                                                                                                | 修复方案                                                                                                                                                       | 验证                                                                                                                                                                              |
| --------- | --- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-003 | P2  | `enabled_source_registry` 五处复制           | `cninfo_incremental_watermark.py:41-63` · `sec_edgar_incremental_watermark.py:43-65` · `deribit_incremental_watermark.py:46-68` · `alpha_vantage_incremental_run.py:137-159`（及 run 内 import 链） | `macro_incremental_common.enabled_source_registry`（`87-110`）已存在；每处 ~23 LOC 同型 monkeypatch | 全部改为 `enabled_source_registry(source_id=..., data_domain=...)`；删除本地 `enabled_*_source_registry` 定义                                                  | `uv run pytest tests/test_cninfo_incremental_e2e.py tests/test_sec_edgar_incremental_e2e.py tests/test_deribit_incremental_e2e.py tests/test_alpha_vantage_incremental_e2e.py -q` |
| A2-P3-001 | P3  | SEC FetchProxy 重复 Macro 代理               | `sec_edgar_incremental_run.py:227-240` vs `macro_incremental_common.py:309-331`                                                                                                                     | 单消费者 wrapper；仅 `operation` 与 dict 名不同                                                     | `run_sec_edgar_incremental` 复用 `MacroIncrementalFetchProxy`（`operation="fetch_filings"`）                                                                   | `uv run pytest tests/test_sec_edgar_incremental_e2e.py -q`                                                                                                                        |
| A2-P3-002 | P3  | 三份 disclosure/crypto validation patch 重复 | `sec_edgar_incremental_run.py:157-204` · `cninfo_incremental_run.py:174-222` · `deribit_incremental_run.py:164-211`                                                                                 | 各 ~48 LOC，与 `macro_incremental_validation_patch` 仅 `expected_columns` / `timestamp_fields` 不同 | 在 `macro_incremental_common` 增加参数化 factory，例如 `incremental_validation_patch(expected_columns=..., timestamp_fields=...)`；三处改为单行 contextmanager | `uv run pytest tests/test_sec_edgar_incremental_e2e.py tests/test_cninfo_incremental_e2e.py tests/test_deribit_incremental_e2e.py -q`                                             |
| A2-P3-003 | P3  | `_load_*_route_bundle` 四重复制              | `alpha_vantage_incremental_run.py:162-171` · `sec_edgar_incremental_run.py:249-259` · `deribit_incremental_run.py`（同型）· `cninfo_incremental_run.py`（同型）                                     | `macro_incremental_common._load_incremental_route_bundle`（`354-365`）已封装 registry/caps/planner  | 导出 `_load_incremental_route_bundle`（或 public `load_incremental_route_bundle`）并在四 run 模块调用                                                          | `uv run pytest tests/test_alpha_vantage_incremental_e2e.py tests/test_sec_edgar_incremental_e2e.py tests/test_deribit_incremental_e2e.py tests/test_cninfo_incremental_e2e.py -q` |

已对抗搜索：`backend/app/ops/*incremental*` 全量对照 `fred_incremental_run.py` / `baostock_incremental_run.py`；`clean_write_targets.py` 与 ADR-028 全文；`master...HEAD` backend 文件列表（`tier_a_sync_router.py` 未入分支 commit，未纳入本维 diff 审计）。

### 做得好的地方

- **migration 015** 与 **incremental_source_registry** 符合 ponytail：无多余抽象，漂移检测有价值。
- **`macro_incremental_common.py`** 在四宏观源间抽共享路径，符合 `plan-doubt-review` D4，避免四份完整 copy。
- **`baostock_incremental_run.py`** 保持 ~100 LOC 薄编排，是 bar 源合理标杆。
- **`clean_write_targets`** 新增 US_DISCLOSURE / CRYPTO 分支与 015 表一一对应，未引入 factory/registry 过度层。
