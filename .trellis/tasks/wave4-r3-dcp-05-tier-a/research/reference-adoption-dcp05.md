# R3-DCP-05 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/wave4-r3-dcp-05-tier-a/`  
> **日期：** 2026-07-02  
> **方式：** 实读 `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目/**` 源码 + QMD 仓内 Wave 3 承接标注（**不进 L 梯**）  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；`backend/app/\*\*` 记为「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）。
4. EasyXT unified_data_interface = **forbidden**（silent fallback）。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                         | 等级                            | 采纳 / 禁止                                  | QMD 目标                                                     |
| ------------------------------------------------ | ------------------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| `OpenBB/.../fetcher.py` L36–85                   | **architecture_only → L3 对齐** | transform_query / extract / transform 三阶段 | `FetchRequest.start_time` + port live；**不拷贝 Fetcher 类** |
| `digital-oracle/.../bis.py` L54–66               | **L2**                          | `startPeriod` / `start_year` 来自 query      | `bis_port` + macro watermark → API 窗参数                    |
| `digital-oracle/.../bis.py` L46–52               | **L2**                          | Provider metadata + capability 声明          | registry/capabilities 文档对齐（非 runtime）                 |
| `EasyXT/.../auto_data_updater.py` L114–147       | **L2 概念 / forbidden runtime** | 交易日跳过、今日是否已更新                   | ops 文档；**禁止** schedule 线程                             |
| `EasyXT/.../auto_data_updater.py` L149–178       | **L2 概念**                     | 单标的日期窗 `start_date=end_date`           | 对齐 watermark 窗，不用 DataManager                          |
| `EasyXT/.../auto_data_updater.py` L31–32, L87–97 | **forbidden**                   | sys.path + DataManager 延迟 import           | 负向：禁止进入 sync                                          |
| `EasyXT/.../unified_data_interface.py` L172–244  | **forbidden**                   | DuckDB 不全 → QMT 在线回退                   | 测试：sync 路径不得 silent fallback                          |

---

## 2. 分参考深读

### 2.1 OpenBB Fetcher（architecture_only）

```36:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
class Fetcher(Generic[Q, R]):
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, ...)
        return cls.transform_data(query=query, data=data, **kwargs)
```

**L3 对齐：** watermark → `transform_query` 等价（QMD `spec.date_start` / `FetchRequest.start_time`）→ port extract → evidence bundle → staging → clean。

### 2.2 digital-oracle BIS（L2）

```54:66:参考项目/digital-oracle/digital_oracle/providers/bis.py
        payload = self.http_client.get_text(
            url,
            params={
                "startPeriod": query.start_year,
                "detail": "dataonly",
                "format": "csv",
            },
        )
```

**L2 拷改：** `read_observation_date_watermark` → 推导 `start_year` / `startPeriod`；写入仍用 QMD `official_macro_evidence_v1` + `axis_observation`。

### 2.3 EasyXT（概念 + forbidden）

- **L2 概念：** 增量 = 只拉窗口内数据（非全量重灌）。
- **forbidden：** 任何「本地无数据则换源」逻辑不得进入 `sync_*_incremental`。

---

## 3. 仓内承接（非参考 L 梯）

| 组件              | 路径                        | DCP-05 用法                         |
| ----------------- | --------------------------- | ----------------------------------- |
| Bar watermark     | `sync/watermark.py`         | baostock, mootdx, alpha_vantage bar |
| Fred macro 模板   | `ops/fred_incremental_*.py` | 宏观五源复制模式                    |
| Orchestrator      | `sync/orchestrator.py`      | L1 直接接                           |
| Product live gate | `product_live_gate.py`      | baostock + 全 Tier A live           |
| Clean 路由        | `clean_write_targets.py`    | ADR-028 扩域 + 新表                 |

---

## 4. Execute RED 前门禁

实读参考文件并落盘 `research/execute-reference-read-evidence.md`（Execute 阶段），路径与上表一致。

---

## 5. 采纳决策摘要

| 能力            | 参考等级                  | 决策                                      |
| --------------- | ------------------------- | ----------------------------------------- |
| 增量 API 窗参数 | digital-oracle bis **L2** | bis / world_bank 等 official API `start*` |
| Fetch 三阶段    | OpenBB **L3**             | 行为对齐，无 OpenBB 类型                  |
| 定时补数 / 回退 | EasyXT **forbidden**      | 仅文档与负向测                            |
| 编排 + clean    | 仓内 DCP-01/02            | 复制，不标 L1/L2/L3                       |
