# Starts Odoo on http://localhost:8069 with sample_state_machine and the stock Time Off app
# (hr_holidays) installed in database odoo_dev.
#   .\scripts\start-odoo.ps1          # create odoo_dev on first run, otherwise upgrade/install the modules
#   .\scripts\start-odoo.ps1 -Reset   # drop odoo_dev and start from scratch
# Login: admin / admin. The admin user is added to "Booking Manager" so the menu is visible.
# Stop with: docker compose stop   |  Logs: docker compose logs -f odoo
param([switch]$Reset)
$ErrorActionPreference = 'Stop'
$db = 'odoo_dev'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    docker compose up -d --wait db
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the database container (is Docker Desktop running?)' }

    docker compose stop odoo | Out-Null
    if ($Reset) {
        docker compose exec -T db dropdb -U odoo --if-exists $db
        docker compose run --rm --no-deps --entrypoint rm odoo -rf "/var/lib/odoo/filestore/$db" | Out-Null
    }

    $exists = docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'"
    if ("$exists".Trim() -ne '1') {
        Write-Host "== Creating $db and installing sample_state_machine + Time Off (hr_holidays)" -ForegroundColor Cyan
        docker compose run --rm --no-deps odoo odoo -d $db -i sample_state_machine,hr_holidays --without-demo=all --stop-after-init
        if ($LASTEXITCODE -ne 0) { throw 'Module install failed' }
    } else {
        # -i hr_holidays installs Time Off on databases created before it was part of the setup;
        # it does nothing if it is already installed.
        Write-Host "== Upgrading sample_state_machine (and making sure Time Off is installed) in $db" -ForegroundColor Cyan
        docker compose run --rm --no-deps odoo odoo -d $db -u sample_state_machine -i hr_holidays --stop-after-init
        if ($LASTEXITCODE -ne 0) { throw 'Module upgrade failed' }
    }

    # Dev DB only: put admin in Booking Manager so the "Sample Bookings" menu is visible (idempotent).
    $py = @'
admin = env.ref('base.user_admin')
group = env.ref('sample_state_machine.group_sample_booking_manager')
field = 'group_ids' if 'group_ids' in admin._fields else 'groups_id'
admin.write({field: [(4, group.id)]})
env.cr.commit()
print('admin is in group:', group.name)
'@
    # Windows PowerShell may prepend a BOM when piping to a native command; strip it in the container.
    $py | docker compose run --rm -T --no-deps --entrypoint sh odoo -c "sed '1s/^\xEF\xBB\xBF//' | odoo shell -d $db --no-http --log-level=warn"
    if ($LASTEXITCODE -ne 0) { throw 'Could not add admin to the Booking Manager group' }

    docker compose up -d odoo
    Write-Host 'Waiting for http://localhost:8069 ...'
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8069/web/login' -TimeoutSec 3
            if ($r.StatusCode -eq 200) { Write-Host "Odoo is up: http://localhost:8069  (admin / admin)" -ForegroundColor Green; exit 0 }
        } catch { Start-Sleep -Seconds 2 }
    }
    throw 'Odoo did not answer on http://localhost:8069 (see: docker compose logs odoo)'
} finally {
    Pop-Location
}
