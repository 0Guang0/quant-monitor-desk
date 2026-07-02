# 016E — Define Platform Source Matrix and qmt_xqshare

## Scope

Design/spec only. Do not change code or enable any QMT source.

## Inputs

- `specs/contracts/platform_source_matrix.yaml`
- `docs/ops/qmt_xqshare_setup.md`
- `specs/datasource_registry/source_capabilities.yaml`

## Required design updates

1. Define platform × source support matrix.
2. Keep `qmt_xtdata` Windows-local and disabled by default.
3. Introduce `qmt_xqshare` as optional remote source, also disabled by default.
4. Require env and explicit user authorization before schedulable.
5. Prohibit auto-login, captcha handling, and remote probing.

## Future implementation tasks

- Add qmt_xqshare source to `source_registry.yaml` only after approval.
- Add qmt_xqshare skeleton only after approval.
- Add platform matrix tests.

## Acceptance commands

```bash
python -m pytest tests/test_platform_source_matrix.py tests/test_source_registry.py tests/test_adapter_skeletons.py -q
```

## Residual risk

No real xqshare connectivity is verified in Phase A. That is intentional because no production/remote authorization has been granted.
