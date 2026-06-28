# Original Plan Trace — R3H-03

> 活卡章节 → EXECUTION_INDEX §2 AC

| 活卡 § | AC ID | Step | 验证 |
| ------ | ----- | ---- | ---- |
| §1 Goal 十源闭环 | AC-TEN-SOURCES | 9.2–9.8 | §2 + §9.8 manifest |
| §5 per-source 8 项 | AC-PORT-GATE | 9.2–9.7 | frozen §5.1 十源表 |
| §6 Done 无 silent primary | AC-NO-SILENT-PRIMARY | 9.4, 9.6, 9.8 | route 负例 |
| §6 QMT 默认禁用 | AC-AUTH-DISABLED | 9.7 | `-k "ifind or qmt or xqshare"` unauthorized |
| §6 Layer3/4/5 | AC-LAYER-CN | 9.9 | `-k layer_cn` |
| §7 ResourceGuard | AC-CAPS | 9.1–9.7 | cap overflow 负例 |
| §14 EasyXT 参考 | AC-NO-REF-IMPORT | A3 audit | rg 禁止 import |
| §8 禁止 R3H-04 | AC-NO-R3H04-TOUCH | 9.8 | 禁止 kalshi/polymarket/web_search 行 |
| G11 baostock 产品化 | AC-G11 | 9.1, 9.2 | evidence + port |
| G16 cninfo/akshare | AC-G16 | 9.3, 9.4 | port + validation |
| BATCH_3H manifest | AC-BATCH-CLOSURE | 9.10 | 全库 pytest |

## 十源 per-source 追溯

| source_id | Step | AC | `-k` 锚点 |
| --------- | ---- | -- | --------- |
| baostock | 9.2 | AC-BAOSTOCK | baostock |
| cninfo | 9.3 | AC-CNINFO | cninfo |
| akshare | 9.4 | AC-AKSHARE-VAL | akshare |
| tdx_pytdx | 9.5 | AC-TDX-FAMILY | tdx |
| mootdx | 9.5 | AC-TDX-FAMILY | mootdx |
| eastmoney | 9.6 | AC-EM-SINA | eastmoney |
| sina_finance | 9.6 | AC-EM-SINA | sina |
| ths_ifind | 9.7 | AC-AUTH-GATED | ifind |
| qmt_xtdata | 9.7 | AC-AUTH-GATED | qmt |
| qmt_xqshare | 9.7 | AC-AUTH-GATED | xqshare |
