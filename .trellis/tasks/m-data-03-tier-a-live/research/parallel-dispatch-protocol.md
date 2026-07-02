# M-DATA-03 并行 Execute Agent 派发协议

> **模型：** composer-2.5  
> **铁律：** 与主会话 Execute 一致 + 参考项目 RED 前实读

---

## 1. 编制

| 角色              | 数  | 串/并                      |
| ----------------- | --- | -------------------------- |
| Infra agent       | 1   | 串行 S00                   |
| Pilot agent       | 1–2 | 并行 2a（fred ∥ baostock） |
| Macro agent       | 1–2 | 并行 2b（4–5 宏观源）      |
| US/CN agent       | 1–2 | 并行 2b/2c                 |
| Merge coordinator | 1   | 串行 S-MERGE + S-ACCEPT    |

**峰值 execute agent：3–4**（禁止 11 源 11 agent）

---

## 2. Boot（每 agent）

| #   | 动作                                                    |
| --- | ------------------------------------------------------- |
| 0a  | `agent-toolchain.md` · trellis-execute · project-global |
| 0b  | `00-EXECUTION-ENTRY.md` · 本 agent 切片 · ADR-034       |
| 0c  | `EXTERNAL-INDEX.md` §A + `implement.jsonl`              |
| 0d  | `reference-adoption-m-data-03.md` §2 对应源             |
| 0e  | GitNexus `impact()` 本切片符号                          |
| 0f  | `validate-execute-boot`（Execute 阶段）                 |

---

## 3. 参考实读（RED 前）

> **等级 SSOT：** `reference-adoption-m-data-03.md` §0。仓内代码 **不** 走本表。

| Agent   | 切片              | 借鉴等级           | 追加实读                                                                             |
| ------- | ----------------- | ------------------ | ------------------------------------------------------------------------------------ |
| Infra   | S00               | L3 + forbidden     | OpenBB fetcher L36–85（概念）· EasyXT unified_data_interface **forbidden** · ADR-034 |
| Pilot-A | FRED              | **L3**             | OpenBB fred 目录（architecture）· SDD FRED API                                       |
| Pilot-B | BAOSTOCK          | **L3** + forbidden | EasyXT auto_data_updater L149–178（**概念 only**）· unified_data_interface forbidden |
| Macro   | BIS               | **L2**             | digital-oracle bis.py L54–66 + **§2.2 改造清单**                                     |
| Macro   | US_TREASURY..CFTC | **L3**             | SDD §E 对应 API                                                                      |
| Market  | SEC..MOOTDX       | **L3**             | SDD §E · 仓内 port（**直接复用** ops 签名）                                          |

**L2 Execute 必交：** 「借鉴点 vs 改造点」对照；**禁止** `from digital_oracle` / 粘贴 `BisProvider`。

落盘：`research/execute-reference-read-evidence-<branch>.md`（Execute 阶段）

---

## 4. Worktree 方案

| Worktree                                  | Branch                     | 切片                              | 禁止拥有           |
| ----------------------------------------- | -------------------------- | --------------------------------- | ------------------ |
| `../quant-monitor-desk-wt-mdata03-infra`  | `feature/m-data-03-infra`  | S00                               | —                  |
| `../quant-monitor-desk-wt-mdata03-pilot`  | `feature/m-data-03-pilot`  | FRED, BAOSTOCK                    | harness 核心       |
| `../quant-monitor-desk-wt-mdata03-macro`  | `feature/m-data-03-macro`  | US_TREASURY, BIS, WORLDBANK, CFTC | registry · harness |
| `../quant-monitor-desk-wt-mdata03-market` | `feature/m-data-03-market` | SEC, AV, DERIBIT, CNINFO, MOOTDX  | registry · harness |

**Base：** `feature/m-data-03-tier-a-live`（S00 merge 后开并行）

**合并顺序：** infra → pilot 绿 → macro ∥ market → coordinator S-MERGE → S-ACCEPT

---

## 5. 禁止并发编辑

- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `tests/test_catalog.yaml`
- `scripts/tier_a_live_acceptance.py`（S00-INFRA 独占，后只 coordinator 扩源列表）

---

## 6. Agent 收尾

```bash
uv run pytest tests/test_<slice>_*.py -q
# live 时：
export QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03
uv run pytest tests/test_<slice>_*.py -m network -q
```

回报：文件列表 · 参考实读路径 · pytest 输出 · blocker
