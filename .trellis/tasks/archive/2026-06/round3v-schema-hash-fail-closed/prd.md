# PRD — B3V-DATA（薄索引）

见 **MASTER.plan.md** §1–§3。

- **问题**: 结构化数据无 `schema_hash` 可绕过 schema drift 检查写入 clean 表。
- **方案**: 契约强制 + adapter 有界推导 + ValidationGate fail-closed。
- **不在范围**: registry 闭合、RawStore、sync、layer5、production clean write。
