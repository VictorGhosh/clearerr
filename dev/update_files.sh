#!/bin/bash

source ../.env

TARGETS=(
  "api" # Folder
  "clearerr.py" 
  "name"
  "script"
  ".env"  
)

REMOTE_PATH="root@$UNRAID_IP:/boot/config/plugins/user.scripts/scripts/clearerr/"
LOCAL_PATH=".."

if [ -z "$1" ]; then
  echo "Usage: $0 {push|pull}"
  exit 1
fi

case "$1" in
  pull)
    echo "Pulling files: server -> local"
    rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}api/" "${LOCAL_PATH}/api"

    for f in "${TARGETS[@]}"; do
      if [ "$f" != "api" ]; then
        rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}${f}" "${LOCAL_PATH}/"
      fi
    done
    ;;

  push)
    echo "Pushing files: local -> server"

    # rsync is annoying about folders
    rsync -rtvz --no-perms --no-owner --no-group "${LOCAL_PATH}/api/" "${REMOTE_PATH}api"

    for f in "${TARGETS[@]}"; do
      if [ "$f" != "api" ]; then
        rsync -rtvz --no-perms --no-owner --no-group "${LOCAL_PATH}/${f}" "${REMOTE_PATH}${f}"
      fi
    done
    ;;

  *)
    echo "Invalid flag: $1"
    echo "Use: push or pull"
    exit 1
    ;;
esac

echo "Done."