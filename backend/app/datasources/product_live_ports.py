"""Product live fetch port factory — ProductLiveGate + LiveTierRouter (R3H-08).

Reference cite (08C arch): OpenBB fetcher.py L74-85 transform_query→extract→transform;
BIS L2: digital-oracle bis.py L46-66 CSV URL/parse; base.py L22-25 Provider metadata (L3).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort
from backend.app.datasources.live_prod_source_tiers import (
    INCREMENTAL_GOLD_PATH_SOURCE_IDS,
    TIER_B_SOURCES,
    TIER_C_SOURCES,
    resolve_prod_source_tier,
)
from backend.app.datasources.product_live_gate import (
    ProductLiveGateError,
    assert_product_live_allowed,
)
from backend.app.datasources.service import DataSourceService

SOURCE_LIVE_DEFAULTS: dict[str, dict[str, Any]] = {
    "fred": {"series_ids": ("DGS10",), "max_rows": 3, "use_mock": False},
    "us_treasury": {"tenors": ("10Y",), "max_rows": 3, "use_mock": False},
    "sec_edgar": {"ciks": ("0000320193",), "max_filings": 3, "use_mock": False},
    "cftc_cot": {"markets": ("088691",), "max_rows": 3, "use_mock": False},
    "bis": {"countries": ("US",), "max_rows": 3, "use_mock": False},
    "world_bank": {
        "countries": ("US",),
        "indicators": ("NY.GDP.MKTP.CD",),
        "max_rows": 3,
        "use_mock": False,
    },
    "alpha_vantage": {"symbols": ("AAPL",), "max_rows": 3, "use_mock": False},
    "deribit": {"instruments": ("BTC-PERPETUAL",), "max_surface_rows": 3, "use_mock": False},
    "baostock": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "cninfo": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "mootdx": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "yahoo_finance": {"symbols": ("AAPL",), "max_rows": 3, "use_mock": False},
    "akshare": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "stooq": {"symbols": ("AAPL.US",), "max_rows": 3, "use_mock": False},
    "coingecko": {"asset_ids": ("bitcoin",), "max_assets": 3, "use_mock": False},
    "eastmoney": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "sina_finance": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": False},
    "tdx_pytdx": {"symbols": ("sh.600519",), "max_rows": 3, "use_mock": True},
    "ths_ifind": {"concepts": ("新能源",), "max_rows": 3},
    "qmt_xtdata": {"symbols": ("000001.SZ",), "max_rows": 3},
    "qmt_xqshare": {"symbols": ("000001.SZ",), "max_rows": 3},
    "kalshi": {"market_tickers": ("KXFED-27APR-T4.25",), "max_markets": 1, "use_mock": False},
    "polymarket": {
        "market_slugs": ("new-rhianna-album-before-gta-vi-926",),
        "max_markets": 1,
        "use_mock": False,
    },
}

_DOMAIN_KWARGS: dict[str, dict[str, tuple[str, ...]]] = {
    "us_treasury": {
        "data_domain": ("us_treasury_yield_curve", "inflation_expectation"),
    },
    "sec_edgar": {"data_domain": ("us_filings", "us_insider_form4")},
    "bis": {"data_domain": ("central_bank_policy", "credit_gap")},
    "world_bank": {"data_domain": ("development_indicator", "global_macro_reference")},
}


class ProductLiveTierError(RuntimeError):
    """Product live rejected for tier/policy mismatch."""


class _ProductLiveFileRegistryPlaceholder:
    """ponytail: production fetch DI placeholder; upgrade = FileRegistry + WriteManager path."""


def _import_create_port(source_id: str) -> Callable[..., FetchPort]:
    mod = importlib.import_module(f"backend.app.datasources.fetch_ports.{source_id}_port")
    return getattr(mod, f"create_{source_id}_fetch_port")


def _kwargs_for_source(source_id: str, data_domain: str) -> dict[str, Any]:
    if source_id not in SOURCE_LIVE_DEFAULTS:
        raise ProductLiveTierError(f"product live not enabled for {source_id!r}")
    kwargs = dict(SOURCE_LIVE_DEFAULTS[source_id])
    domain_opts = _DOMAIN_KWARGS.get(source_id, {}).get("data_domain")
    if domain_opts is not None:
        kwargs["data_domain"] = data_domain if data_domain in domain_opts else domain_opts[0]
    return kwargs


def create_product_live_fetch_port(
    *,
    source_id: str,
    data_domain: str,
    operation: str = "fetch",
) -> FetchPort:
    """Build env-gated product live port for supported LIVE-PROD-24 sources."""
    assert_product_live_allowed(source_id=source_id, operation=operation)
    resolve_prod_source_tier(source_id)
    kwargs = _kwargs_for_source(source_id, data_domain)
    return _import_create_port(source_id)(**kwargs)


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
        product_live_mode=True,
    )


__all__ = [
    "ProductLiveGateError",
    "ProductLiveTierError",
    "SOURCE_LIVE_DEFAULTS",
    "INCREMENTAL_GOLD_PATH_SOURCE_IDS",
    "TIER_B_SOURCES",
    "TIER_C_SOURCES",
    "build_product_live_service",
    "create_product_live_fetch_port",
]
