# Original Plan Trace — R3FR-03

| 任务卡 AC        | Step | 测试函数                                               |
| ---------------- | ---- | ------------------------------------------------------ |
| 缺 pytdx         | 9.1  | `test_tdxPytdxPort_missingPytdx_returnsDisabledSource` |
| live 授权        | 9.4  | `test_tdxPytdxPort_withoutAuth_*` + live auth 模块     |
| mocked 默认      | 9.5  | `test_tdx_manual_probe.py`                             |
| minute/scan 拒绝 | 9.3  | `test_tdxPytdxPort_rejects*`                           |
| raw hash         | 9.2  | `test_tdxNormalizer_equityManifest_*`                  |
| 编排 evidence    | 9.5  | `test_tdx_manual_probe` comparison 子集                |
| guardrails       | 9.7  | `test_reference_adoption_guardrails`                   |
| registry caps    | 9.6  | `test_tdxPytdx_capsMatchTaskCard` + route test         |
| 完整形态         | 9.7  | Tier B + loop_maintain                                 |
