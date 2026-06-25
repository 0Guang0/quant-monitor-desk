# Grill-me Session — B3V-STOR

> Phase 3 · 边界质问

## Q1: 为什么不在 RawStore 内联临时文件逻辑？

**A:** `path_compat` 已集中 Windows 长路径与 `write_bytes`；原子写是 I/O 原语，放 `path_compat` 可单测且避免 RawStore 膨胀。ponytail: 一处实现，RawStore 一行替换。

## Q2: 写失败时目标已存在怎么办？

**A:** 任务卡要求「现有目标保持不变」。`os.replace` 仅在临时文件完整后才执行；异常路径不得 truncate 既有目标。测试须覆盖 pre-existing 文件 + 中途失败。

## Q3: 需要目录 fsync 吗？

**A:** 任务卡 **禁止** Windows 依赖 POSIX-only 目录 fsync。实现：文件 `flush`+`fsync`（平台支持时）+ `os.replace`；不强制 `dir.fsync`。

## Q4: 能改 FileRegistry 吗？

**A:** **否**，除非 RED 证明 RawStore 单测无法覆盖且注册路径断裂。本任务 AC 均在 `test_raw_store.py` 可测。

## Q5: 幂等性测什么？

**A:** 同 `content` 两次 `save` → 同路径、同 hash、文件字节一致；不依赖 FileRegistry。

## Q6: VR-STOR-001 谁闭合？

**A:** Execute 产出 `research/registry_proposed_delta.yaml` + closeout 证据；**主会话**批处理 registry 三件套 commit。

## 结论

边界清晰；五切片垂直；无 scope creep。
