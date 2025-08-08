#!/usr/bin/env bash
# Randomly restarts services for a duration
# Usage: ./docker-chaos.sh <duration_sec> <min_wait_sec> <max_wait_sec>

set -euo pipefail
DURATION="${1:-300}"
MIN_WAIT="${2:-5}"
MAX_WAIT="${3:-15}"
END=$(( $(date +%s) + DURATION ))
SERVICES=(web db redis)

while [ "$(date +%s)" -lt "$END" ]; do
  SVC=${SERVICES[$RANDOM % ${#SERVICES[@]}]}
  echo "[chaos] restarting $SVC"
  docker compose -f devops/docker/docker-compose.yml restart "$SVC" >/dev/null
  SLEEP=$(( RANDOM % (MAX_WAIT - MIN_WAIT + 1) + MIN_WAIT ))
  sleep "$SLEEP"
done

echo "[chaos] done"
