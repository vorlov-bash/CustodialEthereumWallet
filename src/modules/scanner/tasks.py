import asyncio

from src.celery.config import SCANNER_QUEUE, app
from src.modules.scanner.service import run_scanner


@app.task(
    name="block_scanner",
    queue=SCANNER_QUEUE,
    ignore_result=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 10},
)
def block_scanner():
    asyncio.run(run_scanner())
