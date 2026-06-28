# Grill Session — R3H-03（Plan Phase 3）

> Skill: `grill-me` · 2026-06-28

## 质问与回答

**Q1：3G baostock `--live-wire` 是否等于 baostock 已 `READY_WITH_EVIDENCE`？**  
A：**否**。仅证明 pilot 路径可写；G11 要求产品化 `baostock_port` + evidence，非运维 `--live-wire`。

**Q2：R3H-03 能否写主库？**  
A：**否**。sandbox/replay/`.audit-sandbox` only；与 R3H-01 一致。

**Q3：`ops/staged_pilot_fetch_ports` 保留还是长期？**  
A：**L2 迁出**到 `datasources/fetch_ports/`；ops 仅留 orchestration/CLI；禁止双份 fetch 长期并存。

**Q4：十源都要真网 live 吗？**  
A：**否**。`READY_WITH_EVIDENCE` = port + gate + route + **replay** + evidence 字段；真网 live 为可选加分（用户授权），非阻塞。

**Q5：akshare 能否升为 primary？**  
A：**禁止**。registry `validation_only: true` 永久；测试须证明不可 silent 替换 baostock/cninfo。

**Q6：QMT/iFinD/xqshare 默认状态？**  
A：**authorization-disabled**；READY 仅当 `license_gate` + 用户环境证明 + 负例测试齐全。

**Q7：mootdx 与 tdx_pytdx 关系？**  
A：同属 TDX-compatible **验证**路线；独立 source_id；不得互为 silent fallback；可共享 parsing 辅助函数于 `normalizers/`（非 catch-all adapter）。

**Q8：工期紧能否 ADR 部分源？**  
A：终态仅 `READY_WITH_EVIDENCE` 或 **书面 ADR**；Plan 默认十源实现；若受阻 **ADR 候选**：`mootdx`（与 tdx_pytdx 重叠）、`qmt_xqshare`（远程终端边缘）— **须用户确认** 是否接受。

**Q9：Layer3/4/5 做到什么程度？**  
A：**§9.9 smoke only**；非 R3H-05；声明 CN evidence 路径可流入 Layer 契约测试即可。

**Q10：与 R3H-04 并行冲突？**  
A：禁止改 kalshi/polymarket/web_search registry 行与 adapter；共享文件改十源行 + coordinator 表。

**Q11：EasyXT 参考能 import 吗？**  
A：**禁止 runtime import**；仅 L2 重写 TDX lifecycle / integrity 形状。

**Q12：G2/G17 交易日历本卡闭合还是交 R3H-05？**  
A：**⚠️ 须 Grill-me 用户确认**。Plan 默认：§9.9 登记 `data_health_profiles/cn_market.py` 最小 profile + 测试 stub；**完整**交易日窗可交 R3H-05，但须在 frozen §8 写清交接，不得 silent defer。

**Q13：cninfo live 范围？**  
A：**⚠️ 须 Grill-me 用户确认**。Plan 默认：metadata/filing list replay-first；PDF 下载 capped（§7）；真网 live 可选。

**Q14：最小垂直切片顺序？**  
A：**证据契约(9.1)→ baostock(9.2)→ cninfo(9.3)→ akshare(9.4)→ TDX(9.5)→ eastmoney/sina(9.6)→ auth-gated(9.7)→ registry(9.8)→ layer(9.9)→ merge(9.10)**。

## 结论（Plan 锁定）

| 维度 | 决定 |
| ---- | ---- |
| 范围 | 十源终态；吸收 G11/G16 |
| 主库 | 禁止写入 |
| 架构 | 每源 port + `cn_market` normalizer + `license_gate` |
| akshare | validation_only 永久 |
| QMT 系 | 默认 disabled + tested route reason |
| Layer | smoke only；R3H-05 不做 |
| ADR | 仅显式收窄；默认十源实现 |

**Phase 3 complete**
