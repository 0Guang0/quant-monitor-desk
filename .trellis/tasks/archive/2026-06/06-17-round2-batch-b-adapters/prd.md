# Round 2 Batch B — 013 core adapter skeletons

## Goal

五个 adapter skeleton + factory；SUCCESS 写真实 raw + 可选 FileRegistry 登记（偿还 Batch A）；cninfo 未发布语义。

## Acceptance Criteria

| # | 标准 | 验证 |
|---|------|------|
| AC-1 | 五 adapter + factory | §8.5 + §10 A |
| AC-2 | SUCCESS raw + content_hash | §8.1 |
| AC-3 | parametrized PortError + fetch_log | §8.1 |
| AC-4 | QMT AUTH + SUCCESS | §8.3 |
| AC-5 | 无 WriteManager in adapters | §10 grep |
| AC-6 | registry 对齐 | §8.2–8.5 |
| AC-7 | yahoo validation_only | §8.5 |
| AC-8 | pytest + cov ≥75% | §10 A/C |
| AC-9 | FileRegistry local_path 对齐 | §8.1 |
| AC-10 | cninfo 未发布 EMPTY_RESPONSE | §8.4 |

## 索引

**MASTER.plan.md** v1.1 · 对抗审计 `research/adversarial-audit-remediation.md`
