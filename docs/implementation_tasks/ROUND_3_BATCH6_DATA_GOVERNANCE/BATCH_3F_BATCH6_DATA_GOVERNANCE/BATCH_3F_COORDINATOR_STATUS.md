# Batch 3F 主会话协调状态

> 更新：2026-06-25 · **Phase C：integration merge**  
> **纪律：** 禁止 `--no-verify`；**禁止**为通过 hook 削弱测试目的/价值（不得全局 mock RG 等）  
> **Integration：** `integration/round3-batch3f` @ `e000791a`

---

## merge 进度

| 序     | 分支       | 状态             |
| ------ | ---------- | ---------------- |
| #1 MIG | `12cbb3d`  | ✅               |
| #2 LIN | `9f9320d`  | ✅               |
| #3 CLI | `fe495cfd` | ✅               |
| #4 SH  | `e000791a` | ✅               |
| #5 BR  | `71f09550` | ⏳ 待 merge      |
| #6 HYG | `a753dfc`  | ⏳ 待 merge      |
| #7 CI  | `b9805a28` | ⏳ 待 merge      |
| #8 REG | —          | ⏳ 六线 merge 后 |

---

## pre-commit 失败处置原则（用户确认）

| 类型                                | 处置                                                        |
| ----------------------------------- | ----------------------------------------------------------- |
| **环境**（RG HARD_STOP / 内存不足） | `QMD_RESOURCE_PROFILE=normal`、释放内存后重跑；**不**改测试 |
| **真实回归**                        | 修 **生产代码** 或测试与实现/docstring **对齐**（目的不变） |
| **禁止**                            | autouse 全局 stub RG、删断言、改测试目标换绿、`--no-verify` |

---

## 下一步

1. merge **BR → HYG → CI**（冲突仅合并 `test_catalog`，不削弱测）
2. integration 全量 pytest（normal profile）
3. **REG #8** + §7.3 registry 批处理
