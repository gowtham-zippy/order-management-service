#!/usr/bin/env bash
# Azure App Service (Linux/Python) startup command.
set -e
cd /home/site/wwwroot
export PYTHONPATH="/home/site/wwwroot:/home/site/wwwroot/.python_packages_local:${PYTHONPATH}"
exec python -m gunicorn app.main:app \
  --bind=0.0.0.0:${PORT:-8000} \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --timeout 120 \
  --access-logfile '-' \
  --error-logfile '-'
