from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import BaseModel
from src.modules.transactions.enums import (
    RawTransactionStatus,
    TransactionDirection,
    TransactionStatus,
)


class RawTransaction(BaseModel):
    __tablename__ = "raw_transaction"

    status: Mapped[RawTransactionStatus] = mapped_column(
        String(50), nullable=False, default=RawTransactionStatus.CREATED
    )

    tx_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tx_from: Mapped[str] = mapped_column(String(255), nullable=False)
    tx_to: Mapped[str] = mapped_column(String(255), nullable=False)
    tx_value: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tx_fee: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tx_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    gas_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    gas_limit: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gas_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    nonce: Mapped[int] = mapped_column(Integer, nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmation_need: Mapped[int] = mapped_column(Integer, nullable=False, default=12)

    contract_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_input: Mapped[dict | None] = mapped_column(Text, nullable=True)
    raw: Mapped[str | None] = mapped_column(Text, nullable=True)

    # EIP-1559
    base_fee_per_gas: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_fee_per_gas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_priority_fee_per_gas: Mapped[int] = mapped_column(BigInteger, nullable=False)

    system_transactions: Mapped[list["SystemTransaction"]] = relationship(
        "SystemTransaction", back_populates="origin", cascade="all, delete-orphan", lazy="selectin"
    )


class SystemTransaction(BaseModel):
    __tablename__ = "system_transaction"

    origin_id: Mapped[int] = mapped_column(ForeignKey("raw_transaction.id"), unique=False)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"), unique=False)

    origin: Mapped[RawTransaction] = relationship(
        "RawTransaction", back_populates="system_transactions", lazy="selectin"
    )

    amount: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        String(50), nullable=False, default=TransactionStatus.CREATED
    )
    direction: Mapped[TransactionDirection] = mapped_column(String(50), nullable=False)
