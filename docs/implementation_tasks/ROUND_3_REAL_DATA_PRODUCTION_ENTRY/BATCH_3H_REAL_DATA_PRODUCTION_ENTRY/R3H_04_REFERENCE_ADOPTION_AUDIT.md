# R3H-04 参考项目采纳追溯（CLOSED @ 2026-06-28）

> **权威规则：** `specs/contracts/reference_adoption_guardrails.yaml` · 活卡 `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` §2  
> **Trellis 归档：** `.trellis/tasks/archive/2026-06/06-28-round3h-r3h04-prediction-web/`（A3 0 OpenBB runtime · A5 audit PASS）  
> **R3H-05：** 交叉项 **REF-ADOPT-GATE**、**WEB-SEARCH-LIVE**、**KALSHI-POLY-LIVE** 须引用本文。

## 1. 批次级结论

| 项                         | 结论                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| OpenBB agents-for-openbb   | **architecture_only** — widget JSON 字段形状 → `manual_review_staging.py`；**禁止** agent loop / openbb_ai runtime |
| `coingecko_port` mock 模式 | **L2 模式参照**（非文件拷贝）— kalshi/polymarket mock 模板                                                         |
| kalshi / polymarket API    | **L3** greenfield + env-gated live smoke                                                                           |
| `web_search`               | **L3** mock stub — 真搜索 API **故意延后** @ Grill-me Q4                                                           |

## 2. 三源采纳矩阵

| source_id    | adoption_ladder           | 参考路径（只读/归档）                             | QMD 落点                                                            | direct_copy | Trellis 证据                |
| ------------ | ------------------------- | ------------------------------------------------- | ------------------------------------------------------------------- | ----------- | --------------------------- |
| `kalshi`     | **L3** + mock **L2 模式** | `coingecko_port.py` mock 形状；无 Kalshi 参考文件 | `fetch_ports/kalshi_port.py` · `probability_signal`                 | false       | A5 audit · live env-gated   |
| `polymarket` | **L3** + mock **L2 模式** | 同上                                              | `fetch_ports/polymarket_port.py`                                    | false       | 禁止 factual_resolution     |
| `web_search` | **L3** greenfield         | OpenBB widget **architecture_only**               | `fetch_ports/web_search_evidence_port.py` · `manual_review_staging` | false       | mock READY；真 API deferred |

## 3. 延后 / R3H-05 limitation

| 项                   | 处置                                       | 登记位置                  |
| -------------------- | ------------------------------------------ | ------------------------- |
| **WEB-SEARCH-LIVE**  | 真搜索 API 须用户 gate + ADR               | R3H-05 §7 · 路线图 §5.0.1 |
| **KALSHI-POLY-LIVE** | 默认真网 → mock/replay；live 须 limitation | 同上                      |
| clean factual 表写入 | **永久禁止**                               | hardening §4              |

## 4. R3H-05 审计引用

- 三源矩阵 + port `reference_adoption:` 头注释一致
- 不得将 mock-only `web_search` 标为真网搜索能力
- `test_r3h04_*` + `test_reference_adoption_guardrails` 绿
