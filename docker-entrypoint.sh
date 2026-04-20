#!/bin/bash

python3 -m uvicorn frontend.main:app --host 0.0.0.0 --port 8000 &
MAIN_PROCESS_PID=$!

echo "${BACKEND_CRON:-0 0 * * *} python3 -m backend.clearerr > /proc/1/fd/1 2>&1" | crontab -

# cron in background
service cron start

# watch main most likely to fail
wait $MAIN_PROCESS_PID