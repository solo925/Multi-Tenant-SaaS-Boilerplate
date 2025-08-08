param(
    [string]$Command = "help",
    [string]$Parameter = ""
)

# Database connection details (from docker-compose.yml)
$DB_NAME = "multitenant_saas"
$DB_USER = "saasadmin"
$DB_PASSWORD = "supersecret123"
$DB_HOST = "localhost"
$DB_PORT = "5433"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupDir = Join-Path $ScriptDir "backups"
$WalDir = Join-Path $ScriptDir "wal"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Check if database is running
function Test-DatabaseConnection {
    Write-Log "Checking database connection..."
    
    try {
        $env:PGPASSWORD = $DB_PASSWORD
        $result = & pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -q
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Database connection OK"
            return $true
        } else {
            Write-Error "Database is not accessible. Is the Docker container running?"
            return $false
        }
    } catch {
        Write-Error "pg_isready command not found. Install PostgreSQL client tools."
        return $false
    }
}

# Full database backup
function Backup-Full {
    $BackupFile = Join-Path $BackupDir "full_backup_$Timestamp.sql"
    $BackupFileGz = "$BackupFile.gz"
    $BackupFileCustom = "$BackupFile.custom"
    
    Write-Log "Creating full database backup..."
    Write-Log "Backup file: $BackupFileGz"
    
    try {
        $env:PGPASSWORD = $DB_PASSWORD
        
        # Create custom format backup
        & pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
                  --verbose --no-password --format=custom --no-privileges --no-owner `
                  --file=$BackupFileCustom
        
        if ($LASTEXITCODE -eq 0) {
            # Also create SQL version and compress it
            & pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
                      --verbose --no-password --no-privileges --no-owner | `
                      gzip > $BackupFileGz
            
            Write-Log "Full backup completed successfully"
            Write-Log "Files created:"
            Write-Log "  - $BackupFileCustom (PostgreSQL custom format)"
            Write-Log "  - $BackupFileGz (SQL format, compressed)"
            
            # Get backup size
            $Size = (Get-Item $BackupFileGz).Length / 1MB
            Write-Log "Backup size: $([math]::Round($Size, 2)) MB"
        } else {
            Write-Error "Full backup failed"
        }
        
    } catch {
        Write-Error "Backup failed: $($_.Exception.Message)"
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# Backup specific schema (tenant)
function Backup-Schema {
    param([string]$SchemaName)
    
    $BackupFile = Join-Path $BackupDir "schema_${SchemaName}_$Timestamp.sql.gz"
    
    Write-Log "Creating backup for schema: $SchemaName"
    Write-Log "Backup file: $BackupFile"
    
    try {
        $env:PGPASSWORD = $DB_PASSWORD
        
        & pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
                  --schema=$SchemaName --verbose --no-password `
                  --no-privileges --no-owner | gzip > $BackupFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Schema backup completed successfully"
            $Size = (Get-Item $BackupFile).Length / 1MB
            Write-Log "Backup size: $([math]::Round($Size, 2)) MB"
        } else {
            Write-Error "Schema backup failed for: $SchemaName"
        }
        
    } catch {
        Write-Error "Schema backup failed: $($_.Exception.Message)"
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# List available backups
function Get-BackupList {
    Write-Log "Available backups in $BackupDir:"
    
    if (!(Test-Path $BackupDir) -or ((Get-ChildItem $BackupDir).Count -eq 0)) {
        Write-Warn "No backups found"
        return
    }
    
    Write-Host ""
    Write-Host "Full backups:"
    $FullBackups = Get-ChildItem $BackupDir -Filter "full_backup_*" | Sort-Object LastWriteTime -Descending
    if ($FullBackups) {
        foreach ($backup in $FullBackups) {
            $size = [math]::Round($backup.Length / 1MB, 2)
            Write-Host "  $($backup.Name) ($size MB, $($backup.LastWriteTime))"
        }
    } else {
        Write-Host "  None"
    }
    
    Write-Host ""
    Write-Host "Schema backups:"
    $SchemaBackups = Get-ChildItem $BackupDir -Filter "schema_*" | Sort-Object LastWriteTime -Descending
    if ($SchemaBackups) {
        foreach ($backup in $SchemaBackups) {
            $size = [math]::Round($backup.Length / 1MB, 2)
            Write-Host "  $($backup.Name) ($size MB, $($backup.LastWriteTime))"
        }
    } else {
        Write-Host "  None"
    }
    
    Write-Host ""
    Write-Host "WAL files:"
    if ((Test-Path $WalDir) -and ((Get-ChildItem $WalDir -Filter "*.backup" -ErrorAction SilentlyContinue).Count -gt 0)) {
        $WalFiles = Get-ChildItem $WalDir -Filter "*.backup"
        $WalSize = ($WalFiles | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  $($WalFiles.Count) WAL backup files ($([math]::Round($WalSize, 2)) MB total)"
    } else {
        Write-Host "  None"
    }
}

# Restore from backup
function Restore-Backup {
    param([string]$BackupFile)
    
    if (!(Test-Path $BackupFile)) {
        Write-Error "Backup file not found: $BackupFile"
    }
    
    Write-Log "Restoring from backup: $BackupFile"
    Write-Warn "This will OVERWRITE the current database!"
    
    $Confirmation = Read-Host "Are you sure you want to continue? (y/N)"
    if ($Confirmation -notmatch "^[Yy]$") {
        Write-Log "Restore cancelled"
        return
    }
    
    try {
        $env:PGPASSWORD = $DB_PASSWORD
        
        # Determine file type and restore accordingly
        if ($BackupFile -like "*.custom") {
            Write-Log "Restoring from custom format backup..."
            & pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
                         --verbose --clean --if-exists --no-privileges --no-owner `
                         $BackupFile
        } elseif ($BackupFile -like "*.gz") {
            Write-Log "Restoring from compressed SQL backup..."
            & gunzip -c $BackupFile | & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
        } else {
            Write-Log "Restoring from SQL backup..."
            & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $BackupFile
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Restore completed successfully"
        } else {
            Write-Error "Restore failed"
        }
        
    } catch {
        Write-Error "Restore failed: $($_.Exception.Message)"
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# Clean old backups
function Remove-OldBackups {
    param([int]$Days = 7)
    
    Write-Log "Cleaning up backups older than $Days days..."
    
    $CutoffDate = (Get-Date).AddDays(-$Days)
    
    if (Test-Path $BackupDir) {
        $OldBackups = Get-ChildItem $BackupDir -Filter "*.sql*" | Where-Object { $_.LastWriteTime -lt $CutoffDate }
        if ($OldBackups) {
            foreach ($backup in $OldBackups) {
                Remove-Item $backup.FullName -Force
            }
            Write-Log "Deleted $($OldBackups.Count) old backup files"
        } else {
            Write-Log "No old backups to clean up"
        }
    }
    
    # Clean old WAL files if they exist
    if (Test-Path $WalDir) {
        $OldWalFiles = Get-ChildItem $WalDir -Filter "*.backup" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $CutoffDate }
        if ($OldWalFiles) {
            foreach ($wal in $OldWalFiles) {
                Remove-Item $wal.FullName -Force
            }
            Write-Log "Deleted $($OldWalFiles.Count) old WAL files"
        }
    }
}

# Show usage
function Show-Help {
    Write-Host "Database Backup Script for Multi-Tenant SaaS (PowerShell)"
    Write-Host ""
    Write-Host "Usage: .\backup.ps1 -Command [command] -Parameter [parameter]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  full                    - Create full database backup"
    Write-Host "  schema                  - Backup specific tenant schema (requires -Parameter)"
    Write-Host "  list                    - List all available backups"
    Write-Host "  restore                 - Restore from backup file (requires -Parameter)"
    Write-Host "  cleanup                 - Clean backups older than N days (optional -Parameter, default: 7)"
    Write-Host "  help                    - Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\backup.ps1 -Command full"
    Write-Host "  .\backup.ps1 -Command schema -Parameter tenant1"
    Write-Host "  .\backup.ps1 -Command restore -Parameter 'backups\full_backup_20231201_143022.sql.gz'"
    Write-Host "  .\backup.ps1 -Command cleanup -Parameter 30"
    Write-Host ""
    Write-Host "Requirements:"
    Write-Host "  - PostgreSQL client tools (pg_dump, pg_restore, psql)"
    Write-Host "  - Database running on $DB_HOST`:$DB_PORT"
    Write-Host "  - gzip utility for compression"
}

# Main command processing
switch ($Command.ToLower()) {
    "full" {
        if (Test-DatabaseConnection) {
            Backup-Full
        }
    }
    
    "schema" {
        if ([string]::IsNullOrEmpty($Parameter)) {
            Write-Error "Schema name required. Usage: .\backup.ps1 -Command schema -Parameter <schema_name>"
        }
        if (Test-DatabaseConnection) {
            Backup-Schema -SchemaName $Parameter
        }
    }
    
    "list" {
        Get-BackupList
    }
    
    "restore" {
        if ([string]::IsNullOrEmpty($Parameter)) {
            Write-Error "Backup file required. Usage: .\backup.ps1 -Command restore -Parameter <backup_file>"
        }
        if (Test-DatabaseConnection) {
            Restore-Backup -BackupFile $Parameter
        }
    }
    
    "cleanup" {
        $days = if ([string]::IsNullOrEmpty($Parameter)) { 7 } else { [int]$Parameter }
        Remove-OldBackups -Days $days
    }
    
    default {
        Show-Help
    }
}
