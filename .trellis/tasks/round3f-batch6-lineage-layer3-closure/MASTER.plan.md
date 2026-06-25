# MASTER 计划 — B3F-LIN Lineage / Layer3 Registry Closure

> **Execute 入口** — 无 production clean write；registry 闭合归主会话 + B3F-REG。  
> **3D.3：** B01-LIN 仅 partial hygiene；本任务关 ADV-R3X / R3Y-VR / R3-B6-021-O-01/02 registry 证据链。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| 任务 slug | `round3f-batch6-lineage-layer3-closure` |
| Playbook ID | B3F-LIN |
| 分支 | `fix/round3f-batch6-lineage-layer3-registry-closure` |
| Worktree | `../quant-monitor-desk-wt-b3f-lin` |
| 模型 | `composer-2.5` |
| manifest_protocol_version | `3` |
| 基线 | `master` @ `7f628c9` |

### Boundary（Playbook §2.5 / §2.6）

| Owns | Must not |
|------|----------|
| `layer3_chains/**` lineage/snapshot 验收 | production clean write |
| `layer2_sensors/**` VR binding 验收 | live source 默认 |
| registry **proposed delta** | 直接 commit RESOLVED |
| `tests/test_round3f_lineage_layer3_registry_closure.py` | 宣称 3D.3 已全关 |

### 0.1 门控速查

| 项 | 值 |
|----|-----|
| 怎么测 | Playbook §8.2 + §8 垂直切片 |
| 怎么验收 | `validate-execute-handoff` + closure 九项 |
| prod-path | staged/tmp_path only |

---

## 1. 目标

关闭 roadmap `R3F-LIN-01..03`、`R3F-L3-01..02` 的 **runtime 证据** + **registry 草案**；主会话批处理三件套。

### 1.5 停止条件

| # | 事件 | 处理 |
|---|------|------|
| 1 | production clean write | HARD_STOP |
| 2 | 直接 commit registry RESOLVED | 禁止 |
| 3 | 修改 layer5_evidence/** | 禁止 |
| 4 | 宣称 3D.3 已全关 | 禁止 |

### 1.6 原计划归并

| 来源 | 内容 |
|------|------|
| B01-LIN `06bcfde1` | partial hygiene tests |
| Playbook §8.2 | 验收命令 |
| research/source-index.md | 权威路径 |

---

## 8. 实现顺序

| 序 | ID | 交付物 | AC |
|----|-----|--------|-----|
| 1 | R3F-L3-01 | malformed `bars[]` fail-closed | O-01 |
| 2 | R3F-L3-02 | full row tuple rebuild | O-02 |
| 3 | R3F-LIN-02 | VR binding 正负向 | R3Y-LINEAGE-VR-001 |
| 4 | R3F-LIN-01 | L3/L4 contract lineage | ADV-R3X partial |
| 5 | R3F-LIN-03 | manifest + registry draft | Wave-B reconcile |

### 8.0 Boot

| RED 命令 | GREEN 命令 | 证据 | 已执行 |
|----------|------------|------|--------|
| `uv run pytest tests/test_layer3_snapshot_builder.py -q --co -q` | 同左 + context-closure | `8.0-red.txt` / `8.0-green.txt` | [x] |

### 8.1 R3F-L3-01 — malformed bar fail-closed

| RED | `uv run pytest tests/test_round3f_lineage_layer3_registry_closure.py::test_b3fLin_r3fL301_malformedBarElement_failClosed -v`（若缺实现则 FAIL） |
| GREEN | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_malformedBarElement_rejects -v` |
| 证据 | `8.1-red.txt` / `8.1-green.txt` | 已执行 | [x] |

### 8.2 R3F-L3-02 — full row tuple

| RED | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_deterministicRebuild_sameInputsSameHash -v`（021 旧版曾 FAIL） |
| GREEN | 同上 exit 0 |
| 证据 | `8.2-red.txt` / `8.2-green.txt` | 已执行 | [x] |

### 8.3 R3F-LIN-02 — VR binding

| RED | `uv run pytest tests/test_layer2_sensor_loader.py::test_layer2Snapshot_lineageVrMismatch_rejects -v` |
| GREEN | `uv run pytest tests/test_layer2_sensor_loader.py -k lineage -q` |
| 证据 | `8.3-red.txt` / `8.3-green.txt` | 已执行 | [x] |

### 8.4 R3F-LIN-01 — L3/L4 lineage contract

| RED | `uv run pytest tests/test_layer4_market_structure.py::test_marketSnapshot_lineageUpstreamFromLayer3 -v` |
| GREEN | `uv run pytest tests/test_layer3_snapshot_builder.py -k lineage -q` |
| 证据 | `8.4-red.txt` / `8.4-green.txt` | 已执行 | [x] |

### 8.5 R3F-LIN-03 — closure gate + registry draft

| RED | `uv run pytest tests/test_round3f_lineage_layer3_registry_closure.py -q` |
| GREEN | 同上 exit 0 |
| 证据 | `8.5-red.txt` / `8.5-green.txt` | 已执行 | [x] |

---

## 9. 验证（Playbook §8.2）

```bash
uv sync --locked
uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q -k lineage
uv run pytest tests/test_round3f_lineage_layer3_registry_closure.py -q
uv run pytest -q && uv run ruff check .
```

---

## 11. Execute → Audit DoD

- [x] §8.0–8.5 RED/GREEN 证据齐
- [x] `closure.report.md` 九项
- [x] `registry-proposed-delta.md`（非直接闭合）
- [x] 全量 pytest（`QMD_RESOURCE_PROFILE=normal`）
- [x] 无 production DB 写入

---

## 12. Skill 表

| Skill | 绑定 | 已执行 |
|-------|------|--------|
| test-driven-development | §8.5 | [x] |
| incremental-implementation | 每步后子集 pytest | [x] |
| karpathy-guidelines | GREEN 前 | [x] |
| testing-guidelines | 五字段 | [x] |
| trellis-implement | Execute agent | [x] |
