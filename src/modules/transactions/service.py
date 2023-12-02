import logging

import web3.exceptions
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes
from sqlalchemy import insert, select, update
from web3 import Web3
from web3.types import TxData

from src.core.config import settings, w3_obj
from src.database.utils import execute, fetch_all, fetch_one
from src.modules.transactions.enums import (
    RAW_SYSTEM_TX_STATUS_MAPPING,
    GasPolicy,
    RawTransactionStatus,
    TransactionDirection,
    TransactionStatus,
)
from src.modules.transactions.exceptions import NonceIsTooLow, ReplacementTransactionUnderpriced
from src.modules.transactions.models import RawTransaction, SystemTransaction
from src.modules.transactions.utils import get_gas_from_history

logger = logging.getLogger("root")


async def get_gas_price_by_policy(gas_policy: GasPolicy) -> int:
    min_, avg, max_ = await get_gas_from_history(w3_obj)

    policies = {
        GasPolicy.STANDARD: min_,
        GasPolicy.FAST: avg,
        GasPolicy.FASTEST: max_,
    }

    return policies[gas_policy]


async def get_raw_transaction_by_id(obj_id: int) -> dict:
    query = select(RawTransaction).where(RawTransaction.id == obj_id)
    return await fetch_one(query)


async def get_system_transactions_by_raw_tx(raw_transaction: dict) -> list[dict]:
    query = select(SystemTransaction).where(SystemTransaction.origin_id == raw_transaction["id"])
    return await fetch_all(query)


async def get_raw_transaction_by_external_id(external_id: str) -> dict:
    query = select(RawTransaction).where(RawTransaction.external_id == external_id)
    return await fetch_one(query)


async def get_raw_transaction_by_hash(tx_hash: str) -> dict:
    query = select(RawTransaction).where(RawTransaction.tx_hash == tx_hash)
    return await fetch_one(query)


async def get_raw_transactions_by_status(statuses: list[RawTransactionStatus]) -> list[dict]:
    query = select(RawTransaction).where(RawTransaction.status.in_(statuses))
    return await fetch_all(query)


async def get_blocking_raw_transaction(wallet: dict) -> dict:
    query = select(RawTransaction).where(
        RawTransaction.status == RawTransactionStatus.BROADCASTED,
        RawTransaction.tx_from == wallet["address"],
    )
    return await fetch_one(query)


async def get_blockchain_transaction_from_raw(raw_transaction: dict) -> TxData:
    try:
        return await w3_obj.eth.get_transaction(raw_transaction["tx_hash"])
    except web3.exceptions.TransactionNotFound as exc:
        # Set raw and system transactions to failed
        await set_raw_transaction_to_failed(raw_transaction)
        raise ValueError(
            f"Transaction {raw_transaction['tx_hash']} not found on blockchain"
        ) from exc


async def confirm_raw_transaction_by_blockchain(
    raw_transaction: dict,
    confirmations: int,
    blockchain_tx_data: TxData | None = None,
) -> dict:
    if raw_transaction["status"] == RawTransactionStatus.BROADCASTED:
        # Transaction is on broadcast status. This means that
        # it is the first time we are confirming this transaction

        if not blockchain_tx_data:
            blockchain_tx_data = await get_blockchain_transaction_from_raw(raw_transaction)

        tx_receipt = await w3_obj.eth.get_transaction_receipt(blockchain_tx_data["hash"])

        updatable = {
            "status": RawTransactionStatus.PENDING,
            "tx_hash": blockchain_tx_data["hash"].hex(),
            "tx_from": blockchain_tx_data["from"],
            "tx_to": blockchain_tx_data["to"],
            "tx_value": blockchain_tx_data["value"],
            "tx_fee": tx_receipt["gasUsed"] * tx_receipt["effectiveGasPrice"],
            "tx_input": blockchain_tx_data["input"].hex(),
            "gas_used": tx_receipt["gasUsed"],
            "block_number": blockchain_tx_data["blockNumber"],
            "confirmation_count": raw_transaction["confirmation_count"] + confirmations,
        }
    else:
        # Transaction is on pending status
        updatable = {
            "confirmation_count": raw_transaction["confirmation_count"] + confirmations,
        }

        if (
            raw_transaction["confirmation_count"] + confirmations
            >= raw_transaction["confirmation_need"]
        ):
            # Check if transaction is still available on blockchain
            await get_blockchain_transaction_from_raw(raw_transaction)

    if (
        raw_transaction["confirmation_count"] + confirmations
        >= raw_transaction["confirmation_need"]
    ):
        updatable["status"] = RawTransactionStatus.CONFIRMED

    query = (
        update(RawTransaction)
        .where(RawTransaction.id == raw_transaction["id"])
        .values(updatable)
        .returning(RawTransaction)
    )

    result = await fetch_one(query)

    # If status was changed we need to change status of system transactions
    if updatable.get("status"):
        system_transaction_status = RAW_SYSTEM_TX_STATUS_MAPPING[updatable["status"]]
        query = (
            update(SystemTransaction)
            .where(SystemTransaction.origin_id == raw_transaction["id"])
            .values(
                {
                    "status": system_transaction_status,
                }
            )
        )
        await execute(query)

    logger.debug(
        f"Raw transaction {raw_transaction['tx_hash']} was confirmed: "
        f"{raw_transaction['confirmation_count'] + confirmations}/"
        f"{raw_transaction['confirmation_need']}",
        extra={"tx_hash": raw_transaction["tx_hash"]},
    )

    return result


async def update_raw_transaction_status(
    raw_transaction: dict,
    status: RawTransactionStatus,
):
    system_transaction_status = RAW_SYSTEM_TX_STATUS_MAPPING[status]

    queries = [
        (
            update(RawTransaction)
            .where(RawTransaction.id == raw_transaction["id"])
            .values(
                {
                    "status": status,
                }
            )
            .returning(RawTransaction)
        ),
        (
            update(SystemTransaction)
            .where(SystemTransaction.origin_id == raw_transaction["id"])
            .values(
                {
                    "status": system_transaction_status,
                }
            )
        ),
    ]

    await execute(*queries)

    return await get_raw_transaction_by_hash(raw_transaction["tx_hash"])


async def set_raw_transaction_to_failed(raw_transaction: dict) -> dict:
    query = (
        update(RawTransaction)
        .where(RawTransaction.id == raw_transaction["id"])
        .values(
            {
                "status": RawTransactionStatus.FAILED,
            }
        )
        .returning(RawTransaction)
    )

    raw_transaction = {**await fetch_one(query), "system_transactions": []}

    for system_transaction in await get_system_transactions_by_raw_tx(raw_transaction):
        query = (
            update(SystemTransaction)
            .where(SystemTransaction.id == system_transaction["id"])
            .values(
                {
                    "status": TransactionStatus.FAILED,
                }
            )
            .returning(SystemTransaction)
        )
        raw_transaction["system_transactions"].append(await fetch_one(query))

    return raw_transaction


async def create_raw_transaction(
    amount: str,
    transaction_to: str,
    wallet: dict,
    nonce: int,
    gas_policy: GasPolicy = GasPolicy.STANDARD,
) -> dict:
    logger.info(
        f"Creating {gas_policy.upper()} raw transaction for wallet {wallet['external_id']}",
        extra={"wallet": wallet["external_id"]},
    )

    value = Web3.to_wei(amount, "ether")
    wallet_account = wallet["account"]
    from_address = wallet["address"]
    max_fee_per_gas = await get_gas_price_by_policy(gas_policy)
    max_priority_fee_per_gas = Web3.to_wei("0.05", "gwei")

    raw_transaction = {
        "to": Web3.to_checksum_address(transaction_to),
        "from": Web3.to_checksum_address(from_address),
        "value": value,
        "gas": 21000,
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee_per_gas,
        "chainId": settings.CHAIN_ID,
        "nonce": nonce,
    }

    logger.debug(
        f"Raw transaction was created, tx={raw_transaction}",
        extra={"wallet": wallet["external_id"]},
    )

    signed_tx: SignedTransaction = wallet_account.sign_transaction(raw_transaction)
    logger.debug(
        f"Raw transaction was signed, tx={signed_tx}",
        extra={
            "wallet": wallet["external_id"],
            "tx_hash": signed_tx.hash.hex(),
        },
    )
    db_raw_tx = (
        insert(RawTransaction)
        .values(
            {
                "status": RawTransactionStatus.CREATED,
                "tx_hash": signed_tx.hash.hex(),
                "tx_from": wallet["address"],
                "tx_to": transaction_to,
                "tx_value": value,
                "gas_limit": raw_transaction["gas"],
                "gas_price": raw_transaction["maxFeePerGas"],
                "nonce": nonce,
                "max_fee_per_gas": max_fee_per_gas,
                "max_priority_fee_per_gas": max_priority_fee_per_gas,
                "raw": signed_tx.rawTransaction.hex(),
            }
        )
        .returning(RawTransaction)
    )

    logger.debug(
        "Raw transaction was inserted into DB",
        extra={"wallet": wallet["external_id"], "tx_hash": signed_tx.hash.hex()},
    )

    return await fetch_one(db_raw_tx)


async def insert_raw_transaction_from_blockchain(blockchain_tx_data: TxData):
    # Get transaction receipt
    tx_receipt = await w3_obj.eth.get_transaction_receipt(blockchain_tx_data["hash"])
    db_raw_tx = (
        insert(RawTransaction)
        .values(
            {
                "status": RawTransactionStatus.PENDING,
                "tx_hash": blockchain_tx_data["hash"].hex(),
                "tx_from": blockchain_tx_data["from"],
                "tx_to": blockchain_tx_data["to"],
                "tx_value": blockchain_tx_data["value"],
                "tx_fee": tx_receipt["gasUsed"] * tx_receipt["effectiveGasPrice"],
                "tx_input": blockchain_tx_data["input"].hex(),
                "gas_price": blockchain_tx_data["gasPrice"],
                "gas_limit": blockchain_tx_data["gas"],
                "gas_used": tx_receipt["gasUsed"],
                "nonce": blockchain_tx_data["nonce"],
                "block_number": blockchain_tx_data["blockNumber"],
                "confirmation_count": 1,
                # "base_fee_per_gas": tx_receipt["baseFeePerGas"],
                "max_fee_per_gas": blockchain_tx_data["maxFeePerGas"],
                "max_priority_fee_per_gas": blockchain_tx_data["maxPriorityFeePerGas"],
            }
        )
        .returning(RawTransaction)
    )
    result = await fetch_one(db_raw_tx)

    logger.debug(
        f"Raw transaction {blockchain_tx_data['hash'].hex()} was inserted into DB",
        extra={"tx_hash": blockchain_tx_data["hash"].hex()},
    )

    return result


async def create_system_transaction(
    raw_transaction: RawTransaction,
    wallet: dict,
) -> dict:
    amount = Web3.from_wei(raw_transaction["tx_value"], "ether")

    if raw_transaction["tx_to"] == wallet["address"]:
        direction = TransactionDirection.IN
    elif raw_transaction["tx_from"] == wallet["address"]:
        direction = TransactionDirection.OUT
    else:
        raise Exception("Invalid transaction direction")

    status = RAW_SYSTEM_TX_STATUS_MAPPING[raw_transaction["status"]]

    system_transaction = (
        insert(SystemTransaction)
        .values(
            {
                "origin_id": raw_transaction["id"],
                "wallet_id": wallet["id"],
                "amount": str(amount),
                "status": status,
                "direction": direction,
            }
        )
        .returning(SystemTransaction)
    )

    return await fetch_one(system_transaction)


async def broadcast_transaction(raw_transaction: dict) -> dict:
    try:
        await w3_obj.eth.send_raw_transaction(HexBytes(raw_transaction["raw"]))
    except ValueError as exc:
        if "nonce too low" in str(exc):
            raise NonceIsTooLow(external_id=raw_transaction["external_id"]) from exc
        if "replacement transaction underpriced" in str(exc):
            raise ReplacementTransactionUnderpriced(
                external_id=raw_transaction["external_id"]
            ) from exc

    query = (
        update(RawTransaction)
        .where(RawTransaction.id == raw_transaction["id"])
        .values(
            {
                "status": RawTransactionStatus.BROADCASTED,
            }
        )
        .returning(RawTransaction)
    )
    result = await fetch_one(query)
    logger.debug(
        f"Raw transaction {raw_transaction['tx_hash']} was broadcasted",
        extra={"tx_hash": raw_transaction["tx_hash"]},
    )
    return result
