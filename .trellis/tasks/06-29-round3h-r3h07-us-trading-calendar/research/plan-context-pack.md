# Plan 加固 — context-engineering

## 执行包阅读规则

- **切片开工前必读：** `research/` 全部登记文件 + `EXTERNAL-INDEX.md` §A → `00-EXECUTION-ENTRY.md` §5.2
- **执行中情境路由：** §5.3

---

## Level 1 — 常驻 Rules

- `AGENTS.md` / `CLAUDE.md` — GitNexus · ponytail · TDD
- `specs/contracts/reference_adoption_guardrails.yaml`
- `agent-toolchain.md`

---

## Level 2 — 本任务 Spec（按切片）

| 切片    | 必读                                                                  |
| ------- | --------------------------------------------------------------------- |
| **ALL** | `to-issues-slices.md` 对应 § · `calendar-baseline-matrix.md`          |
| S07-01  | **ADR-026** · `cn_trading_calendar.py`（镜像参考）                    |
| S07-02  | `datasource_service_contract.yaml` · `reference-adoption-r3h07.md` §5 |
| S07-03  | `specs/contracts/layer4_market_contract.yaml`                         |
| S07-04  | INDEX §2 负向 AC                                                      |

---

## Level 3 — 源码（按切片）

### S07-BOOT

- `calendar-baseline-matrix.md`（本目录）
- `tests/test_market_data_adapters.py`

### S07-01

- `backend/app/ops/data_health_profiles/cn_trading_calendar.py`（只读镜像）
- 新建 `us_trading_calendar.py` + 配套模块测（S07-01）

### S07-02

- `backend/app/datasources/fetch_ports/yahoo_finance_port.py`
- `backend/app/datasources/fetch_ports/stooq_port.py`
- `backend/app/datasources/fetch_ports/alpha_vantage_port.py`
- `backend/app/datasources/fetch_window.py`
- `backend/app/datasources/normalizers/market_data.py`
- `backend/app/datasources/service.py`
- `tests/test_datasource_service.py` · `tests/test_vendor_fetch_e2e.py`

### S07-03

- `backend/app/layer4_markets/market_structure.py`
- `tests/test_layer4_market_structure.py`
- `tests/fixtures/layer4_staged_market/`

### S07-04

- 上列 + `tests/test_cn_market_adapters.py`（calendar 回归）

---

## Level 4 — 工具

| 时机                 | 工具               |
| -------------------- | ------------------ |
| 改 ports / layer4 前 | GitNexus `impact`  |
| commit 前            | `detect_changes()` |
| 触 backend/specs     | `loop_maintain.py` |

---

## PROJECT CONTEXT（Execute 可复制块）

```text
任务：R3H-07 CAL-US
SSOT：us_trading_calendar.py（C3+G4 共用）
window_kind：US equity → trading_sessions
CN：不得回退 cn_trading_calendar
服务：R3H-10 DataSourceService 金路径
Out：R3H-08 live · 新 DDL · crypto calendar_days
```
