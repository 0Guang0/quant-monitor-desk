# Grill-Me Session — Batch 2.5 (Plan Phase 3)

> 2026-06-20 · 质问锚点：018A + Batch 2 PASS 前提

## Q1: 为什么 Batch 2 不够？

**A:** Batch 2 用 fixture observation 驱动快照，不证明 route/fetch/validation/write/lineage 生产链。Batch 2.5 闭合 G1/G3/G5（018A §6）。

## Q2: 能否在 Batch 2 里偷偷加 live fetch？

**A:** 禁止。BATCH_MAP 与 018A §4 明确排除；模块边界禁止 Layer1→adapter。

## Q3: 默认用什么源？

**A:** **staged/fixture**（`FixtureFetchPort` / macro fixture）。Live QMT/FRED/Yahoo 须用户逐阶段授权证据。

## Q4: FRED primary_source 与 registry 不对齐怎么办？

**A:** Phase 0 记为已知 gap；Phase 2–3 用 `macro_supplementary` + fixture 映射到 observation 形状，不假装 live FRED PASS。

## Q5: 五阶段能否合并？

**A:** 禁止。Audit A0–A4 逐阶段签字；018A §9。

## Q6: schema.sql 无 axis 表？

**A:** Phase 0 gate：以 migration 011 为 runtime 权威；schema.sql 同步为窄 scope 或标 DEFERRED（非 silent）。

## Q7: 指标 allowlist 谁定？

**A:** Execute Phase 2 从 `configs/layer1_axes.yml` enabled 指标中选 1 个：非 forbidden、非 blindspot、可观测；MASTER 约束条件，不写死 ID 以免与 spec 漂移。

## Q8: Batch 6 CLI？

**A:** 非目标。可选窄 `scripts/qmd_layer1_ingest.py` 须 MASTER 批准且默认 dry-run。

## 开放项 → MASTER §7 Red Flags

- 合成 lineage 冒充生产 → Phase 4 禁止
- Phase 1/2 DB mutation → 测试 + inspect 证明
- severe conflict / manual review 写 clean → 阻断

## 结论

Plan 可冻结五阶段 MASTER §8；默认 staged ingestion；live 须授权。
