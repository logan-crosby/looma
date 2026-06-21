#!/usr/bin/env bash
# Looma demo recording script.
# Run from inside a repo that has Claude Code history, e.g.:
#   asciinema rec looma.cast -c "bash /path/to/looma/docs/demo/demo_script.sh"
#
# Uses an isolated demo DB so it never touches your real ~/.looma store.
set -euo pipefail

export LOOMA_DB="${LOOMA_DB:-/tmp/looma-demo-rec/looma.db}"
rm -rf "$(dirname "$LOOMA_DB")"

pause() { sleep "${1:-1.5}"; }
run()   { echo "+ $*"; "$@"; pause "${PAUSE:-1.5}"; }

run looma doctor
run looma init
run looma ingest --once --limit 25 --verbose
run looma work
echo "+ looma resume \"auth\""
looma resume "auth"
sleep 3   # hold on the payoff frame
