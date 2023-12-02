#!/usr/bin/env bash

set -e

export WORKER_CLASS="uvicorn.workers.UvicornWorker"
export GUNICORN_CONF="gunicorn/gunicorn.conf.py"
export APP_MODULE="src.main:app"

# Migrations
python -m alembic upgrade head

python -m src.scanner
