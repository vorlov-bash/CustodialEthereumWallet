from typing import Annotated

from fastapi import Depends

from src.modules.wallets.enums import WalletStatus
from src.modules.wallets.exceptions import WalletIsNotActive, WalletNotFound
from src.modules.wallets.service import get_wallet_by_external_id


async def get_wallet(external_id: str) -> dict:
    wallet = await get_wallet_by_external_id(external_id=external_id)

    if wallet is None:
        raise WalletNotFound(f"Wallet with external_id={external_id} not found")

    return wallet


async def active_wallet(wallet: Annotated[dict, Depends(get_wallet)]) -> dict:
    if wallet["status"] == WalletStatus.ACTIVE:
        return wallet

    raise WalletIsNotActive(external_id=wallet["external_id"])
