# OpenAPI Contract v1

> 权威实现文件：`docs/modules/fastapi_backend.md`。  
> 本文件是后续自动生成或人工校验 OpenAPI 的落点，不是临时文件。

## 通用响应 Envelope

所有接口必须返回：

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "as_of_timestamp": "ISO8601 or null",
    "generated_at": "ISO8601",
    "data_lag_days": 0,
    "quality_flags": [],
    "source_used": "string or null",
    "page": 1,
    "page_size": 200,
    "total": 1000
  },
  "errors": []
}
```

## 必须实现的路由组

```text
/api/market
/api/layer1
/api/layer2
/api/layer3
/api/layer4
/api/layer5
/api/evidence
/api/reports
/api/data-health
/api/agent-tools
```

## 禁止事项

```text
不允许 router 直接拼 SQL。
不允许 API 请求直接写 clean table。
不允许无分页返回大历史。
不允许 Agent tool 返回无来源、无质量标记的数据。
```
