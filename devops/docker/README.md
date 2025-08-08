# Docker & Database Management

This directory contains Docker configuration and database management scripts for the Multi-Tenant SaaS application.

## Directory Structure

```
devops/docker/
├── docker-compose.yml     # Main services configuration
├── apps/Dockerfile       # Application container
├── nginx/default.conf    # Nginx proxy configuration
├── wal/                  # PostgreSQL WAL archive directory
├── backups/              # Database backup storage (created automatically)
├── backup.sh             # Database backup script (Linux/macOS)
├── backup.ps1            # Database backup script (Windows)
└── README.md             # This file
```

## Quick Start

### 1. Start Services
```bash
# Start all services (web, database, redis, nginx)
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps
```

### 2. Database Setup
```bash
# Run initial migrations (automatically done on startup)
docker compose exec web python manage.py migrate_schemas --shared

# Create superuser
docker compose exec web python manage.py createsuperuser

# Create a test tenant
docker compose exec web python manage.py create_tenant --name "Test Company" --schema "test"
```

### 3. Access Application
- **Web Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Database**: localhost:5433 (external), db:5432 (internal)
- **Redis**: localhost:6379

## Services Configuration

### Web Service
- **Image**: Built from `apps/Dockerfile`
- **Port**: 8000
- **Volumes**: Source code mounted for development
- **Environment**: Configured via `../env/.env.dev`

### Database Service
- **Image**: postgres:14
- **Port**: 5433 (external), 5432 (internal)
- **Database**: multitenant_saas
- **User/Password**: saasadmin/supersecret123
- **Features**:
  - Data checksums enabled
  - WAL archiving to `./wal/` directory
  - Health check configured
  - Persistent volume for data

### Redis Service
- **Image**: redis:7-alpine
- **Port**: 6379
- **Features**:
  - AOF persistence enabled
  - Persistent volume for data

### Nginx Service
- **Image**: nginx:alpine
- **Port**: 80
- **Purpose**: Reverse proxy and static file serving

## Database Backup & Recovery

### Backup Scripts

**Linux/macOS:**
```bash
# Full database backup
./backup.sh full

# Backup specific tenant schema
./backup.sh schema tenant1

# List all backups
./backup.sh list

# Restore from backup
./backup.sh restore backups/full_backup_20231201_143022.sql.gz

# Clean old backups (older than 7 days)
./backup.sh cleanup

# Clean old backups (custom days)
./backup.sh cleanup 30
```

**Windows (PowerShell):**
```powershell
# Full database backup
.\backup.ps1 -Command full

# Backup specific tenant schema
.\backup.ps1 -Command schema -Parameter tenant1

# List all backups
.\backup.ps1 -Command list

# Restore from backup
.\backup.ps1 -Command restore -Parameter "backups\full_backup_20231201_143022.sql.gz"

# Clean old backups
.\backup.ps1 -Command cleanup -Parameter 30
```

### WAL (Write-Ahead Logging) Archiving

PostgreSQL is configured to archive WAL files to the `./wal/` directory:

- **Purpose**: Point-in-time recovery and continuous backup
- **Location**: `devops/docker/wal/`
- **Retention**: Managed by backup cleanup scripts
- **Configuration**: Set in `docker-compose.yml` via volume mount

**Benefits:**
- Continuous backup without interrupting database operations
- Point-in-time recovery capabilities
- Minimal data loss in case of failures

### Backup Types

1. **Full Backup** (`backup.sh full`):
   - Complete database dump
   - All schemas (public + tenant schemas)
   - Two formats: SQL (compressed) and PostgreSQL custom

2. **Schema Backup** (`backup.sh schema <name>`):
   - Single tenant schema only
   - Useful for tenant-specific recovery
   - Compressed SQL format

3. **WAL Archives**:
   - Continuous transaction log backup
   - Automatic via PostgreSQL configuration
   - Stored in `./wal/` directory

## Environment Configuration

Create `../env/.env.dev` with:

```env
DEBUG=True
SECRET_KEY=changeme-in-development
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
DB_NAME=multitenant_saas
DB_USER=saasadmin
DB_PASSWORD=supersecret123
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1

# Email (development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Development Workflow

### Daily Development
```bash
# Start services
docker compose up -d

# View application logs
docker compose logs -f web

# Access application shell
docker compose exec web python manage.py shell

# Run tests
docker compose exec web python manage.py test

# Stop services
docker compose down
```

### Database Maintenance
```bash
# Create daily backup
./backup.sh full

# Clean old backups weekly
./backup.sh cleanup 7

# Check database status
docker compose exec db pg_isready -U saasadmin

# Connect to database
docker compose exec db psql -U saasadmin -d multitenant_saas
```

## Troubleshooting

### Common Issues

1. **Services won't start**:
   ```bash
   # Check logs for errors
   docker compose logs
   
   # Rebuild containers
   docker compose build --no-cache
   docker compose up -d
   ```

2. **Database connection errors**:
   ```bash
   # Check if database is ready
   docker compose exec db pg_isready -U saasadmin
   
   # Check database logs
   docker compose logs db
   ```

3. **Permission issues**:
   ```bash
   # Fix WAL directory permissions
   sudo chown -R 999:999 ./wal/
   
   # Fix backup directory permissions
   sudo chown -R $USER:$USER ./backups/
   ```

4. **Backup/restore failures**:
   ```bash
   # Ensure PostgreSQL client tools are installed
   which pg_dump pg_restore psql
   
   # Check database connectivity
   pg_isready -h localhost -p 5433 -U saasadmin
   ```

### Database Recovery Scenarios

**Scenario 1: Corrupt tenant schema**
```bash
# Backup current state
./backup.sh full

# Restore specific tenant from backup
./backup.sh restore backups/schema_tenant1_20231201_143022.sql.gz
```

**Scenario 2: Complete data loss**
```bash
# Stop services
docker compose down

# Remove data volume
docker volume rm docker_pgdata

# Start services (fresh database)
docker compose up -d

# Restore from latest backup
./backup.sh restore backups/full_backup_20231201_143022.sql.gz

# Run migrations
docker compose exec web python manage.py migrate_schemas --shared
```

**Scenario 3: Point-in-time recovery**
```bash
# Use WAL files for point-in-time recovery
# (Advanced scenario - requires PostgreSQL expertise)
# Contact DBA or use professional backup solution
```

## Production Considerations

### Security
- Change default passwords
- Use Docker secrets for sensitive data
- Enable SSL/TLS for database connections
- Configure firewall rules

### Performance
- Use external database for production
- Configure connection pooling
- Set up read replicas for analytics
- Use external Redis cluster

### Backup Strategy
- Automated daily full backups
- Continuous WAL archiving
- Off-site backup storage
- Regular restore testing
- Document recovery procedures

### Monitoring
- Database health checks
- Backup success/failure alerts
- Storage space monitoring
- Performance metrics collection

## Integration with Load Testing & Chaos Engineering

This Docker setup is designed to work with:

- **Load Testing**: `../loadtest/` - Run Locust against `http://localhost:8000`
- **Chaos Engineering**: `../chaos/` - Random container restarts and network issues
- **Performance Testing**: Monitor database under load using backup/restore operations

Example combined testing:
```bash
# Terminal 1: Start chaos engineering
../chaos/docker-chaos.sh 300 10 20

# Terminal 2: Run load test
../loadtest/run_tests.sh stress

# Terminal 3: Create backup during load
./backup.sh full
```
