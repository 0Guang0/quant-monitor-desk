# Tier A 逐源成品核实（11 源 · 关账版）

> **目的：** 能不能用、入库是否符合成品形态、下轮开主库是否还需改管道  
> **SSOT：** `M-DATA-03-HANDOFF.md` §2.1 · §3.4.2  
> **关账报告：** `.audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report.json`  
> **G-07 加厚 run：** `.audit-sandbox/m-data-03/r2-thicken-wb-deribit-20260703224024/`（world_bank=2 · deribit=2 · 分报告 world_bank/deribit）  
> **状态：** **11/11 沙箱验收 PASS** · **0 源可宣称「仅等开主库」**（R4 sandbox scope）

---

## 汇总

| 源            | 能不能用？              | 抓到了吗？                                   | 下轮可开主库？                          | 状态                        |
| ------------- | ----------------------- | -------------------------------------------- | --------------------------------------- | --------------------------- |
| fred          | 沙箱可用                | COMPLETED · axis_observation=3 · F0/B2 PASS  | **否** — 须 R3G promote + 主库 posture  | ✅ 四问                     |
| us_treasury   | 沙箱可用                | axis_observation=3                           | **否**                                  | ✅                          |
| cftc_cot      | 沙箱可用                | axis_observation=3                           | **否**                                  | ✅                          |
| world_bank    | 沙箱可用                | axis_observation=**2**（US+CN）              | **否** — 须 R3G promote                 | ✅ G-07 加厚 **2026-07-03** |
| deribit       | 沙箱可用                | crypto_derivative_clean=**2**（双合约 live） | **否**                                  | ✅ G-07 加厚 **2026-07-03** |
| alpha_vantage | 沙箱可用                | security_bar_1d=3 · f0=PASS                  | **否** — 行情主库须独立 promote         | ✅                          |
| baostock      | 沙箱可用                | security_bar_1d=2 · f0=PASS                  | **否**                                  | ✅                          |
| mootdx        | 沙箱可用                | security_bar_1d=2 · f0=PASS                  | **否**                                  | ✅                          |
| bis           | 沙箱可用（修后）        | axis_observation=1+                          | **否**                                  | ✅ 见 investigation md      |
| cninfo        | 沙箱可用（replay 路径） | cn_announcement_clean=1                      | **否** — 真 SEC/cninfo live parser 后续 | ✅                          |
| sec_edgar     | 沙箱可用（replay 路径） | us_disclosure_clean=2                        | **有条件**                              | ✅                          |

**汇总结论：** 11 源在隔离沙箱内 pipeline 语义已核实；**全部**仍须主库 promote 与生产 posture，不得从本批直接写 canonical DB。

---

## 逐源四问（关账 run 证据）

### fred

| #   | 问题                     | 结论                                        |
| --- | ------------------------ | ------------------------------------------- |
| 1   | 是否可以用？             | 沙箱内 **是**                               |
| 2   | 抓过来了吗？             | raw 落盘 + axis_observation=3               |
| 3   | 入库形态符合成品？       | F0 `layer1_observation_p0` PASS · B2 PASSED |
| 4   | 下轮开主库还需改管道吗？ | **要** — promote gate，非本票范围           |

### us_treasury / cftc_cot

同宏观族：COMPLETED · axis_observation=3 · F0/B2 PASS · 主库前须 promote。

### world_bank

| #   | 结论                                                                      |
| --- | ------------------------------------------------------------------------- |
| 1–3 | 可用 · **2 行** clean（`US`+`CN` 双国家窗）· F0/B2 PASS                   |
| 4   | 主库前须 promote（G-07 加厚 run：`r2-thicken-wb-deribit-20260703224024`） |

### deribit

| #   | 结论                                                                                     |
| --- | ---------------------------------------------------------------------------------------- |
| 1–3 | 可用 · **2 行** `crypto_derivative_clean`（live `_live_instruments` 双合约）· F0/B2 PASS |
| 4   | 主库前须 promote（同上加厚 run `r2-thicken-wb-deribit-20260703224024`）                  |

### alpha_vantage / baostock / mootdx

| #   | 结论                                              |
| --- | ------------------------------------------------- |
| 1–3 | K 线入库 · `f0=PASS`（无 staged-only）· B2 PASSED |
| 4   | 主库前须 R3G/limited production entry             |

### bis

根因：月频窗比较 · 修后 axis_observation≥1 · 见 `tier-a-empty-response-investigation.md`。

### cninfo / sec_edgar

根因：冷启动窗 · `cold_start_fallback` · replay 路径可证管道；真网 parser 完整化为后续 slice。

---

**证据路径：** `.audit-sandbox/m-data-03/r2-live-20260703220000/` · 幂等 run2 同目录 `tier-a-report-run2.json`
