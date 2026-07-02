# R3-DCP-10 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/`  
> **日期：** 2026-07-02  
> **方式：** 实读 `参考项目/**` 源码 + QMD 仓内 Layer5/evidence 承接标注（**不进 L 梯**）  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；`backend/app/layer5_evidence/` 等记为「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）。
4. EasyXT `unified_data_interface` = **forbidden**（silent fallback）。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                        | 等级                            | 采纳 / 禁止                           | QMD DCP-10 目标                                                    |
| ----------------------------------------------- | ------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `OpenBB/.../fetcher.py` L36–85                  | **architecture_only → L3 对齐** | transform_query → extract → transform | fetch bundle 三阶段；**不拷贝 Fetcher 类**                         |
| `OpenBB/.../fetcher.py` L86–120                 | **architecture_only**           | `fetch_data` 统一入口 + credentials   | 对齐 `DataSourceService.fetch_payload` 单入口                      |
| `digital-oracle/.../bis.py` L54–66              | **L2**                          | HTTP 响应 + `content_hash` 指纹       | 宏观源已 DCP-05；本票借鉴 **fetch_id + hash 必填** 纪律            |
| `digital-oracle/.../bis.py` L46–52              | **L2 概念**                     | Provider metadata 声明                | `schema_version` → `schema_hash` 映射（仓内 `evidence_bundle.py`） |
| `EasyXT/.../unified_data_interface.py` L172–244 | **forbidden**                   | DuckDB 空 → 在线回退                  | Layer5 **禁止**无 provenance 的 clean 行冒充事实                   |
| `EasyXT/.../auto_data_updater.py` L149–178      | **L2 概念**                     | 单标的日期窗增量                      | 对齐 mootdx watermark 窗（仓内 DCP-05 已承接）                     |

---

## 2. 分参考深读

### 2.1 OpenBB Fetcher（architecture_only · provenance 三阶段）

**读什么：** `transform_query` → `extract_data` → `transform_data`；fetch 结果带 provider metadata。

**QMD 决策：** mootdx port 已在 extract 后 `finalize_bundle` 写入三哈希。Layer5 绑定发生在 **transform 之后**（读 bundle，非重 fetch）。禁止拷贝 OpenBB `Fetcher` 类。

### 2.2 digital-oracle BIS（L2 · hash 纪律）

**读什么：** API 拉取后必须有确定性的 content 指纹；缺失则 fail-closed。

**QMD 决策：** 对齐 `read_cn_market_evidence_bundle` — 缺 `source_fetch_id` 或 `content_hash` 即 `CnMarketEvidenceError`。Execute 扩展 **schema_hash** 到 `source_dataset_ids`。

### 2.3 EasyXT unified_data_interface（forbidden）

**读什么：** 本地无数据则切换在线源，provenance 断裂。

**QMD 决策：** Layer5 e2e **必须**从同一次 fetch 的 bundle 取 provenance；禁止「clean 有行但 fetch_id 是 staged 占位符」。

---

## 3. 仓内承接（非参考 L 梯）

| 组件                 | 路径                                         | DCP-10 用法                                    |
| -------------------- | -------------------------------------------- | ---------------------------------------------- |
| Evidence bundle SSOT | `datasources/normalizers/evidence_bundle.py` | `finalize_bundle` · `bundle_layer5_provenance` |
| CN market normalizer | `datasources/normalizers/cn_market.py`       | `cn_market_bundle_layer5_provenance`           |
| Mootdx port          | `fetch_ports/mootdx_port.py`                 | P0 fetch 源                                    |
| Incremental ops      | `ops/mootdx_incremental_run.py`              | clean 写封装                                   |
| Layer5 foundation    | `layer5_evidence/foundation.py`              | factual_source 校验                            |
| Layer5 lineage       | `layer5_evidence/lineage.py`                 | snapshot_lineage 对齐                          |
| Raw store            | `storage/raw_store.py`                       | content_hash 先例                              |
| DCP-05 e2e           | `tests/test_mootdx_incremental_e2e.py`       | replay 种子                                    |
| Staged 负向          | `tests/test_layer5_evidence_foundation.py`   | STAGED_PROVENANCE 对比                         |

---

## 4. Provenance 字段映射表（Execute SSOT）

| Fetch bundle 字段 | 类型         | Layer5 `SourceProvenance`                                   | Layer5 lineage          | 备注                       |
| ----------------- | ------------ | ----------------------------------------------------------- | ----------------------- | -------------------------- |
| `source_fetch_id` | string       | `source_fetch_ids[0]`                                       | `source_fetch_ids`      | job run_id / port uuid     |
| `content_hash`    | string (hex) | `source_content_hashes[0]`                                  | `source_content_hashes` | SHA-256 canonical bundle   |
| `schema_hash`     | string (hex) | `source_dataset_ids` 含 `schema:{hash}@{version}`           | `source_dataset_ids`    | ADR-031；非 lineage 独立列 |
| `schema_version`  | string       | `source_dataset_ids` 含 `version:{name}`                    | 同上                    | 例 `cn_market_evidence_v1` |
| `source_id`       | string       | `source_dataset_ids` 含 `clean:security_bar_1d@{source_id}` | 同上                    | 绑 clean 表 + 源           |
| `data_domain`     | string       | `source_dataset_ids` 含 `domain:cn_equity_daily_bar`        | 同上                    | P0 竖切域                  |

**Execute 断言：** e2e 中 foundation record 的 provenance 三件套 **等于** 同 run 的 fetch bundle 映射结果（非 `fetch-staged-001`）。

---

## 5. Execute RED 前门禁

实读参考文件并落盘 `research/execute-reference-read-evidence.md`（Execute 阶段），路径与 §1 表一致。

---

## 6. 采纳决策摘要

| 能力                    | 参考等级              | 决策                             |
| ----------------------- | --------------------- | -------------------------------- |
| Fetch 三阶段 + metadata | OpenBB **L3 对齐**    | 已有 port；Layer5 读 bundle 尾段 |
| hash 必填 fail-closed   | digital-oracle **L2** | 扩展 schema_hash 到 dataset ids  |
| 无数据换源              | EasyXT **forbidden**  | e2e 负向：staging 占位拒收       |
| clean→Layer5 桥         | 仓内 023A + cn_market | 新增 provenance helper + e2e     |
