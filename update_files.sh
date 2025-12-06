###
# Dev helper script to update files on the remote server
###
#!/bin/bash

# load .env
source ./.env

# files to move. should only be what is expected on the server
FILES=(
  "clearerr.py"
  "media_structs.py"
  "name"
  "script"
  ".env"
)

REMOTE_PATH="root@$UNRAID_IP:/boot/config/plugins/user.scripts/scripts/clearerr/"
LOCAL_PATH="."

if [ -z "$1" ]; then
  echo "Usage: $0 {push|pull}"
  exit 1
fi

case "$1" in
  pull)
    echo "Pulling files: server -> local"
    for f in "${FILES[@]}"; do
      rsync -rtvz --no-perms --no-owner --no-group "${REMOTE_PATH}${f}" "${LOCAL_PATH}/"
    done
    ;;
  push)
    echo "Pushing files: local -> server"
    for f in "${FILES[@]}"; do
      rsync -rtvz --no-perms --no-owner --no-group "${LOCAL_PATH}/${f}" "${REMOTE_PATH}${f}"
    done
    ;;
  *)
    echo "Invalid flag: $1"
    echo "Use: push or pull"
    exit 1
    ;;
esac

echo "Done."