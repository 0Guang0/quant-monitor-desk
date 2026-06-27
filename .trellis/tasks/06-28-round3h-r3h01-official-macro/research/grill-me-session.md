# Grill Session — R3H-01（Plan Phase 3）

> Skill: `grill-me`（按 R3G-03 归档格式）· 2026-06-28

## 质问与回答

**Q1：3G mass rehearsal 跑过，是否等于 fred 已 `READY_WITH_EVIDENCE`？**  
A：**否**。预演仅证明 pilot 库 + `live_evidence_bridge` 可接线；G10/G14 明确 **R3E 链与 promote 链未产品级合一**。R3H-01 须独立登记终态。

**Q2：R3H-01 能否写 `quant_monitor.duckdb`？**  
A：**否**。本卡无 Batch 3H 主库 gate/ADR；允许 sandbox/replay/`.audit-sandbox` 证据与 capped pilot 复测，**禁止**默认 merge 预演数据进主库（路线图 §5.0）。

**Q3：`live_evidence_bridge` 保留还是删？**  
A：**产品化后废弃 pilot 语义**。§9.1 抽出共享 normalizer；`r3g03_isolated_pilot_dry_run.py --live-wire` 可暂调 normalizer，但 **不得**再依赖 `_write_sandbox_rehearsal_gate_sidecars` 伪造 DH 门禁。DH 须由真实 data-health profile 或 replay fixture 满足。

**Q4：FRED 证据 canonical schema 以谁为准？**  
A：**以 `source_capabilities.yaml` fred.macro_series.fields 为准**（`observation_date` 非 `date`）。对外文件形态：`fred_evidence.json` 升级为 **多 series bundle**（`schema_version` + `series[]` 各含 `observations[]`），`rehearsal_loader` 与 `live_pilot_phase3` **同一 writer/reader**。

**Q5：已有 `backend/app/ops/fred_fetch_ports.py` 与活卡 §4 `datasources/fetch_ports/fred_port.py` 冲突？**  
A：**L2 拷改**：§9.2 将 fetch 边界 **迁入** `datasources/fetch_ports/fred_port.py`（或 thin re-export + deprecation 注释）；`ops/` 只留 orchestration CLI。禁止双份 live/mock 实现长期并存。

**Q6：六源都要真网 live fetch 吗？**  
A：**否**。`READY_WITH_EVIDENCE` = adapter + gate + route + **replay fixture** + evidence 字段；真网 live 仅 **fred**（用户授权 + `FRED_API_KEY`）为 P0；其余源可先 replay/sandbox capped entry，真网为加分项非阻塞，但 route READY 负例必须存在。

**Q7：若工期紧，能否只交付 fred，其余留 proposed-disabled？**  
A：**否**（Batch 3H hardening）。每源终态只能是 `READY_WITH_EVIDENCE` 或 **`ADR_DISABLED_OUT_OF_SCOPE`（书面 ADR + registry/route/release limitation）**，不得含糊 defer。

**Q8：哪些源适合 ADR 收窄？**  
A：Plan 默认 **全六源实现**；若 Execute 受阻，**仅**在 grill 已确认无 P0 Layer 依赖时可 ADR：`world_bank`（超低频）、`bis`（多 endpoint 复杂）优先候选；`fred`/`us_treasury`/`sec_edgar` **禁止 ADR**（官方宏观/披露主承诺）；`cftc_cot` 次优先实现（单 CSV 形态）。

**Q9：R3H-01 要做到什么程度的 Layer1/Layer5 binding？**  
A：**声明路径 smoke**，非 R3H-05 全层审计。§9.7：macro evidence 可流入 `layer1_axes/ingestion_evidence` 或 Layer5 factual_source 的最小契约测试；**禁止**提前做 R3H-05 cross-layer PASS。

**Q10：`B2.5-O-05` fred live primary 本卡关闭吗？**  
A：**部分**。R3H-01 可登记 fred 为 **capped production-entry candidate**（`R5_LIMITED_PRODUCTION_ENTRY`），但 **默认仍 disabled-by-default**；关闭 primary defer 须 registry + route + 用户授权三门齐，写进 §9.2 验收，不口头宣称 production-live。

**Q11：共享 registry/capability 谁改？**  
A：**Coordinator 审查**（`BATCH_3H_COORDINATOR_PLAYBOOK.md` §3）。R3H-01 分支 PR 须附六源 `old→new route status` 表；禁止未协调改 `R3H-02~04` 拥有的 source。

**Q12：OpenBB `参考项目/fred` 能拷吗？**  
A：**架构借鉴 only**；AGPL runtime 禁止。FRED HTTP 已存在于 `fred_fetch_ports.py`，迁 port 时 **保留 QMD urllib 实现**，不引入 OpenBB provider。

**Q13：与 R3G promote 链关系？**  
A：R3H-01 **不扩展** R3G-03 promote 范围；只 **统一 fred 证据** 使既有 `rehearsal_loader` 无需 bridge sidecar。promote 仍仅 pilot/approved DB。

**Q14：最小垂直切片顺序？**  
A：**G10 证据契约（9.1）→ fred port+route（9.2）→ 其余源并行块（9.3–9.5）→ registry 收口（9.6）→ Layer smoke（9.7）→ merge（9.8）**。

## 结论（Plan 锁定）

| 维度   | 决定                                 |
| ------ | ------------------------------------ |
| 范围   | 六源终态闭环；首步 G10/G14           |
| 主库   | 禁止写入                             |
| bridge | 废弃 sidecar；共享 normalizer        |
| fred   | 迁 `fred_port`；统一 evidence schema |
| Layer  | smoke only；R3H-05 不做              |
| ADR    | 仅作显式收窄，默认六源实现           |

**Phase 3 complete** · 可进入 Phase 3.5 `to-issues` / 5a 步骤定稿。
