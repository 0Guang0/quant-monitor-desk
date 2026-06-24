# Integration Ledger — B01-FRED

> Plan 5c · v3 context packing

## 打包策略

| 策略 | 含义 |
| ---- | ---- |
| inline | MASTER §0/§3 已摘要 |
| summary+pointer | MASTER 摘要 + 原稿 |
| pointer | implement extract/for 精读 |

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
| ------ | -------- | -------- | ------------- | --------------- | ----------- |
| `research/integration-ledger.md` | rule | inline | MASTER §0.4 | v3 boot routing | §9.0 |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md` | decision | summary+pointer | MASTER §1.6 | B2.5-O-05 语义 | AC-FRED-06 |
| `BATCH_01_HARDENING_RULES.md` | rule | summary+pointer | MASTER §0 | §3 授权 YAML | 全 AC |
| `docs/quality/production_live_pilot_policy.md` | rule | summary+pointer | MASTER §0 | fail-closed staged | AC-FRED-06 |
| `specs/contracts/source_route_contract.yaml` | contract | pointer | MASTER §6 | route status | AC-FRED-02 |
| `specs/contracts/data_quality_rules.yaml` | contract | pointer | MASTER §5 | quality_flags | AC-FRED-05 |
| `R3E_fred_authorized_sandbox_pilot.md` | business | pointer | MASTER §2 | FRED sandbox AC | AC-FRED-01..07 |
| `docs/architecture/04_data_architecture.md` | architecture | pointer | MASTER §4 | raw/staging 分层 | AC-FRED-03 |
| `backend/app/ops/staged_pilot.py` | wiring | pointer | MASTER §4 | pilot 复用模式 | §9.3 |
| `backend/app/datasources/route_planner.py` | wiring | pointer | MASTER §4 | route preview | §9.2 |
| `tests/test_fred_staged_semantics.py` | wiring | pointer | MASTER §5 | B2.5-O-05 基线 | §9.6 |
| `018B_production_live_pilot_gate.md` | rule | summary+pointer | MASTER §0 | legacy L05 live gate | AC-FRED-07 |
| `datasource_service_contract.yaml` | contract | pointer | MASTER §3.1 | sanctioned fetch | AC-FRED-03 |
| `backend/app/ops/data_health.py` | rule | summary+pointer | MASTER §3.3 | forbidden 主体只读 | FRED-05 |

## inline 清单

- §0 sandbox-only + B2.5-O-05 + live 授权模板
- §3.2 defer：data_health v2 → DH2；registry commit → 主会话
- §3.5 WL 只读引用策略
- forbidden：`data_health.py` 主体、clean write、macro 替代 FRED
