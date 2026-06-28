# Batch 3H Coordinator Playbook

## 1. Merge order

1. ~~Freeze registry/capability baseline and schema enum checks.~~ **Done** @ R3H-01 boot.
2. ~~Run R3H-01 through R3H-04 in parallel branches.~~ **CLOSED** @ 2026-06-28（双轨 P6 已 merge `master`）。
3. ~~Merge shared registry/capability/route/test catalog changes through coordinator review.~~ **Done** @ P6（四文件冲突已协调合并）。
4. **Run R3H-05** as final audit and Round4 admission gate — **当前入口**；开放项见 `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1。

## 2. Parallel ownership

- R3H-01 owns all official macro/disclosure sources: `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`.
- R3H-02 owns all market/crypto sources: `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`.
- R3H-03 owns all CN market/validation/authorized sources: `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare`.
- R3H-04 owns all probability/evidence/manual-review sources: `kalshi`, `polymarket`, `web_search`.
- R3H-05 owns final cross-layer audit only; it must not implement missing adapters.

## 3. Shared-file conflict handling

Any branch changing shared registry or contract files must list every source it owns with:

```text
source_id
domain
operation
old route status
new route status
final source decision: READY_WITH_EVIDENCE or ADR_DISABLED_OUT_OF_SCOPE
auth/license decision
ResourceGuard cap
replay fixture path
test command
Layer binding, if any
```

Coordinator must reject changes that:

- mark READY without evidence;
- leave a source in vague proposed-disabled status without ADR;
- close a task while one of its owned sources lacks final decision;
- move Round4 forward while R3H-05 is BLOCK.

## 4. Round4 admission

Round4 can start only after R3H-05 says one of:

- `PASS_ROUND4_REAL_DATA_READY`
- `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR`
- `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE`

A WARN must include the ADR that narrows which sources/layers/domains are considered production-entry complete. A WARN cannot silently defer source implementation.
