# Batch 3H — 参考项目采纳索引（追溯 SSOT）

> **规则：** `specs/contracts/reference_adoption_guardrails.yaml` · `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §0（L1/L2/L3）  
> **硬边界：** 禁止 runtime `import` / `sys.path` / 读 `参考项目/**`；OpenBB **architecture_only**（无 AGPL runtime）。

## 1. 四轨追溯文件

| 轨     | 状态   | 追溯文档                             | Trellis 归档                         |
| ------ | ------ | ------------------------------------ | ------------------------------------ |
| R3H-01 | CLOSED | `R3H_01_REFERENCE_ADOPTION_AUDIT.md` | `06-28-round3h-r3h01-official-macro` |
| R3H-02 | CLOSED | `R3H_02_REFERENCE_ADOPTION_AUDIT.md` | `06-28-round3h-r3h02-market-data`    |
| R3H-03 | CLOSED | `R3H_03_REFERENCE_ADOPTION_AUDIT.md` | `06-28-round3h-r3h03-cn-market`      |
| R3H-04 | CLOSED | `R3H_04_REFERENCE_ADOPTION_AUDIT.md` | `06-28-round3h-r3h04-prediction-web` |

活卡路径（仓库）：四轨追溯均已提升至 **Batch 活卡目录**（与 Trellis `research/reference-adoption-audit.md` 归档对照）。

## 2. R3H-05 必审交叉项

| ID                     | 主题                                                                                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REF-ADOPT-GATE**     | 四轨追溯文件存在；25 源 port 头注释 ladder 与矩阵一致；`test_reference_adoption_guardrails` 绿                                                            |
| **STAGED-PILOT-SSOT**  | 产品 fetch SSOT = `datasources/fetch_ports/*`；`ops/staged_pilot_fetch_ports` 双轨收敛 → **R3H-10 Wave 1**（S10-05 / S10-CLOSE）；rehearsal 边界见 S10-03 |
| **PILOT-OPS-CALENDAR** | `r3g03_isolated_pilot_dry_run.py` 等运维脚本可用自然日窗 — **非** 产品 adapter 承诺；R3H-05 limitation                                                    |

## 3. 延后 / 债务（不在 R3H-01～04 重做）

| ID                        | 内容                         | 负责阶段                                                                              |
| ------------------------- | ---------------------------- | ------------------------------------------------------------------------------------- |
| ~~**STAGED-PILOT-SSOT**~~ | ~~post-R3H-05~~              | **已前移至 R3H-10**（活卡 `R3H_10` · Trellis `research/reference-adoption-r3h10.md`） |
| **CAL-US**                | US equity 交易日历 EasyXT L2 | R3H-05 WARN+ADR 或后续 schema/calendar 切片                                           |
| **MACRO-LIVE-DEFER**      | 官方宏观五源 live            | R3H-05 limitation                                                                     |
| **PILOT-OPS-CALENDAR**    | pilot 脚本自然日             | 文档 limitation；不阻塞 Round4 若产品路径已登记                                       |

## 4. Batch 3G 摘要（已完成）

3G **不**直接 adapt 参考项目 runtime 代码；EasyXT/JQ2PTrade/OpenBB 思路消化为 QMD `sandbox_clean_write` + `data_health_profiles`（L2 精神重写）。见 `R3G_01` frozen §4、`test_reference_adoption_guardrails.py` r3g01/r3g03。
