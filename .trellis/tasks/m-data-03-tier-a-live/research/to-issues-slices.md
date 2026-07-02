# M-DATA-03 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **前置：** R3-DCP-05 CLOSED（replay 逻辑）· ADR-027/028 · 用户 11/11 真网

---

## 垂直切片规则

1. 每片：**单源 live** 或 **共享 live 基础设施**；可独立 pytest 绿。
2. RED → GREEN：v4.1 **code-first** — pytest/代码即证据（`EXECUTION_INDEX.md` §1 · frozen §9 `[x]`）；**不**要求 `research/execute-evidence/sNN-*.txt`
3. Live 测试须：`QMD_ALLOW_LIVE_FETCH=1` + 隔离 `DATA_ROOT`（ADR-034）
4. `product_live_gate` / `data_commands.py` / 共享 harness：**S00-INFRA 独占 merge**
5. registry 三件套：**S-MERGE 主会话**
6. **借鉴梯：** 仅 `参考项目/**`；仓内 DCP-05 = **直接复用**，禁止标 L1/L2/L3（见 `reference-adoption-m-data-03.md` §0）
7. Execute RED 前：**L2** 列改造清单 · **L3** 列 SDD 官方 API（`plan-spec.md`）· **forbidden** 列负向测

---

## 依赖图

```text
S00-ELIGIBILITY
  → S00-INFRA（live harness + pytest.network + acceptance 脚本壳）
  → 批次 2a：S-LIVE-FRED ∥ S-LIVE-BAOSTOCK
  → 批次 2b：S-LIVE-US-TREASURY ∥ S-LIVE-BIS ∥ S-LIVE-WORLDBANK ∥ S-LIVE-CFTC ∥ S-LIVE-SEC-EDGAR
  → 批次 2c：S-LIVE-ALPHA-VANTAGE ∥ S-LIVE-DERIBIT ∥ S-LIVE-CNINFO ∥ S-LIVE-MOOTDX
  → S-MERGE（registry + test_catalog）
  → S-ACCEPT（11/11 隔离验收）
```

---

## 切片总表

| Slice                    | What to build                                                                                                                                                         | Acceptance criteria                                                                                 | Blocked by                | 测试 / 证据                                         |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------- | --------------------------------------------------- |
| **S00-ELIGIBILITY**      | `research/tier-a-live-eligibility.md` 固化路线图 §0.3.4                                                                                                               | 11/11 须真网；KEY 槽位列出；无 ADR 例外行                                                           | —                         | 文档评审 · ENTRY §4                                 |
| **S00-INFRA**            | 隔离 `DATA_ROOT` fixture；`@pytest.mark.network`；`tier_a_live_acceptance.py`（exit 0/1/2 契约见 `plan-spec.md`）；**负向测**：无 env 闸 / 主库路径 / silent fallback | infra 单测绿；负向 3 项绿；默认套件无 live 不 fail                                                  | S00-ELIGIBILITY           | `tests/test_tier_a_live_harness.py`                 |
| **S-LIVE-FRED**          | 仓内 `fred_port` live；`use_mock=False`                                                                                                                               | live e2e 写 `axis_observation`；inspect/health 无 P0；**借鉴 L3** + SDD FRED API                    | S00-INFRA + **2a 试点门** | `test_fred_macro_incremental_e2e.py` `-m network`   |
| **S-LIVE-BAOSTOCK**      | 仓内 `baostock` live                                                                                                                                                  | live e2e 绿；幂等；**借鉴 L3**；EasyXT forbidden 负向确认                                           | S00-INFRA + **2a 试点门** | `test_baostock_incremental_e2e.py` `-m network`     |
| **S-LIVE-US-TREASURY**   | 仓内 ops live                                                                                                                                                         | live clean 绿；**借鉴 L3**；SDD Treasury API                                                        | **2a 试点绿**             | `test_us_treasury_incremental_e2e.py` live          |
| **S-LIVE-BIS**           | 仓内 ops；**借鉴 L2** bis 窗参数改造                                                                                                                                  | live clean 绿；禁止 import `BisProvider`                                                            | **2a 试点绿**             | `test_bis_incremental_e2e.py` live                  |
| **S-LIVE-WORLDBANK**     | 仓内 ops live                                                                                                                                                         | live clean 绿；**L3**；SDD World Bank API                                                           | **2a 试点绿**             | `test_world_bank_incremental_e2e.py` live           |
| **S-LIVE-CFTC**          | 仓内 ops live 周频                                                                                                                                                    | live clean 绿；**L3**                                                                               | **2a 试点绿**             | `test_cftc_incremental_e2e.py` live                 |
| **S-LIVE-SEC-EDGAR**     | 仓内 port live                                                                                                                                                        | `us_disclosure_clean` 绿；**L3**；SDD SEC EDGAR                                                     | **2a 试点绿**             | `test_sec_edgar_incremental_e2e.py` live            |
| **S-LIVE-ALPHA-VANTAGE** | 仓内 port live                                                                                                                                                        | `security_bar_1d` 绿；**L3**；`ALPHA_VANTAGE_API_KEY`                                               | **2a 试点绿**             | `test_alpha_vantage_incremental_e2e.py` live        |
| **S-LIVE-DERIBIT**       | 仓内 port live                                                                                                                                                        | `crypto_derivative_clean` 绿；**L3**                                                                | **2a 试点绿**             | `test_deribit_incremental_e2e.py` live              |
| **S-LIVE-CNINFO**        | 仓内 port live                                                                                                                                                        | `cn_announcement_clean` 绿；**L3**                                                                  | **2a 试点绿**             | `test_cninfo_incremental_e2e.py` live               |
| **S-LIVE-MOOTDX**        | 仓内 port live                                                                                                                                                        | `security_bar_1d` 绿；**L3**（非 R3FR 借鉴梯）                                                      | **2a 试点绿**             | `test_mootdx_incremental_e2e.py` live               |
| **S-MERGE**              | registry 三件套；`test_catalog.yaml`                                                                                                                                  | coordinator merge；`loop_maintain` 绿                                                               | 全部 S-LIVE-\* 绿         | registry 测                                         |
| **S-ACCEPT**             | `tier_a_live_acceptance.py` 11/11                                                                                                                                     | 每源 sync→clean→**`DbInspector.inspect()` (E2)** PASS/WARN；exit 0；零主库；F0 全 profile → nightly | S-MERGE                   | 脚本 + `research/l4-tier-a-live-accept-evidence.md` |

---

## 每源 live AC 细项（统一）

| #   | 验证点                                                                                                        |
| --- | ------------------------------------------------------------------------------------------------------------- |
| 1   | `QMD_ALLOW_LIVE_FETCH=1` 且 `DATA_ROOT` 指向隔离路径                                                          |
| 2   | `qmd data sync --source-id <id>`（或等价 ops runner）`status=COMPLETED`                                       |
| 3   | clean 表行数 ≥ 1（域依 ADR-028）                                                                              |
| 4   | 重复跑一次 row count 稳定（幂等）                                                                             |
| 5   | `DbInspector.inspect()`（E2）对该源 PASS/WARN；F0 全 `qmd data health` profile → nightly（见 `plan-spec.md`） |
| 6   | 无 EasyXT 式 silent fallback（S00 负向测覆盖）                                                                |
| 7   | 借鉴：L2 须有改造清单证据；L3 须 SDD URL；仓内组件标「直接复用」                                              |

---

## 并行 worktree 建议

| Worktree         | Slices                                   | 拥有文件                           |
| ---------------- | ---------------------------------------- | ---------------------------------- |
| wt-mdata03-infra | S00-ELIGIBILITY, S00-INFRA               | harness, acceptance 脚本, conftest |
| wt-mdata03-pilot | S-LIVE-FRED, S-LIVE-BAOSTOCK             | fred/baostock port + tests         |
| wt-mdata03-macro | S-LIVE-US-TREASURY, BIS, WORLDBANK, CFTC | macro ops + tests                  |
| wt-mdata03-us    | S-LIVE-SEC-EDGAR, ALPHA-VANTAGE, DERIBIT | us/crypto ops + tests              |
| wt-mdata03-cn    | S-LIVE-CNINFO, MOOTDX                    | cn ops + tests                     |

**合并顺序：** S00 → 2a → 2b∥2c → S-MERGE → S-ACCEPT（主会话）

**峰值 execute agent：3–4**（见 `parallel-dispatch-protocol.md`）

---

## Out of scope

- 新 migration · G1/G2/G4/G5 · Round4 · 主库 promote · 24 源矩阵
