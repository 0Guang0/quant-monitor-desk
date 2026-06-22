"""Futures main-contract roll detection — explicit events, no silent switch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.app.layer2_sensors.models import MainContractRollEvent


@dataclass(frozen=True)
class ContractLiquidity:
    contract_code: str
    trade_date: date
    volume: float
    open_interest: float


class FuturesRollError(ValueError):
    """Invalid futures roll inputs."""


class FuturesRollHandler:
    """Detect main-contract switch via volume/OI dominance (staged rule)."""

    def detect_roll(
        self,
        *,
        asset_id: str,
        roll_date: date,
        incumbent: ContractLiquidity,
        challenger: ContractLiquidity,
        roll_rule: str = "volume_oi_switch",
    ) -> MainContractRollEvent | None:
        if incumbent.contract_code == challenger.contract_code:
            return None
        if roll_rule != "volume_oi_switch":
            raise FuturesRollError(f"unsupported roll_rule: {roll_rule!r}")

        challenger_dominates = (
            challenger.volume > incumbent.volume
            and challenger.open_interest >= incumbent.open_interest
        )
        if not challenger_dominates:
            return None

        return MainContractRollEvent(
            roll_event=True,
            asset_id=asset_id,
            old_contract=incumbent.contract_code,
            new_contract=challenger.contract_code,
            roll_reason="volume_oi_switch",
            roll_date=roll_date,
            volume_old=incumbent.volume,
            volume_new=challenger.volume,
            open_interest_old=incumbent.open_interest,
            open_interest_new=challenger.open_interest,
        )
