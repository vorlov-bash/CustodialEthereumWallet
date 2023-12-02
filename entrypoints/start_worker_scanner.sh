#!/usr/bin/env bash

set -e

MODULE_NAME="src.celery.config"
QUEUE_NAME="eth_scanner_queue"

celery -A $MODULE_NAME worker \
  -Ofair -Q $QUEUE_NAME -P solo \
  --loglevel=DEBUG --logfile=logs/worker.log \
  --without-gossip --without-mingle --without-heartbeat