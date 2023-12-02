from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.dao.sqlalchemy import SqlAlchemyDAOAdapter
from src.modules.wallets.enums import WalletStatus
from src.modules.wallets.models import Wallet


class WalletDAOAdapter(SqlAlchemyDAOAdapter):
    model = Wallet

    def __init__(self, session: async_sessionmaker[AsyncSession]):
        super().__init__(session)

    async def get_active_wallet_by_address(self, address: str) -> dict | None:
        return await self.get_by_fields(self.model.address == address)

    async def get_wallet_by_index(self, index: int) -> dict | None:
        return await self.get_by_fields(self.model.index == index)

    async def get_by_address(self, address: str) -> dict | None:
        return await self.get_by_fields(self.model.address == address)

    async def get_disabled_wallet_by_address(self, address: str) -> dict | None:
        return await self.get_by_fields(
            fields=and_(
                self.model.c.address == address, self.model.c.status == WalletStatus.INACTIVE
            )
        )
