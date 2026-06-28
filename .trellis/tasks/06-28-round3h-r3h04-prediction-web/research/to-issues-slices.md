# To-issues 垂直切片 — R3H-04（Plan 3.5）

| Slice ID | 名称 | Step | 依赖 | 交付物 |
| --- | --- | --- | --- | --- |
| S0 | boot_test_skeleton | 9.0 | — | 三测试模块 import 绿 |
| S1 | probability_evidence_contract | 9.1 | S0 | `probability_signal.py` + contract tests |
| S2 | kalshi_port | 9.2 | S1 | `kalshi_port.py` + replay kalshi |
| S3 | polymarket_port | 9.3 | S1 | `polymarket_port.py` + replay polymarket |
| S4 | web_search_evidence | 9.4 | S1 | `web_search_evidence_port.py` + `manual_review_staging.py` |
| S5 | registry_coordinator | 9.5 | S2,S3,S4 | 三源 registry + `9.5-manifest.md` |
| S6 | clean_write_negative | 9.6 | S2,S3,S4,S5 | `test_no_clean_write_for_web_evidence.py` |
| S7 | layer5_smoke | 9.7 | S4 | L5 manual-review smoke |
| S8 | merge_gate | 9.8 | S5,S6,S7 | 全库 pytest + loop_maintain |

**并行窗口：** S2 ∥ S3 ∥ S4（S1 完成后）
