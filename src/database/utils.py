from typing import Any

from sqlalchemy import Delete, Insert, Select, Update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.engine import async_session


async def fetch_one(
    query: Select | Insert | Update,
    raise_on_none: bool = False,
    session: async_sessionmaker[AsyncSession] = async_session,
    auto_commit: bool = True,
) -> dict[str, Any] | None:
    async with session() as session:
        result = await session.execute(query)
        await session.commit()

        obj = result.scalar_one() if raise_on_none else result.scalar_one_or_none()
        return obj.asdict() if obj else None


async def fetch_all(
    query: Select | Insert | Update,
    session: async_sessionmaker[AsyncSession] = async_session,
) -> list[dict[str, Any]]:
    async with session() as session:
        result = await session.execute(query)
        await session.commit()

        return [obj.asdict() for obj in result.scalars().all()]


async def execute(
    *queries: Select | Insert | Update | Delete,
    session: async_sessionmaker[AsyncSession] = async_session,
) -> None:
    async with session() as session:
        for query in queries:
            await session.execute(query)
            await session.commit()
