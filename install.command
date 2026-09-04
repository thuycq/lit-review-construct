#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec /bin/bash "$SCRIPT_DIR/install.sh" "$@"
