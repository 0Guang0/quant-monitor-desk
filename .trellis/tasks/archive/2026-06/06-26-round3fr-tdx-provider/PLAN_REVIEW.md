# 执行计划审阅稿 — R3FR-03（对抗性审计修复后）

> **分支：** `refactor/round3fr-tdx-provider`  
> **审计：** `research/adversarial-plan-audit.report.md` — ADV-01..25 已闭合  
> **状态：** 待用户批准 → `task.py start`

---

## 1. 目标

TDX provider port（`fetch_ports` + `normalizers`）+ 瘦编排；disabled/raw-only。

## 2. 改动文件（Execute）

| 动作 | 路径                                                                             |
| ---- | -------------------------------------------------------------------------------- |
| 新建 | `backend/app/datasources/fetch_ports/tdx_pytdx_port.py`                          |
| 新建 | `backend/app/datasources/normalizers/tdx.py`                                     |
| 新建 | `tests/test_tdx_pytdx_port.py`                                                   |
| 修改 | `fetch_port.py`（PortError 扩展）                                                |
| 修改 | `adapters/tdx_pytdx.py`、`interface_probe_fetch_ports.py`、`tdx_manual_probe.py` |
| 修改 | `tdx_live_manual_probe_gate.py`、授权 MD（caps 3）                               |
| 修改 | `source_registry.yaml`、`source_capabilities.yaml`（`resource_caps`）            |

## 3. Caps 权威（§0.2）

equity/index **max_rows=3**（supersedes 018C 的 10）；9.4+9.6 须同步 gate/授权 MD/registry。

## 4. 测试矩阵（TDD 函数名）

| Step | 新/关键测试                                                  |
| ---- | ------------------------------------------------------------ |
| 9.1  | `test_tdxPytdxPort_missingPytdx_returnsDisabledSource`       |
| 9.2  | `test_tdxNormalizer_equityManifest_hasRequiredFieldsAndHash` |
| 9.3  | `rejectsMinute` / `rejectsFullMarket` / `rejectsOverCap`     |
| 9.4  | `withoutAuth` + `forbiddenDirectPortInvocation`              |
| 9.6  | `capsMatchTaskCard` + `tdxRoute_disabledByDefault`           |

## 5. 验收

- Tier A：任务卡 §11 两档 pytest
- Tier B：`uv run pytest -q`
- Tier C：`uv run python scripts/loop_maintain.py`（§9.7）

## 6. 并行隔离

- **本任务独占** `tdx_pytdx` registry caps 行
- **勿混** `06-26-round3fr-provider-catalog`（R3FR-05）
- **不闭合** B01-C03 live defer（host 占位）

## 7. Rollback

见活任务卡 §15。

## 8. 权威入口

- [`EXECUTION_INDEX.md`](./EXECUTION_INDEX.md)
- [`frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md`](./frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md)
- [`research/adversarial-plan-audit.report.md`](./research/adversarial-plan-audit.report.md)

**批准后回复「批准执行」。**
