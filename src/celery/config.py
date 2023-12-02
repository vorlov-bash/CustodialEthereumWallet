from celery import Celery
from celery.signals import setup_logging as celery_setup_logging
from src.core.logger import setup_logging as setup_system_logging

app = Celery(
    "eth_service",
    broker="redis://localhost:6379/11",
    include=[
        "src.modules.scanner.tasks",
    ],
)
SCANNER_QUEUE = "eth_scanner_queue"
BROADCAST_QUEUE = "eth_broadcast_queue"


@celery_setup_logging.connect
def config_loggers(*args, **kwargs):
    setup_system_logging()
