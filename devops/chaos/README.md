# Chaos Engineering (Development)

This directory contains chaos engineering scripts to help test the resilience of your Multi-Tenant SaaS application by introducing controlled failures in development.

## Prerequisites

- Docker Desktop running
- Docker Compose services defined in `devops/docker/docker-compose.yml`
- Service names: `web`, `db`, `redis`

## Available Scripts

### Docker Chaos (Random Container Restarts)

**Windows (PowerShell):**
```powershell
# Run for 5 minutes with restarts every 5-20 seconds
powershell -ExecutionPolicy Bypass -File devops/chaos/docker-chaos.ps1 -DurationMinutes 5 -MinWaitSec 5 -MaxWaitSec 20

# Quick 2-minute test
.\devops\chaos\docker-chaos.ps1 -DurationMinutes 2
```

**Linux/macOS (Bash):**
```bash
# Run for 300 seconds (5 minutes) with restarts every 5-20 seconds
bash devops/chaos/docker-chaos.sh 300 5 20

# Quick 60-second test
bash devops/chaos/docker-chaos.sh 60 10 15
```

### Network Latency Simulation (Linux only)

**Add network latency:**
```bash
# Add 200ms latency to web service
sudo bash devops/chaos/netem.sh add web 200ms

# Add 500ms latency to database
sudo bash devops/chaos/netem.sh add db 500ms
```

**Remove latency:**
```bash
# Clear latency from web service
sudo bash devops/chaos/netem.sh clear web

# Clear all latency
sudo bash devops/chaos/netem.sh clear all
```

## What Gets Tested

### Container Restart Scenarios
- **Web service restarts**: Tests application startup resilience and database reconnection
- **Database restarts**: Tests connection pooling and transaction recovery
- **Redis restarts**: Tests cache invalidation and session handling

### Network Latency Scenarios
- **High latency**: Simulates slow network conditions
- **Intermittent connectivity**: Tests timeout handling

## Monitoring During Chaos

While chaos tests are running, monitor:

1. **Application Health**:
   ```bash
   # Check if services are responding
   curl http://localhost:8000/
   curl http://localhost:8000/accounts/login/
   ```

2. **Docker Service Status**:
   ```bash
   docker compose -f devops/docker/docker-compose.yml ps
   ```

3. **Application Logs**:
   ```bash
   docker compose -f devops/docker/docker-compose.yml logs -f web
   ```

4. **Database Connections**:
   ```bash
   docker compose -f devops/docker/docker-compose.yml exec db psql -U saasadmin -d multitenant_saas -c "SELECT count(*) FROM pg_stat_activity;"
   ```

## Expected Behaviors

### Good Resilience Indicators ✅
- Application recovers quickly after service restarts
- No data corruption or lost transactions
- Users can continue working after brief interruptions
- Database connections are properly re-established
- Cache gracefully handles Redis restarts

### Warning Signs ⚠️
- Long recovery times (>30 seconds)
- Failed database connections that don't recover
- Lost user sessions that don't gracefully redirect
- Error 500 pages that persist after service recovery

### Critical Issues 🚨
- Data corruption
- Permanent service failures
- Security vulnerabilities exposed during restarts
- Complete application unavailability

## Example Chaos Scenarios

### Scenario 1: Database Resilience Test
```powershell
# Start chaos focused on database
.\devops\chaos\docker-chaos.ps1 -DurationMinutes 3 -MinWaitSec 10 -MaxWaitSec 30
```

Then test:
- User login/logout during database restarts
- Dashboard data loading
- Tenant creation/management
- Analytics page performance

### Scenario 2: Cache Invalidation Test
```bash
# Restart Redis frequently
# (Modify the scripts to target only Redis if needed)
bash devops/chaos/docker-chaos.sh 180 5 15
```

Then test:
- Dashboard performance without cache
- System settings loading
- Analytics data generation

### Scenario 3: Full System Stress
```powershell
# Combine with load testing
# Terminal 1: Start chaos
.\devops\chaos\docker-chaos.ps1 -DurationMinutes 10

# Terminal 2: Start load test
.\devops\loadtest\run_tests.ps1 -Scenario stress
```

## Safety Guidelines

⚠️ **Important**: Only use in development environments!

- Never run chaos engineering on production systems
- Ensure you have recent backups before testing
- Start with short durations (1-2 minutes) to understand impact
- Monitor system resources during tests
- Have a plan to quickly stop chaos tests if needed

## Stopping Chaos Tests

**Windows**: Press `Ctrl+C` in the PowerShell window
**Linux/macOS**: Press `Ctrl+C` in the terminal

**Emergency stop all containers**:
```bash
docker compose -f devops/docker/docker-compose.yml stop
docker compose -f devops/docker/docker-compose.yml start
```

## Integration with CI/CD

Include chaos testing in your pipeline:

```yaml
# .github/workflows/chaos-test.yml
- name: Chaos Engineering Test
  run: |
    # Start services
    docker compose -f devops/docker/docker-compose.yml up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Run chaos test for 2 minutes
    timeout 120s bash devops/chaos/docker-chaos.sh 120 10 20 || true
    
    # Verify system is still healthy
    curl -f http://localhost:8000/ || exit 1
```

## Extending Chaos Tests

Add your own chaos scenarios by creating new scripts:

- **Memory pressure**: Limit container memory
- **CPU throttling**: Limit container CPU
- **Disk I/O issues**: Simulate slow disk
- **Network partitions**: Block communication between services

Remember: The goal is to find weaknesses before your users do! 🛡️
