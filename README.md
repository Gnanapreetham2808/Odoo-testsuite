# Odoo 19 state machine: sample module + hr_holidays tests

Two Odoo **19.0 Community** modules that run locally in Docker:

| Folder | What it is | Tests |
|---|---|---|
| [`hr_holidays_state_tests/`](hr_holidays_state_tests/) | Test suite for the existing Odoo **Time Off** module (`hr_holidays`). It checks every state transition of a time-off request (`hr.leave`), plus the moves that must be refused. It only contains tests. | 18 |
| [`sample_state_machine/`](sample_state_machine/) | A small custom module: a booking request with 5 states, 7 transitions and a manager-only override, plus one HTTP status route. | 22 + 7 plain-Python |

How the Time Off tests reach the existing module: the official `odoo:19.0` Docker image already
contains `hr_holidays`. Our test module lists it as a dependency, so Odoo installs it first and
then runs our tests against it. No Odoo code is copied into this repo.

The transition table the tests follow, with references into the Odoo source, is in
[`docs/hr_holidays-state-machine.md`](docs/hr_holidays-state-machine.md).

All users and data in the tests are fictitious.

## Prerequisites

- **Docker Desktop**, running
- **Git**
- **Python 3** on your machine (only for the plain-Python tests)
- Port **8069** free
- Windows PowerShell for the scripts. On macOS/Linux, see [Without PowerShell](#without-powershell).

The first run downloads the `postgres:16` and `odoo:19.0` images (a few GB) and takes a few minutes.

## Setup

Using Claude Code? Clone the repo, then follow [`SETUP_WITH_CLAUDE.md`](SETUP_WITH_CLAUDE.md)
instead of the steps below.

```powershell
git clone <repo-url>
cd <repo-folder>
```

No other setup is needed. The scripts start the containers themselves.

If PowerShell blocks the scripts, run them as
`powershell -ExecutionPolicy Bypass -File .\scripts\<name>.ps1`.

## Run the tests

Each Odoo run creates a fresh database, installs the module, runs its tests and drops the database.

```powershell
# Time Off (hr_holidays) transition tests
.\scripts\test-odoo.ps1 -Module hr_holidays_state_tests
#   expect: == 0 failed, 0 error(s) of 18 tests (odoo exit code 0)

# Sample module: all Odoo tests
.\scripts\test-odoo.ps1
#   expect: == 0 failed, 0 error(s) of 22 tests (odoo exit code 0)

# Sample module: plain-Python tests (no Docker needed)
.\scripts\test-plain.ps1
#   expect: Ran 7 tests ... OK
```

More options:

| What | Command |
|---|---|
| Sample module tests by tag | `.\scripts\test-odoo.ps1 -Tags sample_sm_model` (tags: `sample_sm`, `sample_sm_plain`, `sample_sm_model`, `sample_sm_http`) |
| One Time Off test | `.\scripts\test-odoo.ps1 -Module hr_holidays_state_tests -Tags /hr_holidays_state_tests:TestLeaveStateMachine.test_officer_skips_second_approval_step` |
| Keep the test database afterwards | add `-KeepDb` |
| Odoo's own hr_holidays tests (slow) | `.\scripts\test-odoo.ps1 -Module hr_holidays` |

VS Code: the same commands are available under **Terminal → Run Task**.

## See it working

```powershell
# Walk fictitious time-off requests through every transition and print each state.
# Uses a scratch database hr_demo and rolls its changes back, so you can re-run it.
.\scripts\demo-hr-holidays.ps1

# Start Odoo with the sample module and the Time Off app, then open
# http://localhost:8069 (admin / admin).  -Reset recreates the database.
.\scripts\start-odoo.ps1

# Stop everything
docker compose stop
```

In the browser:

- **Time Off**: admin is a Time Off administrator. **Time Off → New**, then pick a type that needs no
  allocation, then approve, refuse or cancel it. Types to try: *Unpaid* (approver + officer), *Sick Time Off*
  (officer only), *Unpaid leave* (no approval, approved straight away). *Paid Time Off* needs an
  allocation first (**Time Off → Management → Allocations**). To see the two-step approval, you need a
  second user as the approver, because admin is an officer and skips that step.
- **Sample Bookings**: admin is in the Booking Manager group, so every button is available.

Step-by-step walk-throughs for both apps: **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)**.

The database has no demo data. Everything you create there is your own test data.

## What the Time Off tests cover

A time-off request starts in **To Approve** (`confirm`). Its path depends on the leave type's
approval setting: none, Time Off Officer, the employee's approver, or both.

| Covered | Tests |
|---|---|
| Creating a request; "no approval" types approved immediately | 2 |
| Approving: approver then officer (two steps), officer in one step, approver-only and officer-only types, back to approval, re-approving a refused request | 6 |
| Refusing: before approval, after the first approval, after full approval | 3 |
| Employee cancelling their own request after first approval, after approval, after refusal | 3 |
| **Refused moves:** employee approves own request, employee cancels a request still waiting, approver refuses an officer-only type, approving a cancelled request | 4 |

Code: [`hr_holidays_state_tests/tests/test_leave_state_machine.py`](hr_holidays_state_tests/tests/test_leave_state_machine.py).

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not start the database container` / `dockerDesktopLinuxEngine` pipe error | Start Docker Desktop and wait until it says it is running. |
| Port 8069 already in use | Stop the other Odoo (`docker ps`), or change `"8069:8069"` in `docker-compose.yml`. |
| Test count is lower than expected | Always test on a fresh database with `-i` (the script does this). `-u` skips the install-time tests. |
| No "Sample Bookings" menu | Use `start-odoo.ps1`. It adds admin to the Booking Manager group. |
| Coverage script fails | Install coverage.py in the container once: `docker compose run --rm --no-deps --entrypoint python3 odoo -m pip install --user --break-system-packages coverage` (not re-checked). |

## Without PowerShell

The scripts wrap plain `docker compose` commands. For example, the Time Off tests:

```bash
docker compose up -d --wait db
docker compose run --rm odoo odoo -d test_hr -i hr_holidays_state_tests \
  --test-tags=/hr_holidays_state_tests --without-demo=all --stop-after-init
docker compose exec db dropdb -U odoo test_hr
```

## Repo layout

```
hr_holidays_state_tests/   test-only module for hr_holidays (Time Off)
sample_state_machine/      custom sample module (details in its README)
docs/                      hr_holidays state-machine write-up
scripts/                   test, demo, coverage and start scripts (PowerShell)
config/odoo.conf           local dev config
docker-compose.yml         postgres:16 + odoo:19.0
CLAUDE.md                  notes for Claude Code
SETUP_WITH_CLAUDE.md       prompt: let Claude Code set up and check everything
```

The usernames and passwords in `docker-compose.yml` and `config/odoo.conf` are local dev
placeholders. Don't reuse them anywhere else.

## Using Claude Code

[`SETUP_WITH_CLAUDE.md`](SETUP_WITH_CLAUDE.md) is a ready-made prompt. Open the repo in Claude
Code and say **"Follow SETUP_WITH_CLAUDE.md"**. Claude checks your prerequisites, runs all the
tests and the demo, starts Odoo, and reports the results. `CLAUDE.md` gives it the project context
automatically.
