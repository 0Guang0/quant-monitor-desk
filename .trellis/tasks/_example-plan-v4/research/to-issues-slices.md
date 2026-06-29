# To-Issues 切片 — Plan v4.1 样板

## 垂直切片总表

| 切片  | Execute Step | 依赖 | 证据                                   |
| ----- | ------------ | ---- | -------------------------------------- |
| EX-01 | 9.1          | 9.0  | `execute-evidence/9.1-{red,green}.txt` |

---

## §1 EX-01 — 验证样板 manifest

**What to build：** 确认 `generate_manifests` 对 v4.1 将 slot2 设为 ENTRY。

**Acceptance criteria：**

- [ ] `implement.jsonl` 第二条含 `00-EXECUTION-ENTRY.md`
- [ ] `validate-plan-phase … 5e` 零错误

**建议测试：** `tests/test_execution_index_protocol.py`

**Out of scope：** 生产代码变更
