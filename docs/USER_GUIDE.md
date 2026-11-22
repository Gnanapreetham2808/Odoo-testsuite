# User guide: Time Off and Sample Bookings

How to try both apps in the browser and watch each state machine move. Use only fictitious
names and data. The example names below are made up.

## Before you start

Run `.\scripts\start-odoo.ps1` (see the [README](../README.md)), then open
**http://localhost:8069** and log in as **admin** / **admin**.

`admin` is a **Time Off administrator** and a **Booking Manager**, so every button is visible.
The database has no demo data. Admin is the only employee until you add more.

---

## Part 1: Time Off (Odoo's built-in `hr_holidays` app)

### The states

```
                 ┌──────────────► Refused ──────────┐
                 │                   │              │
To Approve ──► Second Approval ──► Approved ◄───────┘ (re-approve)
    ▲            (only for            │
    └──────────── "both" types) ──────┘ Back to Approval

Second Approval / Approved / Refused ──► Cancelled (by the employee, via Cancel)
```

| State (on screen) | Meaning |
|---|---|
| **To Approve** | Just submitted. Every new request starts here. |
| **Second Approval** | The approver said yes and it now waits for a Time Off officer. Only for types that need both. |
| **Approved** | Final yes. The days are blocked in the calendar. |
| **Refused** | Said no. An officer can still approve it later. |
| **Cancelled** | Withdrawn. It can't be changed any more. |

Which path a request takes depends on its **type's approval setting**
(Time Off → Configuration → Time Off Types → *Approval*):

| Type to try | Approval setting | Path |
|---|---|---|
| **Unpaid leave** | None needed | Approved as soon as it is created |
| **Sick Time Off** | By Time Off Officer | To Approve → Approved / Refused |
| **Unpaid** | By Employee's Approver and Time Off Officer | To Approve → Second Approval → Approved |

None of these three need an allocation. *Paid Time Off* only works after you give the employee
days under **Time Off → Management → Allocations**.

### Walk-through A: simple approval (5 minutes, admin only)

1. **Time Off → Management → Time Off → New.**
2. Employee: *Administrator*. Type: **Sick Time Off**. Pick a future weekday. Save.
   → The status bar shows **To Approve**.
3. Click **Validate**. → **Approved**. (Odoo labels the button *Validate* when the click gives final
   approval, and *Approve* when it only gives the first of two approvals.)
4. Click **Back to Approval**. → **To Approve** again.
5. Click **Refuse**. → **Refused**.
6. Click **Validate** again. → **Approved** (an officer can re-approve a refused request).
7. Click **Cancel**, enter a fictitious reason, confirm. → **Cancelled**. The request can't be
   changed after this.

Then create one with type **Unpaid leave** and notice it's **Approved** straight away.

### Walk-through B: two-step approval (15 minutes, needs a second user)

You only see **Second Approval** when the first approver is *not* a Time Off officer. Admin is an
officer, so if admin approves an *Unpaid* request, it goes straight to Approved. To see both steps:

1. **Create the approver user:** Settings → Users & Companies → Users → **New**.
   Name `Arlo Approver (fictitious)`, login `arlo`. Leave the Time Off rights empty. Save.
   Then use the gear menu (⚙) → **Change Password** and set a password, e.g. `arlo`.
2. **Create the employee:** Employees → **New**. Name `Ezra Employee (fictitious)`.
   Under **Approvers**, set **Time Off** = *Arlo Approver (fictitious)*. Save.
   (This also gives Arlo the "Time Off Responsible" rights automatically.)
3. **As admin, create the request:** Time Off → Management → Time Off → **New**.
   Employee *Ezra Employee*, type **Unpaid**, a future weekday. Save. → **To Approve**.
4. **As Arlo:** open a private/incognito window, log in as `arlo`, go to
   Time Off → Management → Time Off, open Ezra's request, click **Approve**.
   → **Second Approval**.
5. **As admin:** open the same request and click **Validate**. → **Approved**.

Things to try in this setup:
- As Arlo, **Refuse** a request in Second Approval. This is allowed for "both" types.
- As Arlo, try the same on a **Sick Time Off** request. The Refuse button isn't there, because
  officer-only types can't be refused by the approver.

### What the automated tests prove

Each walk-through step above is also checked automatically by
`hr_holidays_state_tests` (18 tests):

```powershell
.\scripts\test-odoo.ps1 -Module hr_holidays_state_tests
```

The full transition table, with references into the Odoo source, is in
[hr_holidays-state-machine.md](hr_holidays-state-machine.md).
`.\scripts\demo-hr-holidays.ps1` prints the same walk-through in the terminal.

---

## Part 2: Sample Bookings (our `sample_state_machine` module)

An equipment booking request with 5 states.

```
Draft ──Submit──► Submitted ──Approve──► Approved ──Mark as done──► Done
  ▲                  │                      │                         │
  └─────Reject───────┘                      │                         │ Force cancel
                                            ▼                         ▼ (manager only)
Draft / Submitted / Approved ──Cancel──► Cancelled ◄──────────────────┘
```

| Button | From | To | Who |
|---|---|---|---|
| **Submit** | Draft | Submitted | anyone with access |
| **Approve** | Submitted | Approved | Booking Manager |
| **Reject** | Submitted | Draft | Booking Manager |
| **Mark as done** | Approved | Done | anyone with access |
| **Cancel** | Draft, Submitted, Approved | Cancelled | anyone with access |
| **Force cancel** | Done | Cancelled | Booking Manager (the one override) |

### Walk-through C (5 minutes, admin only)

1. **Sample Bookings → New.** Equipment: `Projector (fictitious)`, pick From/To dates. Save.
   → **Draft**.
2. **Submit** → Submitted. **Reject** → back to Draft.
3. **Submit** again → **Approve** → Approved.
4. **Mark as done** → Done. Only **Force cancel** is left.
5. **Force cancel** → Cancelled. No buttons remain.

Rules to notice:
- The status can't be edited by hand. It only changes through the buttons.
- *To* before *From* is rejected when you save.

### Walk-through D: user vs manager (optional)

1. Create a user `Bea Booker (fictitious)`, login `bea`, and set a password as in walk-through B.
   Then add her to the booking group. The group isn't in a regular access-rights category, so:
   Settings → **Activate the developer mode** (bottom of the page), then
   Settings → Users & Companies → **Groups** → search *Booking User* → **Users** tab → add Bea → Save.
2. Log in as Bea in a private window: she can create, Submit, Cancel and Mark as done, but there's
   no **Approve**, **Reject** or **Force cancel** button. She also sees only her own bookings.
3. As admin you see everyone's bookings and can approve Bea's.

### The status URL

While logged in, open `http://localhost:8069/sample/booking/<id>/status` (the id is in the record's
URL). It returns a short JSON with the state. Another user's booking or an unknown id returns
`404 {"error": "not_found"}`.

---

## Resetting

To start over with an empty database: `.\scripts\start-odoo.ps1 -Reset`.
To stop Odoo: `docker compose stop`.
