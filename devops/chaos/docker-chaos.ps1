param(
  [int]$DurationMinutes = 3,
  [int]$MinWaitSec = 5,
  [int]$MaxWaitSec = 15
)

$services = @('web','db','redis')
$end = (Get-Date).AddMinutes($DurationMinutes)

Write-Host "Starting Docker chaos for $DurationMinutes minute(s)"

while((Get-Date) -lt $end){
  $svc = Get-Random -InputObject $services
  Write-Host "[chaos] restarting $svc..."
  docker compose -f devops/docker/docker-compose.yml restart $svc | Out-Null
  Start-Sleep -Seconds (Get-Random -Minimum $MinWaitSec -Maximum $MaxWaitSec)
}

Write-Host "[chaos] done."
