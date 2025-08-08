# Load Testing

This directory contains Locust configuration for load testing the Multi-Tenant SaaS application.

## Prerequisites

```bash
pip install locust
```

## Quick Start

1. **Start your application** (via Docker or locally):
   ```bash
   # Using Docker
   cd devops/docker
   docker compose up -d
   
   # Or locally
   python manage.py runserver
   ```

2. **Run basic load test**:
   ```bash
   # From project root
   locust -f devops/loadtest/locustfile.py
   ```

3. **Open Locust Web UI**: http://localhost:8089

## Test Scenarios

### User Types (by weight)

- **AnonymousUser** (weight: 3) - Most traffic
  - Browse homepage, login/register pages, billing plans
  - Simulates visitors and potential customers

- **AuthenticatedUser** (weight: 2) - Regular users  
  - Dashboard, analytics, tenant management
  - Typical day-to-day usage patterns

- **AdminUser** (weight: 1) - Power users
  - Heavy tenant management, deep analytics
  - Administrative operations

- **SlowUser** (weight: 1) - Slow connections
  - Long pauses between requests
  - Simulates mobile/slow internet users

- **BurstTraffic** (weight: 0, disabled) - Traffic spikes
  - Rapid-fire requests
  - Enable manually for stress testing

## Running Specific Scenarios

```bash
# Test only anonymous users
locust -f devops/loadtest/locustfile.py AnonymousUser

# Test authenticated users only  
locust -f devops/loadtest/locustfile.py AuthenticatedUser

# Enable burst traffic (stress test)
locust -f devops/loadtest/locustfile.py BurstTraffic

# Run headless (no web UI)
locust -f devops/loadtest/locustfile.py --headless -u 50 -r 10 -t 300s
```

## Configuration Options

### Headless Mode
```bash
# 50 users, spawn 10/sec, run for 5 minutes
locust -f devops/loadtest/locustfile.py --headless -u 50 -r 10 -t 300s --host=http://localhost:8000
```

### Custom Host
```bash
# Test against staging
locust -f devops/loadtest/locustfile.py --host=https://staging.yourapp.com
```

### CSV Results
```bash
# Export results to CSV
locust -f devops/loadtest/locustfile.py --headless -u 100 -r 20 -t 60s --csv=results
```

## Interpreting Results

### Key Metrics
- **RPS (Requests Per Second)**: Throughput
- **Response Time**: 50th, 95th, 99th percentiles  
- **Failure Rate**: % of failed requests
- **Users**: Number of concurrent simulated users

### Performance Targets
- **Response Time**: < 200ms (95th percentile)
- **Failure Rate**: < 1%
- **RPS**: Depends on expected load

### Red Flags
- Response times > 1s consistently
- High failure rates (>5%)
- Memory/CPU usage spiking
- Database connection errors

## Advanced Usage

### Custom Test Data
Modify `locustfile.py` to use real test data:

```python
class AuthenticatedUser(HttpUser):
    def on_start(self):
        # Login with test user
        self.client.post("/accounts/login/", {
            "username": "testuser@example.com",
            "password": "testpass123"
        })
```

### API Load Testing
Enable `ApiUser` class for API endpoint testing:

```python
class ApiUser(HttpUser):
    weight = 2  # Enable API testing
    
    @task
    def api_call(self):
        self.client.get("/api/v1/tenants/", 
                       headers={"Authorization": "Bearer token"})
```

### Database Stress Testing
Add POST requests that create/modify data:

```python
@task
def create_tenant(self):
    self.client.post("/tenants/create/", {
        "name": f"Test Tenant {random.randint(1000, 9999)}",
        "schema_name": f"test{random.randint(1000, 9999)}"
    })
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Load Test
  run: |
    locust -f devops/loadtest/locustfile.py --headless \
           -u 100 -r 10 -t 60s --csv=loadtest-results \
           --host=http://localhost:8000
    
    # Fail if 95th percentile > 500ms or failure rate > 1%
    python scripts/check_performance.py loadtest-results_stats.csv
```

### Performance Monitoring
- Monitor application metrics during tests
- Watch database performance
- Check memory/CPU usage
- Monitor cache hit rates

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure app is running on correct port
   - Check `--host` parameter

2. **High Failure Rates**
   - Check Django logs
   - Verify database connections
   - Monitor resource usage

3. **CSRF Errors**
   - Disable CSRF for load testing (test environment only)
   - Or implement proper CSRF token handling

4. **Authentication Issues**
   - Create test users in advance
   - Use Django's test client for complex auth flows

### Performance Optimization Tips
- Use database connection pooling
- Enable caching (Redis)
- Optimize database queries
- Use CDN for static files
- Consider read replicas for analytics

## Example Commands

```bash
# Quick smoke test (10 users, 30 seconds)
locust -f devops/loadtest/locustfile.py --headless -u 10 -r 2 -t 30s

# Stress test (500 users, 10 minutes)  
locust -f devops/loadtest/locustfile.py --headless -u 500 -r 50 -t 600s

# Sustained load (100 users, 1 hour)
locust -f devops/loadtest/locustfile.py --headless -u 100 -r 10 -t 3600s

# Profile specific endpoint
locust -f devops/loadtest/locustfile.py AuthenticatedUser --headless -u 20 -r 5 -t 120s
```
