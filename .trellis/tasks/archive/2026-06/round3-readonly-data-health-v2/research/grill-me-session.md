# Grill session — data health v2 (Plan Phase 3)

## Q: 缺 WL 时能否用 registry 猜 whitelist？

**A:** 否。必须 BLOCKED + owner 文案。已写入 §1.5 #6。

## Q: 基线红测能否改为只断言 report 存在？

**A:** 否。须保留 PASS/WARN + 日 K 规则。DH2-BASE 用自包含 fixture。

## Q: rollup 能否在 SP3 未完成时声称 production ready？

**A:** 否。仅 staged/sandbox readiness；gate 字段独立。
