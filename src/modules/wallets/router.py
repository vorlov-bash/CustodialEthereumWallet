from fastapi import APIRouter, Depends

from src.modules.wallets.dependencies import get_wallet
from src.modules.wallets.exceptions import WalletWithIndexAlreadyExists
from src.modules.wallets.schemas import WalletSchema
from src.modules.wallets.service import create_wallet, get_wallet_by_index, get_wallets_list

router = APIRouter(prefix="/wallet", tags=["wallets"])


@router.on_event("startup")
async def startup_event():
    try:
        await create_wallet(index=0, activate=True)
    except WalletWithIndexAlreadyExists:
        pass


@router.get(
    path="/main",
    response_model=WalletSchema,
    summary="Get main wallet",
)
async def get_main_wallet_view() -> dict:
    return await get_wallet_by_index(index=0)


@router.get(
    path="/list",
    response_model=list[WalletSchema],
    summary="Get wallets list",
)
async def get_wallets_list_view() -> list[dict]:
    return await get_wallets_list()


@router.get(
    path="/{external_id}",
    response_model=WalletSchema,
    summary="Get wallet",
)
async def get_wallet_view(wallet: dict = Depends(get_wallet)) -> dict:
    return wallet


@router.post(
    path="",
    response_model=WalletSchema,
    summary="Create new deposit wallet",
)
async def create_deposit_wallet(index: int | None = None, activate: bool = False) -> dict:
    return await create_wallet(index=index, activate=activate)


# @router.post("/deposit")
# @router.get("/{address}")
# @router.put("/deposit/{address}/enable")
# @router.put("/deposit/{address}/disable")
# @router.get("/deposit/list")
