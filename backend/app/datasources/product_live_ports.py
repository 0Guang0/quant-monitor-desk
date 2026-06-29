"""Product live fetch port factory — ProductLiveGate + LiveTierRouter (R3H-08).

Reference cite (08C arch): OpenBB fetcher.py L74-85 transform_query→extract→transform;
BIS L2: digital-oracle bis.py L46-66 CSV URL/parse; base.py L22-25 Provider metadata (L3).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, FetchPort, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.live_tier_router import LiveTier, resolve_live_tier
from backend.app.datasources.product_live_gate import (
    ProductLiveGateError,
    assert_product_live_allowed,
)
from backend.app.datasources.service import DataSourceService

# 08C macro/market primary (S08-01)
TIER_A_08C_SOURCES = frozenset(
    {
        "fred",
        "us_treasury",
        "sec_edgar",
        "cftc_cot",
        "bis",
        "world_bank",
        "alpha_vantage",
        "deribit",
    }
)

# 08A CN primary (S08-02)
TIER_A_08A_SOURCES = frozenset({"baostock", "cninfo", "mootdx"})

# 08B validation_only (S08-03)
TIER_B_08B_SOURCES = frozenset(
    {
        "yahoo_finance",
        "akshare",
        "stooq",
        "coingecko",
        "eastmoney",
        "sina_finance",
        "tdx_pytdx",
        "ths_ifind",
        "qmt_xtdata",
        "qmt_xqshare",
    }
)

# 08D Tier C probability (S08-04)
TIER_C_08D_SOURCES = frozenset({"kalshi", "polymarket"})


class ProductLiveTierError(RuntimeError):
    """Product live rejected for tier/policy mismatch."""


@dataclass(frozen=True)
class ProductLiveGatedPort:
    """Wrap any FetchPort with ProductLiveGate fail-closed check on each fetch."""

    source_id: str
    inner: FetchPort

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        assert_product_live_allowed(source_id=self.source_id, operation="fetch")
        return self.inner.fetch_payload(req)


def _gate_port(source_id: str, port: FetchPort) -> FetchPort:
    return ProductLiveGatedPort(source_id=source_id, inner=port)


def _assert_expected_tier(source_id: str, *, expected: LiveTier) -> None:
    tier = resolve_live_tier(source_id)
    if tier != expected:
        raise ProductLiveTierError(
            f"source {source_id!r} tier {tier} != expected {expected} for product live slice"
        )


def _fred_port():
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port

    return create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)


def _us_treasury_port(data_domain: str):
    from backend.app.datasources.fetch_ports.us_treasury_port import create_us_treasury_fetch_port

    domain = data_domain if data_domain in {"us_treasury_yield_curve", "inflation_expectation"} else "us_treasury_yield_curve"
    return create_us_treasury_fetch_port(
        tenors=("10Y",), max_rows=3, data_domain=domain, use_mock=False
    )


def _sec_edgar_port(data_domain: str):
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port

    domain = data_domain if data_domain in {"us_filings", "us_insider_form4"} else "us_filings"
    return create_sec_edgar_fetch_port(ciks=("0000320193",), max_filings=3, data_domain=domain, use_mock=False)


def _cftc_cot_port():
    from backend.app.datasources.fetch_ports.cftc_cot_port import create_cftc_cot_fetch_port

    return create_cftc_cot_fetch_port(markets=("088691",), max_rows=3, use_mock=False)


def _bis_port(data_domain: str):
    from backend.app.datasources.fetch_ports.bis_port import create_bis_fetch_port

    domain = data_domain if data_domain in {"central_bank_policy", "credit_gap"} else "central_bank_policy"
    return create_bis_fetch_port(countries=("US",), max_rows=3, data_domain=domain, use_mock=False)


def _world_bank_port(data_domain: str):
    from backend.app.datasources.fetch_ports.world_bank_port import create_world_bank_fetch_port

    domain = data_domain if data_domain in {"development_indicator", "global_macro_reference"} else "development_indicator"
    return create_world_bank_fetch_port(
        countries=("US",),
        indicators=("NY.GDP.MKTP.CD",),
        max_rows=3,
        data_domain=domain,
        use_mock=False,
    )


def _alpha_vantage_port():
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port

    return create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=False)


def _deribit_port():
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port

    return create_deribit_fetch_port(
        instruments=("BTC-PERPETUAL",), max_surface_rows=3, use_mock=False
    )


def _baostock_port():
    from backend.app.datasources.fetch_ports.baostock_port import create_baostock_fetch_port

    return create_baostock_fetch_port(symbols=("sh.600519",), max_rows=3, use_mock=False)


def _cninfo_port():
    from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port

    return create_cninfo_fetch_port(symbols=("sh.600519",), max_rows=3, use_mock=False)


def _mootdx_port():
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port

    return create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=3, use_mock=False)


def _yahoo_finance_port():
    from backend.app.datasources.fetch_ports.yahoo_finance_port import create_yahoo_finance_fetch_port

    return create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3)


def _kalshi_port():
    from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port

    return create_kalshi_fetch_port(market_tickers=("KXHIGHNY-24",), max_markets=1, use_mock=False)


def _polymarket_port():
    from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port

    return create_polymarket_fetch_port(
        market_slugs=("will-fed-cut-rates-2024",), max_markets=1, use_mock=False
    )


_08C_FACTORIES: dict[str, Callable[[str], FetchPort]] = {
    "fred": lambda _d: _fred_port(),
    "us_treasury": _us_treasury_port,
    "sec_edgar": _sec_edgar_port,
    "cftc_cot": lambda _d: _cftc_cot_port(),
    "bis": _bis_port,
    "world_bank": _world_bank_port,
    "alpha_vantage": lambda _d: _alpha_vantage_port(),
    "deribit": lambda _d: _deribit_port(),
}

_08A_FACTORIES: dict[str, Callable[[str], FetchPort]] = {
    "baostock": lambda _d: _baostock_port(),
    "cninfo": lambda _d: _cninfo_port(),
    "mootdx": lambda _d: _mootdx_port(),
}

_08B_FACTORIES: dict[str, Callable[[str], FetchPort]] = {
    "yahoo_finance": lambda _d: _yahoo_finance_port(),
}

_08D_FACTORIES: dict[str, Callable[[str], FetchPort]] = {
    "kalshi": lambda _d: _kalshi_port(),
    "polymarket": lambda _d: _polymarket_port(),
}


def create_product_live_fetch_port(
    *,
    source_id: str,
    data_domain: str,
    operation: str = "fetch",
) -> FetchPort:
    """Build env-gated product live port for supported LIVE-PROD-24 sources."""
    assert_product_live_allowed(source_id=source_id, operation=operation)
    tier = resolve_live_tier(source_id)

    if source_id in TIER_A_08C_SOURCES:
        _assert_expected_tier(source_id, expected="A")
        factory = _08C_FACTORIES.get(source_id)
    elif source_id in TIER_A_08A_SOURCES:
        _assert_expected_tier(source_id, expected="A")
        factory = _08A_FACTORIES.get(source_id)
    elif source_id in TIER_B_08B_SOURCES:
        _assert_expected_tier(source_id, expected="B")
        factory = _08B_FACTORIES.get(source_id)
        if factory is None:
            mod_name = f"{source_id}_port"
            mod = __import__(
                f"backend.app.datasources.fetch_ports.{mod_name}",
                fromlist=[f"create_{source_id}_fetch_port"],
            )
            create_fn = getattr(mod, f"create_{source_id}_fetch_port")
            kwargs: dict[str, Any] = {"max_rows": 3}
            if source_id in {"coingecko"}:
                kwargs = {"max_assets": 3}
            elif source_id in {"ths_ifind"}:
                kwargs = {"concepts": ("新能源",), "max_rows": 3}
            elif source_id in {"akshare", "baostock", "eastmoney", "sina_finance", "stooq", "tdx_pytdx"}:
                kwargs["symbols"] = ("sh.600519",) if source_id != "stooq" else ("AAPL.US",)
            elif source_id in {"qmt_xtdata", "qmt_xqshare"}:
                kwargs["symbols"] = ("000001.SZ",)
            else:
                kwargs["symbols"] = ("AAPL",)
            return _gate_port(source_id, create_fn(**kwargs))
    elif source_id in TIER_C_08D_SOURCES:
        _assert_expected_tier(source_id, expected="C")
        factory = _08D_FACTORIES.get(source_id)
    else:
        raise ProductLiveTierError(f"product live not enabled for {source_id!r}")

    if factory is None:
        raise ProductLiveTierError(f"no product live factory for {source_id!r} tier={tier}")
    return _gate_port(source_id, factory(data_domain))


class _ProductLiveFileRegistryPlaceholder:
    """ponytail: production fetch DI placeholder; upgrade = FileRegistry + WriteManager path."""


def build_product_live_service(
    *,
    source_id: str,
    data_domain: str,
    data_root: Path,
    operation: str = "fetch",
) -> DataSourceService:
    """Construct DataSourceService for product live gold path (staged_fixture_mode=False)."""
    port = create_product_live_fetch_port(
        source_id=source_id,
        data_domain=data_domain,
        operation=operation,
    )
    root = Path(data_root)

    def _file_registry() -> _ProductLiveFileRegistryPlaceholder:
        return _ProductLiveFileRegistryPlaceholder()

    return DataSourceService(
        data_root=root,
        fetch_port=port,
        file_registry_factory=_file_registry,
        staged_fixture_mode=False,
    )


__all__ = [
    "ProductLiveGatedPort",
    "ProductLiveGateError",
    "ProductLiveTierError",
    "TIER_A_08A_SOURCES",
    "TIER_A_08C_SOURCES",
    "TIER_B_08B_SOURCES",
    "TIER_C_08D_SOURCES",
    "build_product_live_service",
    "create_product_live_fetch_port",
]
