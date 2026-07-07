# QMT / xtdata Adapter 模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 11 章

# 11. QMT / xtdata Adapter

不要让业务层直接调用 QMT API。必须封装适配层。

```python
class QMTDataAdapter:
    def ensure_history_cached(self, stock_code: str, period: str, start_time: str | None, end_time: str | None):
        ...

    def fetch_bars(self, stock_codes: list[str], period: str, start_time: str | None = None, end_time: str | None = None, count: int = -1, adjust_type: str = "none"):
        ...

    def fetch_latest_quote(self, stock_codes: list[str]):
        ...

    def subscribe_realtime(self, stock_codes: list[str], callback):
        ...
```

适配层内部可以根据版本和券商环境选择：

```text
download_history_data
download_history_data2
get_market_data
get_market_data_ex
get_local_data
subscribe_quote
subscribe_whole_quote
```

不要把 `get_market_data_ex` 的某种用法写死到业务层。

---

## 用户决策补充：第一版默认禁用

落实 D-11：QMT / miniQMT adapter 第一版必须默认禁用。启用前必须由用户确认本机 QMT 安装路径、账号授权、行情权限与本地运行状态。没有用户确认时，QMT 只能作为 fallback candidate，不得自动尝试连接。

---

## qmt_xqshare 可选远程源边界

`qmt_xqshare` 只作为未来可选远程 QMT 源设计，默认禁用，不阻塞 Round3。启用前必须满足：

```text
用户明确授权
XQSHARE_REMOTE_HOST
XQSHARE_REMOTE_PORT
platform_source_matrix 允许
SourceRoutePlan route_status=READY
```

禁止：

```text
自动探测远程端口
自动登录 QMT
处理验证码
缺配置时 silent fallback
把 qmt_xqshare 设为默认启用源
```

权威文件：`docs/ops/qmt_xqshare_setup.md`、`specs/contracts/platform_source_matrix.yaml`、`specs/contracts/source_route_contract.yaml`、`specs/datasource_registry/source_capabilities.yaml`。

Phase A 不修改 `source_registry.yaml`、不新增 qmt_xqshare adapter 代码、不新增依赖。
