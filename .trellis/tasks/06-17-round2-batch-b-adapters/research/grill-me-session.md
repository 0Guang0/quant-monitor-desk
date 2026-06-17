# Phase 3 — grill-me 决策树（Batch B）

> Skill: `grill-me` · 仓库可答项已自检；以下为已收敛 Q&A（等效逐问记录）

---

## Q1：五个 adapter 是否都要写真实 raw 文件，还是继续 Batch A 的「字段可携带」？

**推荐：** SUCCESS 路径 **必须** 调用 `RawStore.save()` 写入 `data/raw/{source}/{domain}/{as_of}/` 真实文件；`FetchResult.raw_file_paths` 与磁盘一致。

**理由：** Batch A 豁免在 DECISIONS §5 / MASTER §3.2；Batch B 任务 013 明确偿还 contract rule 2。

**结论：** ✅ 采纳

---

## Q2：skeleton 是否调用 FileRegistry.register？

**推荐：** **是（可选注入）** — SUCCESS 后 `file_registry.register(saved)`；`FetchResult.raw_file_paths[0]` 须与 `file_registry.local_path` 一致（偿还 Batch A Beta §6）。测试通过 `file_registry_stack` fixture 注入；**adapters 包禁止 import WriteManager**。

**结论：** ✅ 采纳（v1.1 修订，取代 v1.0「本批不做」）

---

## Q3：QMT 本地客户端不可用时的 skeleton 行为？

**推荐：** 默认 `StubFetchPort` 返回 SUCCESS（测试/CI）；注入 `UnavailableClientPort` 时返回 `AUTH_FAILED` + `error_message`，仍经 `fetch()` 写 fetch_log。

**结论：** ✅ 采纳

---

## Q4：是否新增运行时依赖（akshare/baostock/yfinance SDK）？

**推荐：** **不新增**。DECISIONS §6 继承；skeleton 仅协议 + stub port。

**结论：** ✅ 采纳

---

## Q5：NOT_PUBLISHED_YET 是否纳入 Batch B？

**推荐：** **条件** — `CninfoAdapter` + 单测覆盖；不扩展全局 `FetchResult.status` Literal 除非 contract md 同步更新（本批 **不** 扩 7 态；用 `EMPTY_RESPONSE` + 明确 error_message 或 skeleton 内 TODO 注释指向 Batch C）。

**修订（5d + 对抗审计 F02）：** 保持 7 态 Literal；cninfo `UnpublishedPort` → `EMPTY_RESPONSE` + error_message；§8.4 单测 AC-10。**不**扩展 contract 第 8 态。

**结论：** ✅ 采纳（v1.1）

---

## Q6：factory 是否本批交付？

**推荐：** **是** — `create_adapter(source_id, registry, data_root)` 供 Batch D；未知 source_id → `KeyError`。

**结论：** ✅ 采纳
