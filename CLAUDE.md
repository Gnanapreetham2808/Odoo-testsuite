# CLAUDE.md

## What this is

`sample_state_machine/` is an Odoo **19.0** capability-sample module. It adds a state machine on the
custom model `sample.booking`: 5 states (`draft`, `submitted`, `approved`, `done`, `cancelled`),
7 regular transitions and 1 manager-only override (`force_cancel`, done → cancelled). The transition
table is plain Python (`transitions.py`, it does not import Odoo). There is also one plain HTTP route,
`GET /sample/booking/<id>/status`, and tests. The module depends only on `base`, so Odoo Community is enough.

Repo layout (repo root = this folder; the module is the `sample_state_machine/` subfolder):

- `docker-compose.yml`: `postgres:16` + `odoo:19.0`. The module is mounted at `/mnt/extra-addons/sample_state_machine`.
- `config/odoo.conf`: dev config (addons path, DB connection). Dev-only credentials.
- `scripts/*.ps1`: the three day-to-day jobs (below). `.vscode/tasks.json` wraps them.

## Running things (PowerShell, from the repo root; Docker Desktop must be running)

| Job | Command |
|---|---|
| Plain tests (no Odoo, no DB) | `.\scripts\test-plain.ps1` |
| Full Odoo suite, fresh DB | `.\scripts\test-odoo.ps1` |
| Odoo subset by tag | `.\scripts\test-odoo.ps1 -Tags sample_sm_model` |
| Start Odoo for manual testing | `.\scripts\start-odoo.ps1` (`-Reset` to recreate the DB), then http://localhost:8069, admin / admin |
| Stop | `docker compose stop` |

What the scripts run:

- Plain: `cd sample_state_machine; python tests/plain/test_transitions_plain.py`. Expect 7 tests OK.
- Full: `docker compose run --rm odoo odoo -d sm_test_<timestamp> -i sample_state_machine --test-tags=/sample_state_machine --without-demo=all --stop-after-init`.
  Expect `0 failed, 0 error(s) of 22 tests` (7 wrapper + 10 model + 5 HTTP). The test DB is dropped afterwards (`-KeepDb` keeps it).
- Always test on a **fresh database with `-i`**. Never use `-u` for the full run, because it skips the `at_install` tests.

If PowerShell blocks the scripts, run `powershell -ExecutionPolicy Bypass -File .\scripts\<name>.ps1`.

## Test tags

- `sample_sm`: all module tests
- `sample_sm_plain`: transition-table checks run inside Odoo (wrapper)
- `sample_sm_model`: `TransactionCase` model tests
- `sample_sm_http`: `HttpCase` route tests

## Gotchas

- Run the plain test **by file path**, not with `python -m unittest`. The module's package `__init__.py` imports Odoo, so importing it as a package fails without Odoo.
- Odoo's test loader only collects test methods defined on the class itself. The wrapper class in `tests/test_transitions_wrapper.py` inherits its checks, so it needs `allow_inherited_tests_method = True`. Do not remove it, or the 7 wrapper tests silently disappear.
- `HttpCase` and `TransactionCase` tests need a database, so they only run through Odoo (`scripts/test-odoo.ps1`). They do not run with plain Python.
- The "Sample Bookings" menu is restricted to the booking groups. `start-odoo.ps1` adds admin to Booking Manager in `odoo_dev` only. That is dev-DB setup, not module data.

## Rules for this module

- It is a sample that will be **sent to an external client for review**. It must contain nothing from that client's business: no real names, no real data, fictitious data only.
- Never use the phrase "supplier payment gate" or any payment-provider names anywhere in the module.
- Keep `base` as the **only** dependency in `__manifest__.py`.
- Use Odoo 19 conventions: `<list>` not `<tree>`; `models.Constraint` instead of `_sql_constraints` if SQL constraints are ever added; `check_access` instead of `check_access_rights`.
- Do not commit secrets or `.env` files. The credentials in `docker-compose.yml` / `config/odoo.conf` are local dev placeholders only.
