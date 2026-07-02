# Plan Doubt Review — R3-DCP-06

> doubt-driven-development · Plan 5c

## 质疑 1：五轴都要 live 真网吗？

**攻击：** §3.5.1 写「Tier A clean」，是否必须 `QMD_ALLOW_LIVE_FETCH`？

**辩护：** DCP-05 已证明 incremental **写** clean；DCP-06 证明 **读** clean + 算轴。replay 种子写入 tmp_path 隔离库即满足「非 staged_fixture_only」，与 DCP-05 e2e 同政策。live 可选 smoke，非关账必须。

**裁决：** ACCEPT — replay clean e2e 为 PASS 证据；live 不挡关账。

---

## 质疑 2：流动性轴 spec 是 tiingo，Tier A 无 tiingo

**攻击：** 五轴之一无法真 clean，PASS 造假。

**辩护：** ADR-029 ponytail：用 `alpha_vantage` → `security_bar_1d` 算 Amihud proxy；spec primary 差异文档化 + 升级路径 tiingo port。§3.5.1 要求「每轴可断言 pytest 绿」，非「每 YAML primary 源就绪」。

**裁决：** ACCEPT with ponytail — S04 必须 ADR 注释 + 测；tiingo 全路径阶段外置 Batch 6+。

---

## 质疑 3：改 ingestion 桥会破坏 Batch 2.5？

**攻击：** `Layer1ObservationIngestionService` 是 staged 入口，改它回归风险高。

**辩护：** GitNexus impact LOW；**新 reader 并行**，默认 staged 路径不动。Doubt 要求 S00 新文件而非重写 commit 事务。

**裁决：** ACCEPT — 禁止替换 staged 默认；仅增 clean 读 API。

---

## 质疑 4：ACC-LAYER-E2E-LIVE-001 能否在 DCP-06 全关？

**攻击：** 台账要求 L1–L5 全链。

**辩护：** 路线图 §3.5.2 明确 DCP-06 只承接 L1/五轴；终态审计 Wave 5 GATE。Repair 必须 **阶段外置** L3–L5，禁止假全关。

**裁决：** ACCEPT — S06 登记阶段外置 + §1 部分关账证据。

---

## 质疑 5：参考项目对 Layer1 有无 L1 可复制代码？

**攻击：** 没参考是否瞎写？

**辩护：** 实读 OpenBB/digital-oracle/EasyXT；Layer1 引擎已仓内成熟。参考贡献为 **L2 概念 + L3 行为对齐 + forbidden 负向**，非拷贝五轴实现。

**裁决：** ACCEPT — `reference-adoption-dcp06.md` 已落盘。

## 残留风险（Execute 验证）

- COT observation 行映射复杂度（S05）
- K1 readiness 与 coordinator merge 时序（S06）
