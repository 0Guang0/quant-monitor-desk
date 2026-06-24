# Phase A 派发记录

> 派发时间：2026-06-24  
> 模型：**composer-2.5**（全部，无 fast）  
> 阶段：**Phase A only**（align-ponytail）

## Worktrees

| 桶   | 分支                                  | Worktree 路径                                                       |
| ---- | ------------------------------------- | ------------------------------------------------------------------- |
| G    | debt/test-hygiene/bucket-g-gate       | `C:\Users\Guang\Desktop\quant-monitor-desk-worktrees\bucket-g-gate` |
| L1   | debt/test-hygiene/bucket-l1-layer1    | `...\bucket-l1-layer1`                                              |
| L23  | debt/test-hygiene/bucket-l23-layers   | `...\bucket-l23-layers`                                             |
| DS   | debt/test-hygiene/bucket-ds-sync      | `...\bucket-ds-sync`                                                |
| VAL  | debt/test-hygiene/bucket-val-storage  | `...\bucket-val-storage`                                            |
| OPS  | debt/test-hygiene/bucket-ops-cli      | `...\bucket-ops-cli`                                                |
| LOOP | debt/test-hygiene/bucket-loop-trellis | `...\bucket-loop-trellis`                                           |
| AUD  | debt/test-hygiene/bucket-audit-r3x    | `...\bucket-audit-r3x`                                              |
| SMK  | debt/test-hygiene/bucket-smk-smoke    | `...\bucket-smk-smoke`                                              |

## 并行 Agent（composer-2.5）

| Agent      | 描述                      | Agent ID                             |
| ---------- | ------------------------- | ------------------------------------ |
| agent-G    | Bucket G gate tests       | 997be3bb-4993-446f-b0c7-0f3002b8f66a |
| agent-L1   | Bucket L1 layer1 tests    | b85a0b5a-7167-45ae-b539-341f99e8e1b3 |
| agent-L23  | Bucket L23 layers tests   | 60f5bbf4-1101-4a26-99d7-0208fb776e18 |
| agent-DS   | Bucket DS sync tests      | e2afc12b-d464-4a34-b27f-d2680983a39f |
| agent-VAL  | Bucket VAL storage tests  | 427ddc7b-887e-4068-95d5-f4737b28a4cd |
| agent-OPS  | Bucket OPS cli tests      | 932d5631-c062-4647-a515-d5fe11976a62 |
| agent-LOOP | Bucket LOOP trellis tests | 0de7d21a-6169-4261-8787-84ffdb9644d1 |
| agent-AUD  | Bucket AUD r3x tests      | c6a4e3d0-5986-43d7-807c-6144b6238e19 |
| agent-SMK  | Bucket SMK smoke tests    | 5a92f337-3255-4375-bc11-4c30c17cccb5 |

## MERGE-C

- **Baseline / merge**：主会话待 9 桶完成后执行（integration 分支 `debt/test-hygiene/integration` 尚未创建）
- 证据汇总目录：`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/`

## 已知环境项

- 派发时主仓 `uv run python -m pytest` 报 `No module named pytest`；各 worktree 内 agent 需 `uv sync --all-extras` 或按项目 dev 依赖安装后再跑验证
