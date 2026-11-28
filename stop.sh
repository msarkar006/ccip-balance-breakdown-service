#!/bin/bash
# stop.sh - stop only the processes start.sh recorded in .pids.
cd "$(dirname "$0")" || exit 1
if [ ! -f .pids ]; then
    echo "No .pids file found; nothing to stop."
    exit 0
fi
while IFS= read -r pid; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "Stopped PID $pid"
    fi
done <.pids
rm -f .pids
echo "All services stopped."
