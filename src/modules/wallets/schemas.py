from datetime import datetime

from pydantic import BaseModel

from src.modules.wallets.enums import WalletStatus


class WalletSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
    external_id: str
    address: str
    index: int
    nonce: int
    status: WalletStatus
