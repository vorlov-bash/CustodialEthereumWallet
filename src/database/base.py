import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, class_mapper, mapped_column

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    external_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, default=lambda x: str(uuid.uuid4())
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return str(self.__dict__)

    def asdict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in class_mapper(self.__class__).mapped_table.c
        }
