# Grill-Me Session — B01-FRED (Phase 3)

## Q1: FRED pilot 能否关闭 B2.5-O-05 而不做 live fetch？

**A:** 不能单独用 mocked 关闭；须 FRED-only sandbox evidence（manifest + hash + fetch_id）。无 live 时可 re-defer 并强化 closure test；mocked 路径仍须绿。

## Q2: macro_supplementary 能否代替 FRED？

**A:** 禁止。PROMPT_04 + hardening §4 明确 insufficient。

## Q3: 谁改 data_health？

**A:** B01-DH2。FRED 仅 `fred_evidence_validator.py` + closeout 供 DH2 消费。

## Q4: WL 未合并能否 Execute？

**A:** 可以开发；P0 series 回退 Layer1 specs。Merge master 前须 WL 先合并（Track A #1→#3）。

## Q5: Live 何时允许？

**A:** Execute FRED-07；`authorization.yaml` 落盘 + `FRED_API_KEY`；coordinator 2026-06-24 已预授权。

## 结论

范围清晰；主要纠偏：FRED-05 不碰 data_health；registry 主会话合并。
