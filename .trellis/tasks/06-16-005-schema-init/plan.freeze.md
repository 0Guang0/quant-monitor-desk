# Plan 冻结 — 005 Schema（示范）

> Execute / Audit **不读**

---

## 3. 冻结自检（示范已勾）

### 3.0 双契约 one-pager

| ✓ | Execute（MASTER） | ✓ | Audit（AUDIT） |
|---|-------------------|---|----------------|
| [x] | §10 Execute 专用；B/C prod-path | [x] | §1 + §2 A1–A8（A6 SKIP 有理由） |
| [x] | §11 仅交接 | [x] | A7/A8 audit-sandbox ≠ Execute DATA_ROOT |
| [x] | 6.pre 路径 | [x] | 7.pre + audit.jsonl |

### 3.1 MASTER

- [x] §0.1 + §8 证据 + §9 四层 + §10 Execute 专用
- [x] §12 无 Audit skill

### 3.2 AUDIT

- [x] §2 无留空 `{{}}`；A6 §2.2 跳过行已写
- [x] A9 主会话

### 3.3 REPAIR / jsonl

- [x] REPAIR 按需；implement→MASTER；check→spec

**005 示范说明：** A6 跳过 = schema 无性能 SLA；§2 其余行已替换占位。Plan 填表见 guides `templates/AUDIT.plan.md` §2.1/§2.2、`plan.freeze.md` §2.5。
