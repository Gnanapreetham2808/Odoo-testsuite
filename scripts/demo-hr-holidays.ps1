# Runs scripts/demo_hr_holidays.py through `odoo shell` against the scratch database hr_demo.
#   .\scripts\demo-hr-holidays.ps1          # create hr_demo on first run (hr_holidays, no demo data), then run the demo
#   .\scripts\demo-hr-holidays.ps1 -Reset   # drop and recreate hr_demo first
# The demo rolls back its own changes, so it can be re-run on the same database.
param([switch]$Reset)
$ErrorActionPreference = 'Stop'
$db = 'hr_demo'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    docker compose up -d --wait db
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the database container (is Docker Desktop running?)' }

    if ($Reset) {
        docker compose exec -T db dropdb -U odoo --if-exists $db
        docker compose run --rm --no-deps --entrypoint rm odoo -rf "/var/lib/odoo/filestore/$db" | Out-Null
    }
    $exists = docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'"
    if ("$exists".Trim() -ne '1') {
        Write-Host "== Creating scratch database $db with hr_holidays" -ForegroundColor Cyan
        docker compose run --rm --no-deps odoo odoo -d $db -i hr_holidays --without-demo=all --stop-after-init --log-level=warn
        if ($LASTEXITCODE -ne 0) { throw 'hr_holidays install failed' }
    }

    # The scripts folder is mounted read-only; the file is fed to odoo shell inside the container.
    docker compose run --rm -T --no-deps -v "${PWD}/scripts:/mnt/scripts:ro" --entrypoint sh odoo `
        -c "odoo shell -d $db --no-http --log-level=warn < /mnt/scripts/demo_hr_holidays.py"
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
