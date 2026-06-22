# User Intervention Policy

Agent 自行解决 vs 必须问用户的边界（Loop Engineering P0–P4）。

## 必须问用户

1. 改变业务目标或验收标准
2. 启用真实生产数据、真实账号、付费 API、外部网络
3. 提高 ResourceGuard 限制
4. 新增大型依赖或更换核心架构
5. 前端最终信息架构、视觉、交互拍板
6. 将 deferred 风险改成 accepted risk
7. 需要用户业务授权或合规确认

## 不得问用户（agent 必须自行解决）

1. 去哪里找 docs/specs — 使用 `scripts/context_router.py` → `context_pack.json`
2. 某模块应读取哪些 contract — 查 `specs/context/authority_graph.yaml`
3. 某测试验证什么 — 查 `tests/test_catalog.yaml`
4. 如何生成 context_pack — `uv run python scripts/context_router.py --task <dir>`
5. 如何收集 evidence — 更新 `evidence_index.json` / `loop_manifest.json`
6. 如何运行普通本地/CI 验证 — `docs/ops/verification_commands.md`
7. 如何判断测试失败对应哪个契约 — `specs/verification/feature_verification_matrix.yaml` 与 `contract_coverage.yaml`

## 权威入口

| 用途       | 文件                                                  |
| ---------- | ----------------------------------------------------- |
| 上下文路由 | `context_pack.json`                                   |
| 测试语义   | `tests/test_catalog.yaml`                             |
| 功能验收   | `specs/verification/feature_verification_matrix.yaml` |
| 契约覆盖   | `specs/verification/contract_coverage.yaml`           |
| 证据索引   | `evidence_index.json`                                 |
| 项目地图   | `docs/generated/project_map.generated.json`           |
