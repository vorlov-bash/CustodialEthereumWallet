bind = "0.0.0.0:8000"
timeout = 0
loglevel = "debug"
worker_class = "uvicorn.workers.UvicornWorker"
logger_class = "src.core.logger.GunicornLogger"

workers = 1
