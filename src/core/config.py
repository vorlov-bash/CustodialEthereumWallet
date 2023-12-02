import contextvars
import pathlib
from typing import Literal
from uuid import uuid4

from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from web3 import AsyncHTTPProvider, AsyncWeb3

BASE_DIR = pathlib.Path(__file__).parent.parent.parent
PROJECT_DIR = BASE_DIR / "src"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
ABI_DIR = BASE_DIR / "abi"

CONTEXT_ID = contextvars.ContextVar("context_id", default=str(uuid4()))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

    SETTINGS_MODULE: Literal["DEV", "PROD"] = "DEV"
    DATABASE_URI: str | PostgresDsn
    REDIS_URI: str | RedisDsn
    CELERY_BROKER_URL: str | RedisDsn

    ETH_WALLET_XPRIV: SecretStr
    ETH_RPC_URL: str
    CHAIN_ID: int = 1

    SECRET_KEY: SecretStr


settings = Settings()

FASTAPI_CONFIG = {
    "title": "Ethereum wallet service",
    "version": "0.0.1",
    "description": "This is a service for creating and manage Ethereum wallets",
}

w3_obj: AsyncWeb3 = AsyncWeb3(AsyncHTTPProvider(settings.ETH_RPC_URL))
