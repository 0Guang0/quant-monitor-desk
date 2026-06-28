# R3H-04 参考项目采纳审计（主会话 · 2026-06-28）

> **纠正：** Plan 写「仓库无 OpenBB clone / 形状已内联 §14」导致 Execute 可能跳过参考对照。`参考项目/agents-for-openbb/**` **存在**（gitignore 本地-only）。

## 活卡列出的参考路径

| 参考路径 | 阶梯 | QMD 目标 | 动作 |
|----------|------|----------|------|
| `参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/.../main.py` | **architecture_only** | `manual_review_staging.py` 证据摘要字段 | 仅借鉴 widget JSON **artifact 形状**；**禁止** FastAPI/OpenAI/openbb_ai runtime |
| `参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/.../main.py` | **architecture_only** | 同上 | dashboard 展示字段命名参考 |
| `backend/app/datasources/fetch_ports/coingecko_port.py` | **L2 模式参照** | kalshi/polymarket port | mock/replay FetchPort 模式，非 OpenBB |
| kalshi/polymarket API | **L3** | `kalshi_port.py`, `polymarket_port.py` | 无合适参考；用户要求 **live smoke capped** |
| web_search | **L3（延后）** | `web_search_evidence_port.py` | 用户 Gate：真实 API **待定**；mock stub READY |

## guardrails 缺口（Plan 未列入 INDEX §3）

- **须补 Read：** `specs/contracts/reference_adoption_guardrails.yaml`
- **须补 Read：** `specs/contracts/data_adapter_contract.md` §6–7

## 当前 Execute 状态

- 三 port + normalizer + staging：**结构正确**（probability / manual-review / no clean write）
- **缺：** live smoke 路径（用户 Gate）；reference adoption 文件头未标 L2/L3
- **风险：** `test_r3g02AdversarialAudit_copiedOpenbbBlocks` 若失败，检查新文件是否含 `openbb`/`OpenBB` 字符串或拷贝模式

## Execute 铁律（主会话追加）

1. OpenBB：**只读**参考 `main.py` 的 widget 响应 JSON 字段名，在 QMD evidence bundle 中复现形状。
2. **禁止** 拷贝 agent loop、CORS、openai client、`from openbb_ai import *`。
3. kalshi/polymarket live：ResourceGuard + capped；仍走 probability_signal，禁止 factual_resolution。
4. web_search：维持 mock；勿接真实搜索 API 直至用户另行批准。
