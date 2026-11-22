# Set up this repo with Claude Code

How to use it:

1. Clone the repo and open the folder in VS Code (or a terminal) with Claude Code.
2. Tell Claude: **"Follow SETUP_WITH_CLAUDE.md"**, or paste everything below the line.

Claude checks your machine, runs every test suite and the demo, starts Odoo, and reports what
passed. It takes about 10 to 15 minutes on the first run, mostly downloading the Docker images.

---

You are setting up this Odoo 19.0 repo on my machine and checking that everything works.
First read `README.md` and `CLAUDE.md`, then work through the steps below in order.

Rules:
- Don't edit, skip or weaken any test to make it pass. If something fails, stop on that step,
  show me the real error lines, explain the likely cause and suggest a fix. Ask me before
  changing any file.
- Don't commit, push, or change git settings.
- Don't install software without asking me. Telling me what to install is fine.
- Run the commands from the repo root. The scripts are PowerShell. On macOS/Linux, use the
  `docker compose` commands in the README's "Without PowerShell" section instead.
- Odoo runs can take several minutes, and the first one downloads a few GB. Use long timeouts
  (10 minutes) or run them in the background. Don't treat slowness as a failure.
- If PowerShell blocks a script, run it as
  `powershell -ExecutionPolicy Bypass -File .\scripts\<name>.ps1`.

## Step 1: Check prerequisites

Check each of these and report what you find:
- `git --version`
- `python --version` (or `python3 --version`): needed only for the plain tests
- `docker --version` and `docker compose version`
- `docker info`, which only succeeds if Docker Desktop is running. If it fails on Windows, start
  `C:\Program Files\Docker\Docker\Docker Desktop.exe`, wait up to 2 minutes, and retry. If Docker
  isn't installed, tell me to install Docker Desktop and stop here.
- Port 8069 is free. If something already uses it, tell me what, and don't stop it yourself.

## Step 2: Plain-Python tests (no Docker)

Run `.\scripts\test-plain.ps1`. Expect `Ran 7 tests` and `OK`.

## Step 3: Time Off (hr_holidays) tests

Run `.\scripts\test-odoo.ps1 -Module hr_holidays_state_tests`.
Expect the last line to be `== 0 failed, 0 error(s) of 18 tests (odoo exit code 0)`.

This creates a fresh database, installs Odoo's built-in Time Off module and our test module, runs
the tests and drops the database.

## Step 4: Sample module tests

Run `.\scripts\test-odoo.ps1`.
Expect `== 0 failed, 0 error(s) of 22 tests (odoo exit code 0)`.

## Step 5: Time Off demo

Run `.\scripts\demo-hr-holidays.ps1`. It prints fictitious time-off requests moving through each
state, then `Done. All demo changes were rolled back.` The "Illegal transition" part is
expected to show `refused with UserError`.

Explain the output briefly against the table in `docs/hr_holidays-state-machine.md`.

## Step 6: Start Odoo for manual testing

Run `.\scripts\start-odoo.ps1`. Expect `Odoo is up: http://localhost:8069 (admin / admin)`.
Tell me to open http://localhost:8069, log in as admin / admin, and use the **Sample Bookings** menu.
Odoo keeps running in Docker until `docker compose stop`.

## Step 7: Report

Finish with a short table: step, result (pass/fail) and the key output line. Then:
- If anything failed: the error and your suggested fix.
- If everything passed: a 5-line summary of what the repo contains and how the Time Off tests
  reach Odoo's built-in `hr_holidays` module. It ships in the `odoo:19.0` image, and
  `hr_holidays_state_tests` lists it as a dependency.
- A reminder that `docker compose stop` stops Odoo.
