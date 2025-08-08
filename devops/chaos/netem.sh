#!/usr/bin/env bash
# Network chaos engineering using Linux tc (traffic control)
# Requires root privileges (sudo)
# Usage: sudo ./netem.sh [add|clear] [service] [delay]

set -euo pipefail

ACTION="${1:-help}"
SERVICE="${2:-}"
DELAY="${3:-100ms}"

# Docker compose file path
COMPOSE_FILE="devops/docker/docker-compose.yml"

function log() {
    echo "[netem] $1"
}

function get_container_id() {
    local service="$1"
    docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null || echo ""
}

function get_container_pid() {
    local container_id="$1"
    docker inspect -f '{{.State.Pid}}' "$container_id" 2>/dev/null || echo ""
}

function add_delay() {
    local service="$1"
    local delay="$2"
    
    log "Adding $delay delay to service: $service"
    
    local container_id
    container_id=$(get_container_id "$service")
    
    if [[ -z "$container_id" ]]; then
        log "ERROR: Service '$service' not found or not running"
        return 1
    fi
    
    local pid
    pid=$(get_container_pid "$container_id")
    
    if [[ -z "$pid" ]]; then
        log "ERROR: Could not get PID for container $container_id"
        return 1
    fi
    
    # Enter network namespace and add delay
    nsenter -t "$pid" -n tc qdisc add dev eth0 root netem delay "$delay"
    log "Added $delay delay to $service (container: $container_id)"
}

function clear_delay() {
    local service="$1"
    
    if [[ "$service" == "all" ]]; then
        log "Clearing delay from all services"
        for svc in web db redis; do
            clear_delay "$svc" || true
        done
        return 0
    fi
    
    log "Clearing delay from service: $service"
    
    local container_id
    container_id=$(get_container_id "$service")
    
    if [[ -z "$container_id" ]]; then
        log "WARNING: Service '$service' not found or not running"
        return 0
    fi
    
    local pid
    pid=$(get_container_pid "$container_id")
    
    if [[ -z "$pid" ]]; then
        log "WARNING: Could not get PID for container $container_id"
        return 0
    fi
    
    # Enter network namespace and clear delay
    nsenter -t "$pid" -n tc qdisc del dev eth0 root 2>/dev/null || true
    log "Cleared delay from $service (container: $container_id)"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    echo "Example: sudo $0 add web 200ms"
    exit 1
fi

case "$ACTION" in
    add)
        if [[ -z "$SERVICE" ]]; then
            echo "Usage: $0 add <service> [delay]"
            echo "Services: web, db, redis"
            echo "Example: $0 add web 200ms"
            exit 1
        fi
        add_delay "$SERVICE" "$DELAY"
        ;;
    
    clear)
        if [[ -z "$SERVICE" ]]; then
            echo "Usage: $0 clear <service|all>"
            echo "Services: web, db, redis, all"
            echo "Example: $0 clear web"
            exit 1
        fi
        clear_delay "$SERVICE"
        ;;
    
    help|*)
        echo "Network Chaos Engineering Tool"
        echo ""
        echo "Usage: sudo $0 [action] [service] [delay]"
        echo ""
        echo "Actions:"
        echo "  add    - Add network delay to service"
        echo "  clear  - Clear network delay from service"
        echo ""
        echo "Services:"
        echo "  web    - Web application service"
        echo "  db     - PostgreSQL database service" 
        echo "  redis  - Redis cache service"
        echo "  all    - All services (clear only)"
        echo ""
        echo "Examples:"
        echo "  sudo $0 add web 200ms      # Add 200ms delay to web service"
        echo "  sudo $0 add db 500ms       # Add 500ms delay to database"
        echo "  sudo $0 clear web          # Clear delay from web service"
        echo "  sudo $0 clear all          # Clear delay from all services"
        echo ""
        echo "Note: Requires root privileges and Linux tc (traffic control)"
        ;;
esac
