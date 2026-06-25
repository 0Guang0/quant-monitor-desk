# Vertical Slices — B3F-BR (/to-issues · Plan 3.5)

> 冻结为 MASTER §8 · 对应 `R3F-BR-01..05`

| 序 | ID | 垂直切片 | 交付物（完标准） | 依赖 | AC |
|----|-----|----------|------------------|------|-----|
| 0 | BR-BOOT | 基线 RED | closure + runners 测试 RED 证据 | — | AC-BR-PLAN |
| 1 | BR-01 | Backfill parity | `test_r3fBr01_*` + registry 叙事无 skip-validator | BOOT | AC-BR-01 |
| 2 | BR-02 | Reconcile re-fetch | `test_r3fBr02_*` 锚定 `test_audit_remediation` | BOOT | AC-BR-02 |
| 3 | BR-03 | R3-PARTIAL-5 guard | `test_r3fBr03_*` UNRESOLVED 无重开 + handoff 指向 | BOOT | AC-BR-03 |
| 4 | BR-04 | Handler registry | `OrchestratorJobHandler` + registry + `test_r3fBr04_*` + `test_sync_runners` 接线 | BR-01 | AC-BR-04 |
| 5 | BR-05 | ADR-023 链 + §8.5 | `test_r3fBr05_*` + Playbook §8.5 40 tests 绿 | BR-04 | AC-BR-05 |

## 范围门控

| 禁止 | 理由 |
|------|------|
| 重开 crash-window 实现 | B3V-C04 已闭合；`R3F-BR-03` guard only |
| production write | Batch 3F hardening |
| 主会话外直接改 UNRESOLVED 关账 | `R3F-BR-05` honest DEFERRED + ADR 链 |
