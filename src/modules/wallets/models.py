from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import BaseModel
from src.modules.wallets.enums import WalletStatus


class Wallet(BaseModel):
    __tablename__ = "wallet"

    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[WalletStatus] = mapped_column(
        String(50), nullable=False, default=WalletStatus.INACTIVE
    )
    nonce: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    index: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
