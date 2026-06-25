# PRD — B3V-SYNC（精简）

## 问题

审计 `VR-SYNC-002`：契约未区分已实现/预留 job；reserved 抛裸 `NotImplementedError`。`VR-SYNC-001`：写成功与 COMPLETED 之间存在 crash-window。

## 用户故事

- 作为编排调用方，我需要契约与 runtime 一致的 job support matrix，以便 CLI/API 不误报 reserved 为可用。
- 作为运维，我需要 reserved job 返回带 code/owner/phase 的稳定 deferred 错误。
- 作为 SRE，我需要 crash-window 有可测恢复路径或明确 3F.4 交接。

## 非目标

- 实现 full_load / data_quality / revision_audit 完整 runner
- 修改 write 模式契约（B3V-OPS）
- CLI 发布
