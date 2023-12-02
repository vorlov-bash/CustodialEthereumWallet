"""
In this file you must import all models from a whole project to
be able alembic see all metadata to autogenerate migrations.
"""
from src.database.base import Base
from src.modules.transactions.models import RawTransaction, SystemTransaction  # noqa: F401
from src.modules.wallets.models import Wallet  # noqa: F401

metadata = Base.metadata

__all__ = ["metadata"]
