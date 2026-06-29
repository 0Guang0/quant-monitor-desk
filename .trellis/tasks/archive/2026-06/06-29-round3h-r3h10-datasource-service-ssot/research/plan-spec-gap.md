# Plan 加固 — spec-driven-development

> **Skill:** `spec-driven-development` · **阶段：** SPECIFY → PLAN（冻结前）  
> **任务：** R3H-10 · **日期：** 2026-06-29

## ASSUMPTIONS（显式假设）

1. 正式 Plan freeze **延后**；Execute 按 `to-issues-slices.md` 单切片推进，每切片全量 pytest。
2. R3H-10 **不**新增 migration、**不**做 R3H-08 真网 live。
3. `参考项目/**` 仅 Plan 只读对照，永不 runtime 依赖。
4. Sync 生产语义下 `datasource_service=` **必须显式传入**（fail-closed ADR）。

---

## 六要素覆盖自检

| 要素                  | 状态 | SSOT / 缺口                                                            |
| --------------------- | ---- | ---------------------------------------------------------------------- |
| **Objective**         | ✅   | `R3H_10_DATASOURCE_SERVICE_SSOT.md` §1 · `WAVE1_...INDEX.md` §1        |
| **Commands**          | ⚠️   | 验证命令已散见切片；**缺**活卡 § 统一块（见下）                        |
| **Project Structure** | ✅   | `backend/app/datasources/` · `sync/` · `ops/*_pilot*` · `tests/test_*` |
| **Code Style**        | ✅   | ponytail + 现有 `DataSourceService` / guard 模式                       |
| **Testing Strategy**  | ✅   | TDD RED→GREEN · `execute-evidence/9.x-*.txt` · 全量 `uv run pytest -q` |
| **Boundaries**        | ⚠️   | rehearsal vs 产品路径在 S10-03；**缺**活卡 Boundaries 三节表           |
| **Success Criteria**  | ✅   | INDEX §1 AC + `to-issues-slices.md` 每切片验收                         |

---

## 成功标准（由需求改写为可测条件）

| 原表述                       | 可测成功标准                                                           |
| ---------------------------- | ---------------------------------------------------------------------- |
| 「统一经 DataSourceService」 | 矩阵 12 行中生产路径标 ✅；`interface_probe` 委托 service（S10-04）    |
| 「消除 bypass」              | `test_r3ySync001_*` + 新增无 service 负向测绿                          |
| 「STAGED-PILOT-SSOT CLOSED」 | audit 行 CLOSED + staged/live port 与 `fetch_ports` 同实现类（S10-05） |
| 「契约 SSOT」                | `datasource_service_contract.yaml` status = `active`（S10-02）         |

---

## Boundaries（建议写入活卡 §2）

| 层级          | 内容                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------- |
| **Always**    | 每切片 RED→GREEN 后全量 pytest；改 `service`/sync 前 GitNexus `impact`                        |
| **Ask first** | 删 pilot 模块；改 `forbidden_direct_callers` 列表；契约 status 枚举变更                       |
| **Never**     | runtime `import 参考项目/**`；默认构造 production `DataSourceService`；用 pilot 冒充产品 live |

---

## Commands（建议写入活卡 §3）

```bash
# 单切片验证（每步）
uv run pytest -q

# 切片定向（示例）
uv run pytest -q tests/test_sync_orchestrator.py tests/test_datasource_service.py
uv run pytest -q tests/test_staged_pilot.py tests/test_batch275_live_pilot_gate.py

# Plan 冻结门（用户批准 formal freeze 后）
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot
```

---

## Open Questions（Plan 阶段剩余）

| ID     | 项                                                    | 建议                                 |
| ------ | ----------------------------------------------------- | ------------------------------------ |
| ~~U1~~ | fail-closed vs 默认 service                           | **已裁决** → ADR-025                 |
| U3     | `interface_probe` 是否用 digital-oracle `gather` 并行 | 默认否；单线程委托 service 即可 PASS |
| U4     | 参考树 CI 不可见                                      | Execute 前本地只读 clone；不阻塞     |

---

## spec-driven-development 验证清单

- [x] 六要素已扫描，缺口已标 ⚠️ 并给出落点
- [x] 成功标准可测
- [x] Boundaries 三档已起草（待合并活卡）
- [ ] **人工：** 活卡 `R3H_10` 补 §Commands + §Boundaries（freeze 前或 S10-BOOT 时）
