# Runs the plain-Python transition tests (no Odoo, no database).
# Run by file path: the module's package __init__ imports Odoo, so `python -m` would fail.
$ErrorActionPreference = 'Stop'
$module = Join-Path (Split-Path -Parent $PSScriptRoot) 'sample_state_machine'
Push-Location $module
try {
    python tests/plain/test_transitions_plain.py -v
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
