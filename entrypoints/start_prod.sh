#!/usr/bin/env bash

set -e

export SETTINGS_MODULE="PROD"

export WORKER_CLASS="uvicorn.workers.UvicornWorker"
export GUNICORN_CONF="gunicorn/gunicorn.conf.py"
export APP_MODULE="src.main:app"

# Migrations
python -m alembic upgrade head

gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"
