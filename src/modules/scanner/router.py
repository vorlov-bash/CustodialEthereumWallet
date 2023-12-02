import asyncio

from fastapi import APIRouter

from src.modules.scanner.service import run_scanner

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    asyncio.create_task(run_scanner())
