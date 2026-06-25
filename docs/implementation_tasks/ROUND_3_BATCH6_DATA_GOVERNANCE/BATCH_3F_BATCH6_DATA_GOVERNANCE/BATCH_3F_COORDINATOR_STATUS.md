# Batch 3F 主会话协调状态

> 更新：2026-06-25 · **Phase C：integration merge — 八路完成**  
> **纪律：** 禁止 `--no-verify`；**禁止**为通过 hook 削弱测试目的/价值（不得全局 mock RG 等）  
> **Integration：** `integration/round3-batch3f` @ `d0393153`

---

## merge 进度

| 序     | 分支       | 状态                                         |
| ------ | ---------- | -------------------------------------------- |
| #1 MIG | `12cbb3d`  | ✅                                           |
| #2 LIN | `9f9320d`  | ✅                                           |
| #3 CLI | `fe495cfd` | ✅                                           |
| #4 SH  | `e000791a` | ✅                                           |
| #5 BR  | `fdb29a05` | ✅                                           |
| #6 HYG | `ea7f2c7d` | ✅                                           |
| #7 CI  | `3aff66ba` | ✅                                           |
| #8 REG | `8b79fd2`  | ✅ FF → `d0393153`（registry COVERAGE 交付） |

---

## pre-commit 失败处置原则（用户确认）

| 类型                                | 处置                                                                                                               |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **环境**（RG HARD_STOP / 内存不足） | 先 `Stop-Process -Name codebase-memory-mcp -Force` 释放内存；再设 `QMD_RESOURCE_PROFILE=normal` 重跑；**不**改测试 |
| **真实回归**                        | 修 **生产代码** 或测试与实现/docstring **对齐**（目的不变）                                                        |
| **禁止**                            | autouse 全局 stub RG、删断言、改测试目标换绿、`--no-verify`                                                        |

---

## 验证

- integration 全量 `uv run pytest -q`：**绿**（`QMD_RESOURCE_PROFILE=normal`，post-REG merge）
- REG §8.7 范围测：40 passed + `check_manifest_files.py` OK

---

## 下一步（主会话 §7.3）

1. 按需应用 `registry_proposed_delta.yaml` 中 **COORDINATOR-QUEUED** 项（registry 三件套 `Last reconciled` 刷新；不重复闭合已 RESOLVED 实现）
2. `R3F-LIN-03` Wave-B 全 reconcile（六线 evidence 已齐，可主会话批处理）
3. 更新 `ROUND3_HANDOFF` / 归档 Batch 3F 协调包
