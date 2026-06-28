# R3H-01 参考项目采纳追溯（CLOSED @ 2026-06-28）

> **权威规则：** `specs/contracts/reference_adoption_guardrails.yaml` · 活卡 `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` §14  
> **Trellis 归档：** `.trellis/tasks/archive/2026-06/06-28-round3h-r3h01-official-macro/`（A3 0 runtime import · A5 audit PASS · `execute-evidence/9.8-full*.txt`）  
> **R3H-05：** 交叉项 **REF-ADOPT-GATE** 须引用本文 + R3H-03/04 同名文件。

## 1. 批次级结论

| 项                            | 结论                                                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| runtime `参考项目/**` import  | **PASS** — `backend/` 0 命中；`test_reference_adoption_guardrails.py` 绿                        |
| OpenBB FRED provider 源码拷贝 | **禁止** — architecture_only（活卡 §14、Grill-me Q12）                                          |
| 双份 fetch 实现               | **CLOSED** — `fred` L2 迁入 `fetch_ports/fred_port.py`；`ops/fred_fetch_ports` 仅 orchestration |

## 2. 六源采纳矩阵

| source_id     | adoption_ladder         | 参考路径（只读/归档）                                             | QMD 落点                                                     | direct_copy | 说明                                          |
| ------------- | ----------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------ | ----------- | --------------------------------------------- |
| `fred`        | **L2** copy_and_rewrite | `ops/fred_fetch_ports.py`；OpenBB `providers/fred/` **架构 only** | `fetch_ports/fred_port.py` · `normalizers/official_macro.py` | false       | MIT/urllib 保留；无 AGPL runtime              |
| `us_treasury` | **L3** greenfield       | 无 1:1 参考文件；OpenBB provider **目录布局** only                | `fetch_ports/us_treasury_port.py`                            | false       | mock-first；证据 `official_macro_evidence_v1` |
| `sec_edgar`   | **L3** greenfield       | 无 1:1；SEC fair-access 约束自研                                  | `fetch_ports/sec_edgar_port.py`                              | false       | live 需 `SEC_EDGAR_USER_AGENT`；默认 mock     |
| `cftc_cot`    | **L3** greenfield       | 无 1:1                                                            | `fetch_ports/cftc_cot_port.py`                               | false       | mock-first                                    |
| `bis`         | **L3** greenfield       | 无 1:1                                                            | `fetch_ports/bis_port.py`                                    | false       | mock-first                                    |
| `world_bank`  | **L3** greenfield       | 无 1:1                                                            | `fetch_ports/world_bank_port.py`                             | false       | mock-first                                    |

**标签纠正（2026-06-28 文档债闭合）：** 除 `fred` 外五源 port 文件头原标「L2」过宽；已改为 **L3** + 统一证据 normalizer（非外部文件拷改）。

## 3. 延后 / 不在本卡重做

| 项                              | 处置                                            | 登记位置                                   |
| ------------------------------- | ----------------------------------------------- | ------------------------------------------ |
| 五源 mock-first **live 产品化** | **延后** → R3H-05 **MACRO-LIVE-DEFER**          | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 |
| G3/G4 clean DDL                 | **延后** → R3H-05 **SCHEMA-G3G4**               | 同上                                       |
| baostock pilot DH sidecar       | **非本卡 scope** → R3H-05 **G14-PILOT-SIDECAR** | 路线图 §5.0                                |

## 4. R3H-05 审计引用

- 矩阵行：六源 `final_decision` + 上表 ladder 一致
- `test_reference_adoption_guardrails.py` 全绿
- 无 port 标 L2 却无 `reference_project.path`（本文件 + 活卡 §14 为 SSOT）
