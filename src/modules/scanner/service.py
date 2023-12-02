import logging
import signal

from web3.types import TxData

from src.core.config import w3_obj
from src.core.utils import signal_fence
from src.database.redis import redis
from src.modules.scanner.utils import build_map_from_list_of_dicts
from src.modules.transactions.enums import RawTransactionStatus
from src.modules.transactions.service import (
    confirm_raw_transaction_by_blockchain,
    create_system_transaction,
    get_raw_transaction_by_hash,
    get_raw_transactions_by_status,
    insert_raw_transaction_from_blockchain,
)
from src.modules.wallets.service import get_wallet_by_address

logger = logging.getLogger("root")


async def confirm_block(block_number: int) -> None:
    logger.info(f"Confirming block {block_number}", extra={"block_number": block_number})

    block_info = await w3_obj.eth.get_block(block_number, full_transactions=True)

    logger.info(
        f"Found {len(block_info.get('transactions'))} transactions in block {block_number}",
        extra={"block_number": block_number},
    )

    # Map transaction hash to raw transaction object to decrease big O complexity.
    pending_transactions = build_map_from_list_of_dicts(
        list_of_dicts=await get_raw_transactions_by_status(statuses=[RawTransactionStatus.PENDING]),
        key="tx_hash",
    )

    with signal_fence(signal.SIGINT):
        for transaction in block_info.get("transactions"):
            tx_hash = transaction.get("hash").hex()
            logger.debug(
                f"Processing transaction {transaction.get('hash').hex()}",
                extra={"block_number": block_number},
            )
            transaction: TxData

            # In this stage raw transaction only have a broadcasted status

            wallet_from = await get_wallet_by_address(transaction.get("from"))
            wallet_to = await get_wallet_by_address(transaction.get("to"))

            if wallet_from or wallet_to:
                # Means that transaction is related to our system.
                # We need to create raw and system transactions.
                logger.debug(
                    f"Detected transaction {tx_hash}", extra={"block_number": block_number}
                )

                broadcasted_transaction = await get_raw_transaction_by_hash(tx_hash)
                if not broadcasted_transaction:
                    pending_transaction = await insert_raw_transaction_from_blockchain(transaction)
                else:
                    pending_transaction = await confirm_raw_transaction_by_blockchain(
                        raw_transaction=broadcasted_transaction,
                        confirmations=1,
                        blockchain_tx_data=transaction,
                    )

                if wallet_from:
                    await create_system_transaction(pending_transaction, wallet_from)

                if wallet_to:
                    await create_system_transaction(pending_transaction, wallet_to)

        # Confirm pending transactions
        for pending_transaction in pending_transactions.values():
            confirmations = 1

            block_number_delta = block_number - pending_transaction["block_number"]
            confirmations_left = (
                pending_transaction["confirmation_need"] - pending_transaction["confirmation_count"]
            )

            if block_number_delta > confirmations_left:
                confirmations = confirmations_left

            await confirm_raw_transaction_by_blockchain(
                raw_transaction=pending_transaction, confirmations=confirmations
            )

    logger.info(f"Block {block_number} confirmed", extra={"block_number": block_number})


async def set_last_scanned_block(block_number: int) -> None:
    await redis.set("EWS:last_scanned_block", block_number)


async def get_last_scanned_block() -> int | None:
    last_block_number = await redis.get("EWS:last_scanned_block")
    return int(last_block_number) if last_block_number else None
