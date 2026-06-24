# Round 3 Wave B — 待修复清单（归档对账）

> **Authority:** Wave B（PROMPT_19 / 021 / fix α）合并与 Trellis 归档后的**残余开放项**台账。  
> **配对文档:** `docs/AUDIT_DEFERRED_REGISTRY.md` · `docs/UNRESOLVED_ISSUES_REGISTRY.md` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.4  
> **基准:** `master` @ `68b10982` · 2026-06-24  
> **规则:** 每项标明清理阶段、是否阻塞下一批次（PROMPT_20 / 022）、关闭测试/证据。

---

## 1. Wave B 已关闭（勿重复打开）

| ID / 切片                   | 问题                                          | 关闭证据                                                                                                                                             |
| --------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **α-1** `R3Y-SYNC-001`      | 生产 sync `adapter=` 旁路                     | merge `616feeb8` · `tests/test_sync_orchestrator.py::test_r3ySync001_*` · archived `fix-r3y-sync-adapter-guard`                                      |
| **α-2** registry SSOT       | R3Y 行 / wave-A RESOLVED / lineage defer 登记 | merge `984c7b28` · registry alignment tests · archived `fix-r3y-registry-lineage-defer`                                                              |
| **β-1** `R3Y-MUT-PROOF-001` | `mutation_proof` VERIFIED 语义过宽            | merge `e4abb372` · `backend/app/ops/mutation_proof.py` · `tests/test_staged_pilot.py` AC-MUT-001 · archived `06-24-round3-real-data-staged-pilot-v2` |
| **B-19** PROMPT_19          | staged real-data pilot v2 九切片证据          | merge `e4abb372` · Audit PASS · archived `06-24-round3-real-data-staged-pilot-v2`                                                                    |
| **B-21** `021`              | Layer3 日快照 + staged lineage envelope       | `1cdb7e48` on `master` · Audit PASS · archived `06-24-round3-021-layer3-snapshot`                                                                    |

---

## 2. 待偿还 — 不阻塞 PROMPT_20 / 022 主线（ hygiene / Batch 6）

| ID                      | 问题                                                   | 清理阶段             | 任务挂钩                                      | 阻塞什么                                 | 关闭条件                                                       |
| ----------------------- | ------------------------------------------------------ | -------------------- | --------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------- |
| `R3Y-STAGED-REG-001`    | `register_staged_file_registry_rows` 绕过 WriteManager | **β-2** after α-1    | `fix/r3y-staged-registry-privatize`           | 声称 staging 写路径已全面经 WriteManager | API 私有化或经 WriteManager；metadata-only 策略文档化 + pytest |
| `R3Y-PROMPT15-EVID-001` | PROMPT_15 closed-claim 缺 execute `*-green.txt` 映射   | **fix α-3**          | `fix/r3y-prompt15-evidence`                   | 声称 PROMPT_15 全量证据可审计            | 补 evidence 链 + checklist 映射；不得弱化测试目的              |
| `R3Y-TEST-DEPTH-001`    | closed-claim 反证测试深度不足                          | **Batch 6 hygiene**  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §Batch 6 | 不阻塞 staged-only 主线                  | per-ID runtime-strong pytest 或 explicit wont-fix ADR          |
| `R3-B6-021-O-01`        | Layer3 manifest 非 dict bar 元素静默跳过               | **Batch 6**          | `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md`   | 不阻塞 021 staged 闭环                   | schema fail-closed + pytest                                    |
| `R3-B6-021-O-02`        | 确定性重建测试仅断言部分字段                           | **Batch 6**          | 同上                                          | 不阻塞 021 staged 闭环                   | 全 row tuple 断言                                              |
| `ADV-R3X-LINEAGE-001`   | L3/L4 完整 snapshot lineage 持久化                     | **Batch 4B+ / 022+** | `021`+ · `022`                                | 不阻塞 PROMPT_20                         | snapshot lineage pytest + registry RESOLVED                    |
| `R3Y-LINEAGE-VR-001`    | Layer2 VR / fetch_log 绑定未闭合                       | **Batch 4B+**        | `021`+                                        | 不阻塞 PROMPT_20                         | sandbox 不得用合成 ID 冒充 VR binding                          |

---

## 3. 硬约束（仍 DEFERRED，任何批次不得误读）

| ID                           | 含义                                    | 规则                                              |
| ---------------------------- | --------------------------------------- | ------------------------------------------------- |
| `R3-B2.75-REQ2-EM`           | Eastmoney hist 真实路径不可达           | 不得作为 production-live / PROMPT_20 unblock 依据 |
| `R3-PROMPT14-AKSHARE-VAL-01` | akshare validation 网络失败             | PROMPT_19 可 retry；不得单独关闭 REQ2-EM          |
| staged-only 全局             | Batch 2.75 closeout `PILOT_FAIL_SOURCE` | 不得声称 production-live readiness                |

---

## 4. α-2 归档后 hygiene（NON-BLOCKING，可选下一小 PR）

| ID              | 问题                                                    | 建议                                                    |
| --------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| `WAVE-B-HYG-01` | 四份 SSOT `Last reconciled` 措辞曾不一致                | 已在本归档 reconcile 统一；后续改 registry 须四文件同句 |
| `WAVE-B-HYG-02` | `test_r3yRegistrySlice_alpha2LastReconciled` 仅子串匹配 | Batch 6：可增加 normalize 相等断言                      |
| `WAVE-B-HYG-03` | `QMD_SYNC_ALLOW_ADAPTER=1` 生产逃生口                   | 运维文档 + 部署检查；非代码阻塞                         |
