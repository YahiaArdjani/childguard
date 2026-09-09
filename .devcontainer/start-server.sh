#!/usr/bin/env bash
set -euo pipefail

if curl --silent --fail http://127.0.0.1:8000/docs >/dev/null 2>&1; then
  exit 0
fi

nohup python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info \
  >/tmp/uvicorn.log 2>&1 &
