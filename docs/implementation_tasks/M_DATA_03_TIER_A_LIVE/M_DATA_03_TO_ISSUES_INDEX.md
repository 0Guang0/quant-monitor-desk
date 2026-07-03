# M-DATA-03 `/to-issues` 索引

> **活卡：** `M_DATA_03_TIER_A_LIVE.md`  
> **Trellis 切片 SSOT：** `.trellis/tasks/m-data-03-tier-a-live/research/to-issues-slices.md`

## 队列位置

```text
M-DATA-03（本票）→ M-G1-03 → M-G2/G4/G5-FULL → M-PASS-01
```

## 切片一览

| Slice                | 业务一句话                           | 并行批 |
| -------------------- | ------------------------------------ | ------ |
| S00-ELIGIBILITY      | 11 源资格矩阵固化                    | 串行   |
| S00-INFRA            | 隔离库 live 验收脚手架               | 串行   |
| S-LIVE-FRED          | FRED 真网增量→axis_observation       | 2a     |
| S-LIVE-BAOSTOCK      | baostock 真网→security_bar_1d        | 2a     |
| S-LIVE-US-TREASURY   | 美债真网→macro clean                 | 2b     |
| S-LIVE-BIS           | BIS 真网→macro clean                 | 2b     |
| S-LIVE-WORLDBANK     | 世行真网→macro clean                 | 2b     |
| S-LIVE-CFTC          | CFTC 真网→macro clean                | 2b     |
| S-LIVE-SEC-EDGAR     | SEC 真网→us_disclosure_clean         | 2b     |
| S-LIVE-ALPHA-VANTAGE | AV 真网→security_bar_1d              | 2c     |
| S-LIVE-DERIBIT       | Deribit 真网→crypto_derivative_clean | 2c     |
| S-LIVE-CNINFO        | cninfo 真网→cn_announcement_clean    | 2c     |
| S-LIVE-MOOTDX        | mootdx 真网→security_bar_1d          | 2c     |
| S-MERGE              | registry 三件套 + test_catalog       | 串行   |
| S-ACCEPT             | 11/11 隔离验收脚本                   | 串行   |

## 设计权威倒查（Plan 已读）

见 Trellis `research/tier-a-live-inventory.md` §1–§4。
