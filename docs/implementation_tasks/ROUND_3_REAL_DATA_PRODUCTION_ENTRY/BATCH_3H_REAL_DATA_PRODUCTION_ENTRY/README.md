# Batch 3H — Real Data Production Entry

> **Batch:** Round 3H Real Data Production Entry  
> **Purpose:** 在进入 Round4 产品化之前，把 Round3 的五层模型、真实数据接入和数据治理闭合到完整的有限生产接入级别。  
> **Execution rule:** 本批次可以按数据域/能力域并行，但不是“选几个源试一下”。凡是已经进入 `source_registry.yaml` / `source_capabilities.yaml` 的目标 source，都必须在本批次得到明确闭环：要么完成 adapter + gate + replay + route + evidence，要么用 ADR 明确说明为什么不属于当前产品承诺范围。

---

## 1. 为什么必须有 Batch 3H

当前 registry 已新增很多 proposed-disabled source。如果直接进入 Round4，API/前端/Agent 只能展示“尚未接入”的 source readiness，而不能基于真实生产数据工作。

Round3 的目标不是停在 proposed-disabled，也不是只做 baostock/cninfo/FRED 小样本 clean-write 彩排。Round3 必须把五层模型、真实数据接入、数据治理做到可以支撑产品化的完整生产接入基础。

所以 Batch 3H 的规则是：**全部目标 source 必须闭环，不允许只完成一组 adapter。**

对每个 source，闭环只能是以下两种之一：

1. **实现完成：** adapter/fetch port、auth/license gate、ResourceGuard、SourceRoutePlan、route tests、replay fixture/sandbox sample、fetch_log/content_hash/schema_hash/source_fetch_id、data health/source conflict/Layer evidence 都具备。
2. **范围收窄：** 有 ADR 明确说明该 source 不属于当前 Round3 产品承诺范围，且 registry/route/release manifest 都保持 `DISABLED_SOURCE` / not-ready，不得假装完成。

---

## 2. Batch 3H 必须覆盖的 source

### 2.1 既有 source 也必须收口

```text
qmt_xtdata
baostock
akshare
cninfo
yahoo_finance
tdx_pytdx
fred
qmt_xqshare
```

这些不能因为早期已有 skeleton/staged/probe 就跳过。Batch 3H 必须明确它们是 production-entry READY、validation-only READY、authorized-disabled，还是 ADR 排除。

### 2.2 新增 proposed-disabled source 必须全部处理

```text
us_treasury
sec_edgar
cftc_cot
bis
world_bank
deribit
coingecko
kalshi
polymarket
stooq
alpha_vantage
mootdx
eastmoney
sina_finance
ths_ifind
web_search
```

它们不能继续只停留在 proposed-disabled 文档层。每个 source 都必须有具体 adapter/gate/replay/route/evidence 结论，或 ADR 收窄范围。

---

## 3. Task cards

| Task ID  | Active card                                          | Required source coverage                                                                                                      | Parallel rule                                                                     |
| -------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `R3H-01` | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`       | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | 可独立分支；只拥有官方低频/披露 adapter 与 Layer1/Layer5 low-frequency binding    |
| `R3H-02` | `R3H_02_MARKET_DATA_ADAPTERS.md`                     | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | 可独立分支；只拥有跨资产/美股/ETF/期权/加密行情 adapter 与 route tests            |
| `R3H-03` | `R3H_03_CN_MARKET_ADAPTERS.md`                       | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | 可独立分支；必须明确 Primary/Validation/authorized-disabled，不得 silent fallback |
| `R3H-04` | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`     | `kalshi`, `polymarket`, `web_search`                                                                                          | 可独立分支；输出只能是 probability/evidence/manual_review，不得 clean-write 主值  |
| `R3H-05` | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | 汇总所有 source 与 Layer1–5 真实数据绑定                                                                                      | 必须最后；不得替前四张卡补实现，只做验收、阻断或 ADR 收窄                         |

---

## 4. Batch-level gates

Batch 3H 不算完成，除非：

- registry/capability 中每个目标 source 都有 adapter/gate/replay/route/evidence 结论。
- 每个被启用或可调度的 source 都有 READY route 和 negative route test。
- 每个不能启用的 source 都有明确 DISABLED route reason、auth/license/ADR 说明和 release limitation。
- 五层模型至少覆盖声明范围内的真实数据/evidence 路径，不再只靠 staged fixture。
- DataSourceService / SourceRoutePlanner / provider ports 不再只是 facade/skeleton。
- Clean-write 入口只允许 capped production entry，不允许全市场/全历史/分钟线默认。
- Round4 只能在 R3H-05 PASS 或 ADR 收窄 Round3 生产接入承诺后启动。

---

## 5. Forbidden scope

- 不做全市场。
- 不做全历史。
- 不默认分钟线/期权链全量。
- 不默认启用 QMT/TDX/Yahoo/商业终端。
- 不把 prediction market 当事实结果源。
- 不让 `web_search` 写 clean table。
- 不复制 `参考项目/**` runtime source。
- 不把 adapter 启用拆成“只加一个字段/只加一个 registry note”的新微批次。
