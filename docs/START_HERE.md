# Start Here

第一次使用 Quant Monitor Desk 时，请先确认你是哪类角色：

| 角色         | 入口                          |
| ------------ | ----------------------------- |
| 用户/操作者  | `docs/OPERATOR_GUIDE.md`      |
| 开发者/Agent | `docs/DEVELOPER_GUIDE.md`     |
| 研究者       | `docs/RESEARCHER_GUIDE.md`    |
| 运维排障     | `docs/ops/TROUBLESHOOTING.md` |

## 本项目核心边界

1. local-first。
2. 不是 day-one 自动交易系统。
3. QMT/Yahoo/qmt_xqshare 默认禁用，必须用户确认。
4. Agent 只读，不写库，不下单。
5. 所有数据源切换必须通过 SourceRoutePlan 显式记录。
