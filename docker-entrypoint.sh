#!/bin/bash

# Kill any existing python/uvicorn processes using /proc
for pid in /proc/[0-9]*; do
    cmd=$(cat $pid/cmdline 2>/dev/null | tr '\0' ' ')
    if echo "$cmd" | grep -qE 'uvicorn|backend.clearerr'; then
        # Don't kill our current script process
        if [ "${pid##*/}" != "$$" ]; then
            echo "Killing ghost process: $pid ($cmd)"
            kill -9 "${pid##*/}" 2>/dev/null
        fi
    fi
done

# Generate db if it does not exist yet
DB_PATH=$(python3 -c "from settings.config import config; print(config._DB_PATH)")
if [ ! -s "$DB_PATH" ]; then
    echo "Database not found. Initializing..." >&2
    python3 -u -c "from backend.clearerr import Actions; Actions.full_build_lib()"
else
    echo "Database exists. Skipping initialization."
fi

python3 -m uvicorn frontend.main:app --host 0.0.0.0 --port 8000 &
MAIN_PROCESS_PID=$!

# cron sucks
printenv | grep -v "no_proxy" > /etc/environment
echo "${BACKEND_CRON:-0 0 * * *} cd /app && $(which python3) -m backend.clearerr > /proc/1/fd/1 2>&1" | crontab -
service cron start

# watch main most likely to fail
wait $MAIN_PROCESS_PID