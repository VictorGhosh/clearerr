###
# Dev script to move files from PC to server
###

#!/bin/bash

source ../.env

TARGETS=(
  "api" # folder
  "obj" # folder
  # "lib"
  "clearerr.py"
  "requirements.txt"
  # "name"
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
    
    # rsync is annoying about folders
    rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}api/" "${LOCAL_PATH}/api"
    rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}obj/" "${LOCAL_PATH}/obj"

    for f in "${TARGETS[@]}"; do
      if [[ "$f" != "api" && "$f" != "obj" ]]; then
        rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}${f}" "${LOCAL_PATH}/"
      fi
    done
    ;;

  push)
    echo "Pushing files: local -> server"

    rsync -rtvz --no-perms --no-owner --no-group "${LOCAL_PATH}/api/" "${REMOTE_PATH}api"
    rsync -rtvz --no-perms --no-owner --no-group "${LOCAL_PATH}/obj/" "${REMOTE_PATH}obj"

    for f in "${TARGETS[@]}"; do
      if [[ "$f" != "api" && "$f" != "obj" ]]; then
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