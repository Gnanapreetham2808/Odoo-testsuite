# Runs the Odoo test suite on a FRESH database (-i on a new DB; never -u, which skips at_install tests).
#   .\scripts\test-odoo.ps1                      # all module tests (/sample_state_machine)
#   .\scripts\test-odoo.ps1 -Tags sample_sm_model # a subset by tag
#   .\scripts\test-odoo.ps1 -KeepDb               # keep the test DB for inspection
param(
    [string]$Tags = '/sample_state_machine',
    [switch]$KeepDb
)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $db = 'sm_test_' + (Get-Date -Format 'yyyyMMdd_HHmmss')

    docker compose up -d --wait db
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the database container (is Docker Desktop running?)' }

    Write-Host "== Fresh database: $db  tags: $Tags" -ForegroundColor Cyan
    # Odoo logs to stderr; merge it into the pipeline without PowerShell treating it as an error.
    $ErrorActionPreference = 'Continue'
    & docker compose run --rm --no-deps odoo odoo -d $db -i sample_state_machine `
        "--test-tags=$Tags" --without-demo=all --stop-after-init 2>&1 |
        ForEach-Object { "$_" } | Tee-Object -Variable lines | Out-Host
    $rc = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'

    if (-not $KeepDb) {
        docker compose exec -T db dropdb -U odoo --if-exists $db | Out-Null
        docker compose run --rm --no-deps --entrypoint rm odoo -rf "/var/lib/odoo/filestore/$db" | Out-Null
    } else {
        Write-Host "Kept database $db" -ForegroundColor Yellow
    }

    $summary = $lines | Select-String -Pattern '(\d+) failed, (\d+) error\(s\) of (\d+) tests' | Select-Object -Last 1
    if (-not $summary) {
        Write-Host 'FAILED: no test summary line found in the Odoo log.' -ForegroundColor Red
        exit 1
    }
    $m = $summary.Matches[0].Groups
    $failed = [int]$m[1].Value; $errors = [int]$m[2].Value; $total = [int]$m[3].Value
    Write-Host "== $failed failed, $errors error(s) of $total tests (odoo exit code $rc)" -ForegroundColor Cyan
    if ($rc -ne 0 -or $failed -ne 0 -or $errors -ne 0 -or $total -eq 0) { exit 1 }
    exit 0
} finally {
    Pop-Location
}
