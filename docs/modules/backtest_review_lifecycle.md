# Backtest Review Lifecycle（Round2.6）

## 1. 定位

本生命周期用于 Round4 `029_implement_backtest_and_review.md`。它借鉴 JQ2PTrade MiniPTrade 的“固定生命周期 + context + report builder”结构，但不借鉴下单、持仓、交易费用或自动交易语义。

## 2. 生命周期

```text
load scenario
→ load frozen snapshot/evidence
→ build review context
→ build event set
→ iterate event dates
→ compute forward windows T+1/T+3/T+5/T+10/T+20
→ compute metric snapshots
→ write backtest_run_log / backtest_metric_snapshot / backtest_report
→ generate limitations and human review notes
```

## 3. 硬边界

1. 不支持 `order/order_target/order_value/cancel_order`。
2. 不输出买卖动作。
3. 所有窗口必须 as-of freeze，禁止前视。
4. 每次 run 必须保存 `scenario_hash`、`params_hash`、`data_cutoff_time`。
5. 每个报告必须 `no_action_semantics=true`。

## 4. 指标契约

见 `specs/contracts/backtest_metric_contract.yaml`。

## 5. 后续实现模块

```text
backend/app/review/backtest_engine.py
backend/app/review/review_context.py
backend/app/review/report_builder.py
backend/app/review/metrics.py
```

## 6. 验收

```bash
python -m pytest tests/test_backtest_review_lifecycle.py tests/test_backtest_metric_contract.py -q
```
