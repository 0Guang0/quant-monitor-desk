# Project Overview — B-19 staged pilot v2

**任务：** 在 PROMPT_14 v1 基础上，受控扩样 baostock/cninfo/akshare validation，产出 v2 证据链（route、validation、conflict、no-mutation、closeout）。

**边界：** staged-only / sandbox-first；`R3-B2.75-REQ2-EM` DEFERRED；AUD-08 `WARN_ALLOW_WITH_CONTROLS`。

**核心文件：** `staged_pilot.py`、`mutation_proof.py`、`test_staged_pilot.py`。

**九垂直切片：** R3Y-SP2-01..09；β-1 `R3Y-MUT-PROOF-001` 归入 SP2-08。

**禁止：** production clean write、full market scan、TDX live、QMT、live FRED、production-live 声称。
