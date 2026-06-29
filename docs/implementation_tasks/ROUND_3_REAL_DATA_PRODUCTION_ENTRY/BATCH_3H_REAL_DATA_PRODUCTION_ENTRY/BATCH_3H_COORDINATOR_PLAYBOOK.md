# Batch 3H Coordinator Playbook

> **模块轨 SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · `R3H_PASS_EXECUTION_PLAN.md`  
> **当前下一入口（写死）：** **`R3H-10` → `R3H-07` 串行** — `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`

---

## 1. Merge order（历史 + 活轨）

### 1.1 已完成

1. R3H-01～04 并行分支 — **CLOSED** @ 2026-06-28。
2. Registry 三件套 coordinator merge — **Done** @ P6。
3. R3H-06 clean schema — **CLOSED** @ 2026-06-29。
4. Batch 3V — **CLOSED** @ 2026-06-28。

### 1.2 活轨（PASS Wave 1–5）

```text
Wave 1  R3H-10 merge → R3H-07 merge（串行，禁止 10∥07 同会话抢文件）
Wave 2  R3H-08 建议 merge：08C → 08A → 08B → 08D（单 agent）
Wave 3–4  R3-DCP 按 INDEX；G12 五轴同一 Wave 4 关账
Wave 5  R3H-05A..E 并行 merge → R3H-05-GATE 最后
```

**R3H-05 不是当前 merge 入口** — 仅 Wave 5。

---

## 2. Parallel ownership（历史 CLOSED + 活轨）

### 2.1 R3H-01～04（CLOSED — 勿再开工）

- R3H-01：宏观六源
- R3H-02：市场五源（CAL-US → R3H-07）
- R3H-03：CN 十源
- R3H-04：预测/网页证据

### 2.2 Wave 1（活轨 · 串行）

| 轨         | 拥有                                | Module | 阻塞              |
| ---------- | ----------------------------------- | ------ | ----------------- |
| **R3H-10** | DataSourceService SSOT；消除 bypass | C2, E4 | 无（**先执行**）  |
| **R3H-07** | US TradingCalendar L2               | G4, C3 | **R3H-10 CLOSED** |

### 2.3 Wave 2（活轨）

| 轨      | 拥有                  |
| ------- | --------------------- |
| R3H-08A | CN primary → Tier A   |
| R3H-08B | validation → Tier B   |
| R3H-08C | macro + fred → Tier A |
| R3H-08D | kalshi/poly → Tier C  |

### 2.4 Wave 5

- R3H-05：审计 **only** — 不得实现缺失 adapter。

---

## 3. Shared-file conflict handling

（同前 — coordinator 拒绝 READY 无 evidence、vague proposed-disabled、R3H-05 BLOCK 时推进 Round4。）

任何改动 shared registry 的分支须列出：

```text
source_id · domain · operation · old/new route · final decision
auth/license · ResourceGuard cap · replay path · test command · Layer binding
```

---

## 4. Round4 admission

Round4 **仅**在 `R3H-05-GATE` = **`PASS_ROUND4_REAL_DATA_READY`** 后启动（项目主路径，非 WARN）。

PASS 前硬门禁包括：**G12 五轴 pytest 全绿**（`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1）。

---

## 5. PASS 波次协调（模块轨）

| Wave | 协调要点                                                                    |
| ---- | --------------------------------------------------------------------------- |
| 1    | **串行** 10→07；`/to-issues` 见 `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md` |
| 2    | 四轨勿改 migration；registry 主会话批 merge                                 |
| 3–4  | R3-DCP debt-lite slice plan（Phase 8D）；五轴在 Wave 4 一次关账             |
| 5    | 05A–E 可并行；GATE 必须全量 pytest + 五轴清单                               |

**主会话维护：** 每 Wave Done 更新 `R3H_PASS_EXECUTION_PLAN.md` §3.1 状态表。

---

## 6. 禁止事项

- Wave 1 内默认 **禁止** R3H-07 与 R3H-10 并行。
- 禁止在 R3H-10 未 CLOSED 时开工 R3H-08（live 会重复修入口）。
- 禁止用 R3H-05 审计卡代替 Wave 1–4 实现。
- 禁止 pilot merge 主库。
