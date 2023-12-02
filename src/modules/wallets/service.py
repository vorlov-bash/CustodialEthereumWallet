import logging

from eth_account.signers.local import LocalAccount
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from src.core.config import settings, w3_obj
from src.database.redis import redis
from src.database.utils import fetch_all, fetch_one
from src.modules.transactions.enums import GasPolicy
from src.modules.transactions.exceptions import NonceIsTooLow, ReplacementTransactionUnderpriced
from src.modules.transactions.service import (
    broadcast_transaction,
    create_raw_transaction,
    set_raw_transaction_to_failed,
)
from src.modules.wallets.enums import WalletStatus
from src.modules.wallets.exceptions import WalletWithIndexAlreadyExists
from src.modules.wallets.models import Wallet
from src.modules.wallets.utils import get_account_by_index

logger = logging.getLogger("root")


async def get_wallet_by_address(address: str) -> dict | None:
    wallet = await fetch_one(query=select(Wallet).where(Wallet.address == address))

    if wallet is None:
        return None

    wallet["account"] = get_account_by_index(
        xprivate_key=settings.ETH_WALLET_XPRIV.get_secret_value(), index=wallet["index"]
    )

    return wallet


async def get_wallet_by_external_id(external_id: str) -> dict | None:
    wallet = await fetch_one(query=select(Wallet).where(Wallet.external_id == external_id))

    if not wallet:
        return None

    wallet["account"] = get_account_by_index(
        xprivate_key=settings.ETH_WALLET_XPRIV.get_secret_value(), index=wallet["index"]
    )

    return wallet


async def get_wallet_by_index(index: int) -> dict | None:
    wallet = await fetch_one(query=select(Wallet).where(Wallet.index == index))

    if wallet is None:
        return None

    wallet["account"] = get_account_by_index(
        xprivate_key=settings.ETH_WALLET_XPRIV.get_secret_value(), index=wallet["index"]
    )

    return wallet


async def get_account_by_wallet(wallet: dict) -> LocalAccount:
    return get_account_by_index(
        xprivate_key=settings.ETH_WALLET_XPRIV.get_secret_value(), index=wallet["index"]
    )


async def get_wallets_list(active: bool | None = None) -> list[dict]:
    query = select(Wallet)

    if active is not None:
        query = query.where(
            Wallet.status == WalletStatus.ACTIVE if active else WalletStatus.INACTIVE
        )

    return await fetch_all(query=query)


async def get_last_wallet_index() -> int:
    query = select(Wallet).order_by(Wallet.index.desc()).limit(1)
    wallet = await fetch_one(query=query)
    if wallet is None:
        return 0
    return wallet["index"]


async def create_wallet(index: int | None = None, activate: bool = False) -> dict:
    if index is None:
        index = await get_last_wallet_index() + 1

    account = get_account_by_index(
        index=index, xprivate_key=settings.ETH_WALLET_XPRIV.get_secret_value()
    )

    try:
        query = (
            insert(Wallet)
            .values(
                index=index,
                address=account.address,
                status=WalletStatus.ACTIVE if activate else WalletStatus.INACTIVE,
            )
            .returning(Wallet)
        )
        new_wallet = await fetch_one(query=query)
    except IntegrityError as exc:
        raise WalletWithIndexAlreadyExists(index) from exc

    new_wallet["account"] = account
    return new_wallet


async def activate_wallet(disabled_wallet: dict) -> dict | None:
    if disabled_wallet["status"] == WalletStatus.ACTIVE:
        raise ValueError("Wallet is already inactive")

    query = (
        Wallet.update()
        .where(Wallet.address == disabled_wallet["address"])
        .values(status=WalletStatus.ACTIVE)
        .returning(Wallet)
    )
    return await fetch_one(query=query)


async def deactivate_wallet(active_wallet: dict) -> dict | None:
    if active_wallet["status"] == WalletStatus.INACTIVE:
        raise ValueError("Wallet is already inactive")

    if active_wallet["index"] == 0:
        raise ValueError("Main wallet cannot be deactivated")

    query = (
        Wallet.update()
        .where(Wallet.address == active_wallet["address"])
        .values(status=WalletStatus.INACTIVE)
        .returning(Wallet)
    )

    return await fetch_one(query=query)


async def get_deposit_list() -> list[dict]:
    query = select(Wallet).where(Wallet.status == WalletStatus.ACTIVE, Wallet.index > 0)
    return await fetch_all(query=query)


async def get_wallet_nonce(wallet: dict) -> int:
    cached_nonce = await redis.get(f"EWS:{wallet['external_id']}:nonce")

    if cached_nonce is not None:
        return int(cached_nonce)

    return await w3_obj.eth.get_transaction_count(wallet["address"])


async def update_wallet_nonce(wallet: dict, nonce: int) -> None:
    wallet_id = wallet["external_id"]
    await redis.set(f"EWS:{wallet_id}:nonce", nonce)


async def withdraw_from_wallet(
    wallet: dict,
    amount: str,
    to_address: str,
    speed: GasPolicy = GasPolicy.STANDARD,
) -> dict:
    # Get nonce of the wallet
    nonce = await get_wallet_nonce(wallet=wallet)

    raw_transaction = await create_raw_transaction(
        amount=amount,
        transaction_to=to_address,
        wallet=wallet,
        gas_policy=speed,
        nonce=nonce,
    )

    try:
        raw_transaction = await broadcast_transaction(raw_transaction=raw_transaction)
    except (NonceIsTooLow, ReplacementTransactionUnderpriced) as exc:
        await set_raw_transaction_to_failed(raw_transaction=raw_transaction)

        if isinstance(exc, NonceIsTooLow):
            nonce = await w3_obj.eth.get_transaction_count(wallet["address"])
        elif isinstance(exc, ReplacementTransactionUnderpriced):
            nonce = wallet["nonce"] + 1
        else:
            raise

        logger.warning(
            f"Nonce ({wallet['nonce']} is too low for wallet {wallet['address']}."
            f" Retrying with {nonce}"
        )
        await update_wallet_nonce(wallet=wallet, nonce=nonce)
        return await withdraw_from_wallet(
            wallet=wallet, amount=amount, to_address=to_address, speed=speed
        )

    await update_wallet_nonce(wallet=wallet, nonce=raw_transaction["nonce"] + 1)

    return raw_transaction
