#!/usr/bin/env bash
# Database backup script for Multi-Tenant SaaS
# Creates full database dumps and manages WAL archiving

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
WAL_DIR="$SCRIPT_DIR/wal"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Database connection details (from docker-compose.yml)
DB_NAME="multitenant_saas"
DB_USER="saasadmin"
DB_PASSWORD="supersecret123"
DB_HOST="localhost"
DB_PORT="5433"

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

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database is running
check_db_connection() {
    log "Checking database connection..."
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; then
        error "Database is not accessible. Is the Docker container running?"
    fi
    log "Database connection OK"
}

# Full database backup
backup_full() {
    local backup_file="$BACKUP_DIR/full_backup_${TIMESTAMP}.sql"
    local backup_file_gz="${backup_file}.gz"
    
    log "Creating full database backup..."
    log "Backup file: $backup_file_gz"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Create backup with all schemas
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
               --verbose --no-password --format=custom --no-privileges --no-owner \
               --file="$backup_file.custom"; then
        
        # Also create SQL version for readability
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                --verbose --no-password --no-privileges --no-owner \
                | gzip > "$backup_file_gz"
        
        log "Full backup completed successfully"
        log "Files created:"
        log "  - $backup_file.custom (PostgreSQL custom format)"
        log "  - $backup_file_gz (SQL format, compressed)"
        
        # Get backup size
        local size=$(du -h "$backup_file_gz" | cut -f1)
        log "Backup size: $size"
        
    else
        error "Full backup failed"
    fi
    
    unset PGPASSWORD
}

# Backup specific schema (tenant)
backup_schema() {
    local schema_name="$1"
    local backup_file="$BACKUP_DIR/schema_${schema_name}_${TIMESTAMP}.sql.gz"
    
    log "Creating backup for schema: $schema_name"
    log "Backup file: $backup_file"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
               --schema="$schema_name" --verbose --no-password \
               --no-privileges --no-owner | gzip > "$backup_file"; then
        
        log "Schema backup completed successfully"
        local size=$(du -h "$backup_file" | cut -f1)
        log "Backup size: $size"
        
    else
        error "Schema backup failed for: $schema_name"
    fi
    
    unset PGPASSWORD
}

# List available backups
list_backups() {
    log "Available backups in $BACKUP_DIR:"
    
    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        warn "No backups found"
        return 0
    fi
    
    echo ""
    echo "Full backups:"
    ls -lh "$BACKUP_DIR"/full_backup_* 2>/dev/null | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' || echo "  None"
    
    echo ""
    echo "Schema backups:"
    ls -lh "$BACKUP_DIR"/schema_* 2>/dev/null | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' || echo "  None"
    
    echo ""
    echo "WAL files:"
    if [[ -d "$WAL_DIR" ]] && [[ -n "$(ls -A "$WAL_DIR" 2>/dev/null)" ]]; then
        local wal_count=$(ls -1 "$WAL_DIR"/*.backup 2>/dev/null | wc -l || echo 0)
        local wal_size=$(du -sh "$WAL_DIR" 2>/dev/null | cut -f1 || echo "0")
        echo "  $wal_count WAL backup files ($wal_size total)"
    else
        echo "  None"
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
    fi
    
    log "Restoring from backup: $backup_file"
    warn "This will OVERWRITE the current database!"
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restore cancelled"
        return 0
    fi
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Determine file type and restore accordingly
    if [[ "$backup_file" == *.custom ]]; then
        log "Restoring from custom format backup..."
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                   --verbose --clean --if-exists --no-privileges --no-owner \
                   "$backup_file"
    elif [[ "$backup_file" == *.gz ]]; then
        log "Restoring from compressed SQL backup..."
        gunzip -c "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    else
        log "Restoring from SQL backup..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$backup_file"
    fi
    
    if [[ $? -eq 0 ]]; then
        log "Restore completed successfully"
    else
        error "Restore failed"
    fi
    
    unset PGPASSWORD
}

# Clean old backups
cleanup_backups() {
    local days="${1:-7}"
    
    log "Cleaning up backups older than $days days..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        local count=$(find "$BACKUP_DIR" -name "*.sql*" -mtime +${days} | wc -l)
        if [[ $count -gt 0 ]]; then
            find "$BACKUP_DIR" -name "*.sql*" -mtime +${days} -delete
            log "Deleted $count old backup files"
        else
            log "No old backups to clean up"
        fi
    fi
    
    # Clean old WAL files if they exist
    if [[ -d "$WAL_DIR" ]]; then
        local wal_count=$(find "$WAL_DIR" -name "*.backup" -mtime +${days} 2>/dev/null | wc -l || echo 0)
        if [[ $wal_count -gt 0 ]]; then
            find "$WAL_DIR" -name "*.backup" -mtime +${days} -delete 2>/dev/null || true
            log "Deleted $wal_count old WAL files"
        fi
    fi
}

# Show usage
show_help() {
    echo "Database Backup Script for Multi-Tenant SaaS"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  full                    - Create full database backup"
    echo "  schema <schema_name>    - Backup specific tenant schema"
    echo "  list                    - List all available backups"
    echo "  restore <backup_file>   - Restore from backup file"
    echo "  cleanup [days]          - Clean backups older than N days (default: 7)"
    echo "  help                    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full"
    echo "  $0 schema tenant1"
    echo "  $0 restore backups/full_backup_20231201_143022.sql.gz"
    echo "  $0 cleanup 30"
    echo ""
    echo "Environment variables:"
    echo "  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME"
    echo ""
    echo "Requirements:"
    echo "  - PostgreSQL client tools (pg_dump, pg_restore, psql)"
    echo "  - Database running on $DB_HOST:$DB_PORT"
}

# Main command processing
case "${1:-help}" in
    full)
        check_db_connection
        backup_full
        ;;
    
    schema)
        if [[ -z "${2:-}" ]]; then
            error "Schema name required. Usage: $0 schema <schema_name>"
        fi
        check_db_connection
        backup_schema "$2"
        ;;
    
    list)
        list_backups
        ;;
    
    restore)
        if [[ -z "${2:-}" ]]; then
            error "Backup file required. Usage: $0 restore <backup_file>"
        fi
        check_db_connection
        restore_backup "$2"
        ;;
    
    cleanup)
        cleanup_backups "${2:-7}"
        ;;
    
    help|*)
        show_help
        ;;
esac
