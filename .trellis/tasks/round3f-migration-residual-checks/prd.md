# PRD — B3F-MIG（薄索引）

见 **MASTER.plan.md** §1–§3。

- **问题**: Migration 009 残余（priority CHECK、SELECT * 重建、registry 生命周期列）与 008 plan 路由未闭合，阻塞 B3F-SH 合并。
- **方案**: 012 migration + ADR-002 + 路由文档 + 六路 verify/regression 测试；009 CHECK verify-only。
- **不在范围**: `source_health_snapshot` 表；registry 三件套闭合；production clean write。
