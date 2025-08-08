param(
    [string]$Scenario = "smoke",
    [string]$Host = "http://localhost:8000"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$LocustFile = Join-Path $ScriptDir "locustfile.py"

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

# Check if locust is installed
try {
    locust --version | Out-Null
} catch {
    Write-Error "Locust is not installed. Run: pip install locust"
}

# Check if app is running
Write-Log "Checking if application is running at $Host..."
try {
    $response = Invoke-WebRequest -Uri $Host -Method GET -TimeoutSec 5 -ErrorAction Stop
} catch {
    Write-Warn "Application may not be running at $Host"
    Write-Warn "Start with: docker compose -f devops/docker/docker-compose.yml up -d"
}

switch ($Scenario.ToLower()) {
    "smoke" {
        Write-Log "Running smoke test (10 users, 30 seconds)..."
        locust -f $LocustFile --headless -u 10 -r 2 -t 30s --host=$Host --only-summary
    }
    
    "quick" {
        Write-Log "Running quick test (50 users, 2 minutes)..."
        locust -f $LocustFile --headless -u 50 -r 10 -t 120s --host=$Host --csv=quick-test
    }
    
    "stress" {
        Write-Log "Running stress test (200 users, 5 minutes)..."
        locust -f $LocustFile --headless -u 200 -r 20 -t 300s --host=$Host --csv=stress-test
    }
    
    "sustained" {
        Write-Log "Running sustained load test (100 users, 10 minutes)..."
        locust -f $LocustFile --headless -u 100 -r 10 -t 600s --host=$Host --csv=sustained-test
    }
    
    "ui" {
        Write-Log "Starting Locust web UI at http://localhost:8089"
        locust -f $LocustFile --host=$Host
    }
    
    "anonymous" {
        Write-Log "Testing anonymous users only (30 users, 2 minutes)..."
        locust -f $LocustFile AnonymousUser --headless -u 30 -r 5 -t 120s --host=$Host --csv=anonymous-test
    }
    
    "authenticated" {
        Write-Log "Testing authenticated users only (20 users, 2 minutes)..."
        locust -f $LocustFile AuthenticatedUser --headless -u 20 -r 5 -t 120s --host=$Host --csv=auth-test
    }
    
    "burst" {
        Write-Log "Running burst traffic test (100 users, 1 minute)..."
        locust -f $LocustFile BurstTraffic --headless -u 100 -r 50 -t 60s --host=$Host --csv=burst-test
    }
    
    "clean" {
        Write-Log "Cleaning up old test results..."
        Remove-Item -Path "*.csv", "*.html", "locust.log" -ErrorAction SilentlyContinue
        Write-Log "Cleanup complete"
    }
    
    default {
        Write-Host "Load Testing Runner"
        Write-Host ""
        Write-Host "Usage: .\run_tests.ps1 -Scenario [scenario] -Host [host]"
        Write-Host ""
        Write-Host "Scenarios:"
        Write-Host "  smoke      - Quick smoke test (10 users, 30s)"
        Write-Host "  quick      - Quick test (50 users, 2min)"
        Write-Host "  stress     - Stress test (200 users, 5min)"
        Write-Host "  sustained  - Sustained load (100 users, 10min)"
        Write-Host "  ui         - Start web UI"
        Write-Host "  anonymous  - Test anonymous users only"
        Write-Host "  authenticated - Test authenticated users only"
        Write-Host "  burst      - Burst traffic test"
        Write-Host "  clean      - Clean up test results"
        Write-Host "  help       - Show this help"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\run_tests.ps1 -Scenario smoke"
        Write-Host "  .\run_tests.ps1 -Scenario quick -Host https://staging.app.com"
    }
}
