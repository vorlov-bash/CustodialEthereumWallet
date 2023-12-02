from fastapi import Depends, FastAPI

from src.core.config import FASTAPI_CONFIG
from src.core.logger import setup_logging
from src.core.middlewares import log_body, setup_middlewares

from src.modules.wallets.router import router as wallets_router

setup_logging()
app = FastAPI(
    **FASTAPI_CONFIG,
    dependencies=[
        Depends(log_body())
    ],
)
setup_middlewares(app)

# Routes
app.include_router(wallets_router, tags=["wallets"])


# app.include_router(settings_router, tags=["settings"], prefix="/settings")


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
