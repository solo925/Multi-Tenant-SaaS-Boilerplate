#!/usr/bin/env bash
# Load testing runner script
# Usage: ./run_tests.sh [scenario]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCUSTFILE="$SCRIPT_DIR/locustfile.py"
HOST="${HOST:-http://localhost:8000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    error "Locust is not installed. Run: pip install locust"
fi

# Check if app is running
log "Checking if application is running at $HOST..."
if ! curl -s "$HOST" > /dev/null; then
    warn "Application may not be running at $HOST"
    warn "Start with: docker compose -f devops/docker/docker-compose.yml up -d"
fi

case "${1:-smoke}" in
    smoke)
        log "Running smoke test (10 users, 30 seconds)..."
        locust -f "$LOCUSTFILE" --headless -u 10 -r 2 -t 30s --host="$HOST" --only-summary
        ;;
    
    quick)
        log "Running quick test (50 users, 2 minutes)..."
        locust -f "$LOCUSTFILE" --headless -u 50 -r 10 -t 120s --host="$HOST" --csv=quick-test
        ;;
    
    stress)
        log "Running stress test (200 users, 5 minutes)..."
        locust -f "$LOCUSTFILE" --headless -u 200 -r 20 -t 300s --host="$HOST" --csv=stress-test
        ;;
    
    sustained)
        log "Running sustained load test (100 users, 10 minutes)..."
        locust -f "$LOCUSTFILE" --headless -u 100 -r 10 -t 600s --host="$HOST" --csv=sustained-test
        ;;
    
    ui)
        log "Starting Locust web UI at http://localhost:8089"
        locust -f "$LOCUSTFILE" --host="$HOST"
        ;;
    
    anonymous)
        log "Testing anonymous users only (30 users, 2 minutes)..."
        locust -f "$LOCUSTFILE" AnonymousUser --headless -u 30 -r 5 -t 120s --host="$HOST" --csv=anonymous-test
        ;;
    
    authenticated)
        log "Testing authenticated users only (20 users, 2 minutes)..."
        locust -f "$LOCUSTFILE" AuthenticatedUser --headless -u 20 -r 5 -t 120s --host="$HOST" --csv=auth-test
        ;;
    
    burst)
        log "Running burst traffic test (100 users, 1 minute)..."
        locust -f "$LOCUSTFILE" BurstTraffic --headless -u 100 -r 50 -t 60s --host="$HOST" --csv=burst-test
        ;;
    
    clean)
        log "Cleaning up old test results..."
        rm -f *.csv *.html locust.log
        log "Cleanup complete"
        ;;
    
    help|*)
        echo "Load Testing Runner"
        echo ""
        echo "Usage: $0 [scenario]"
        echo ""
        echo "Scenarios:"
        echo "  smoke      - Quick smoke test (10 users, 30s)"
        echo "  quick      - Quick test (50 users, 2min)"
        echo "  stress     - Stress test (200 users, 5min)"
        echo "  sustained  - Sustained load (100 users, 10min)"
        echo "  ui         - Start web UI"
        echo "  anonymous  - Test anonymous users only"
        echo "  authenticated - Test authenticated users only"
        echo "  burst      - Burst traffic test"
        echo "  clean      - Clean up test results"
        echo "  help       - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  HOST       - Target host (default: http://localhost:8000)"
        echo ""
        echo "Examples:"
        echo "  $0 smoke"
        echo "  HOST=https://staging.app.com $0 quick"
        ;;
esac
