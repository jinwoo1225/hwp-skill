#!/usr/bin/env bash
# ============================================
# hwp-skill · Unix wrapper
# 사용법: ./run.sh input.md output.hwpx [--template X]
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "[ERROR] python3 또는 python이 필요합니다." >&2
    exit 1
fi

echo "[hwp-skill] $PY \"$SCRIPT_DIR/md_to_hwpx.py\" $*"
exec "$PY" "$SCRIPT_DIR/md_to_hwpx.py" "$@"
