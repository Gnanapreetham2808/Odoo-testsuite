# Runs a module's tests under coverage.py on a FRESH database, then prints the coverage summary
# for that module only (its tests/ folder excluded).
#   .\scripts\coverage-odoo.ps1 -Module hr_holidays
#   .\scripts\coverage-odoo.ps1 -Module hr_holidays -Tags /hr_holidays:TestHolidaysFlow
# Needs coverage.py inside the Odoo container (installed with pip --user into the odoo-web-data volume);
# see README.md for how to install it.
param(
    [string]$Module = 'sample_state_machine',
    [string]$Tags = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Tags) { $Tags = "/$Module" }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $db = 'cov_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
    # Stock modules live in the image; custom ones are mounted under /mnt/extra-addons.
    $src = if (Test-Path (Join-Path (Get-Location) $Module)) { "/mnt/extra-addons/$Module" } else { "/usr/lib/python3/dist-packages/odoo/addons/$Module" }
    $data = "/var/lib/odoo/.coverage_$Module"

    docker compose up -d --wait db
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the database container (is Docker Desktop running?)' }

    Write-Host "== Coverage run on fresh database $db  module: $Module  tags: $Tags" -ForegroundColor Cyan
    $cmd = "python3 -m coverage run --data-file=$data --source=$src /usr/bin/odoo -d $db -i $Module " +
           "--test-tags=$Tags --without-demo=all --stop-after-init --log-level=warn --log-handler=odoo.tests.result:INFO --log-handler=odoo.tests.stats:INFO; rc=`$?; " +
           "python3 -m coverage report --data-file=$data --omit='*/tests/*' --skip-empty; exit `$rc"
    docker compose run --rm --no-deps -T --entrypoint sh odoo -c $cmd
    $rc = $LASTEXITCODE

    docker compose exec -T db dropdb -U odoo --if-exists $db | Out-Null
    docker compose run --rm --no-deps --entrypoint rm odoo -rf "/var/lib/odoo/filestore/$db" | Out-Null
    exit $rc
} finally {
    Pop-Location
}
