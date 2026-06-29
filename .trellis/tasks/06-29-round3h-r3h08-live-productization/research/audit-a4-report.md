# R3H-08 A4 审计结果（安全 · env gate）

> **维度：** A4 — 安全 · env gate  
> **任务：** `06-29-round3h-r3h08-live-productization`  
> **协议：** `plan_protocol_version: 4.1`  
> **模板：** `agents/security-auditor.md`  
> **日期：** 2026-06-30

---

## 维度证据（§3 · env gate 静态审查）

### Checklist（摘要）

| 检查项                                       | 结论     |
| -------------------------------------------- | -------- |
| `QMD_ALLOW_LIVE_FETCH` 默认 fail-closed      | **PASS** |
| `create_product_live_fetch_port` 全切片 gate | **PASS** |
| Tier B 拒 canonical main DB                  | **PASS** |
| Tier C 不写 clean bar                        | **PASS** |
| `live_fetch` 函数 `dry_run=True` 默认        | **PASS** |
| `live_fetch` CLI 子命令注册                  | **FAIL** |
| `live_fetch` ResourceGuard fail-closed       | **FAIL** |
| `live_fetch` `route_status==READY`           | **FAIL** |
| per-port 直连 `use_mock=False` 绕过 gate     | **FAIL** |
| diff 内明文密钥                              | **PASS** |

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 共 **7** 行非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                              | 锚点                                                    | 根因                                       | 修复方案                                                | 验证                                      |
| -------- | --- | --------------------------------- | ------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------- | ----------------------------------------- |
| A4-P1-01 | P1  | `qmd data live-fetch` 未接入 CLI  | `backend/app/cli/main.py` vs `data_commands.py:107-167` | S08-05 仅实现 Python 函数，未注册 argparse | 增加 `live-fetch` 子命令 + `_run_data` 分支             | subprocess CLI 测 exit 0 + `dry_run:true` |
| A4-P1-02 | P1  | `live_fetch` 不强制 ResourceGuard | `data_commands.py:135-163`                              | guard 结果只写入 payload                   | `dry_run=False` 前 guard PAUSE/HARD_STOP → `CliFailure` | monkeypatch guard→HARD_STOP 须拒绝        |
| A4-P1-03 | P1  | `live_fetch` 未校验 READY         | `data_commands.py:134-163`                              | 架构 §3.4 preview→READY 未实现             | `dry_run=False` 前要求 `route_status==READY`            | route 非 READY 时拒绝                     |

---

## 计划外发现

| ID       | P   | 标题                                        | 锚点                                              | 根因                         | 修复方案                                               | 验证                                                      |
| -------- | --- | ------------------------------------------- | ------------------------------------------------- | ---------------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| A4-P1-04 | P1  | fetch_port 工厂可绕过 `ProductLiveGate`     | `fred_port.py:174-185` 等 22 源                   | Gate 仅在 product live 工厂  | 各 `*LiveFetchPort` 入口 `assert_product_live_allowed` | 无 env 时 `create_fred_fetch_port(use_mock=False)` 须拒绝 |
| A4-P2-01 | P2  | `live_fetch` 绕过 `DataSourceService.fetch` | `data_commands.py:152-163`                        | 直调 `port.fetch_payload`    | 改经 `build_product_live_service(...).fetch`           | service 金路径一致                                        |
| A4-P2-02 | P2  | `live_fetch` 负向安全测缺口                 | `tests/test_r3h08_live_productization.py:541-558` | 仅测 dry_run=True 且已设 env | 补无 env/guard/READY 负向                              | pytest -k liveFetch 全绿                                  |
| A4-P2-03 | P2  | Tier C smoke 路径可无产品 env 触网          | `kalshi_port.py:113-118`                          | `KALSHI_LIVE_SMOKE` fallback | 文档化双轨或 smoke 与 product 隔离                     | 无 env 时 product 路径拒绝                                |

Repair 优先序建议：**A4-P1-04** → **A4-P1-02/03** → **A4-P1-01**。
