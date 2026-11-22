# hr_holidays: the `hr.leave` state machine (Odoo 19.0 Community)

Source: the stock `hr_holidays` module in the `odoo:19.0` Docker image (`Odoo Server 19.0-20261112`),
path `/usr/lib/python3/dist-packages/odoo/addons/hr_holidays/`. Line numbers are for that build and will
shift in other revisions. Paths below are relative to the module folder.

Everything here was read in the source. The rows marked **(demo)** were also run for real by
`scripts/demo_hr_holidays.py`.

## States

`models/hr_leave.py:129-135`, default `confirm`:

| Value | Label |
|---|---|
| `confirm` | To Approve |
| `refuse` | Refused |
| `validate1` | Second Approval |
| `validate` | Approved |
| `cancel` | Cancelled |

There is no `draft` state: a new request starts in `confirm`.

## What decides the path: the leave type's validation type

`hr.leave.validation_type` (`models/hr_leave.py:150`) is related to
`hr.leave.type.leave_validation_type` (`models/hr_leave_type.py:87-91`, default `hr`):

| Value | Label |
|---|---|
| `no_validation` | None needed |
| `hr` | By Time Off Officer |
| `manager` | By Employee's Approver |
| `both` | By Employee's Approver and Time Off Officer |

`validate1` is used only for `both` (`models/hr_leave.py:1478-1479`).

## Who is who

| Role in this doc | What it is in the source |
|---|---|
| Officer | group `hr_holidays.group_hr_holidays_user` ("Officer: Manage all requests"). The Administrator group `group_hr_holidays_manager` implies it (`security/hr_holidays_security.xml:21-30`). |
| Approver | the user set as the employee's `leave_manager_id` (`is_time_off_manager`, `models/hr_leave.py:1433`) |
| Employee | the user linked to the request's employee (`is_own_leave`, `models/hr_leave.py:1429`) |
| Superuser / `sudo()` | `_check_approval_update` returns `True` immediately (`models/hr_leave.py:1465-1466`) |

## Transitions

| Action method (file:line) | From | To | Who may do it |
|---|---|---|---|
| `create` (`models/hr_leave.py:922-963`) | (new) | `confirm` | default state (`:135`) |
| `create` → `action_approve()` under `sudo()` (`:956-958`) | (new) | `validate` | automatic when the type is `no_validation` **(demo)** |
| `action_approve` (`:1189-1204`) → writes `validate1` at `:1200` | `confirm` | `validate1` | when `can_approve` is true and `can_validate` is not. In practice: the Approver, for a `both` type **(demo)** |
| `action_approve` → `_action_validate` (`:1281-1306`, writes `validate` at `:1289`) | `confirm` | `validate` | when `can_validate`: an Officer (any type), or the Approver for a `manager` type **(demo)** |
| `action_approve` → `_action_validate` | `validate1` | `validate` | Officer (second approval) **(demo)** |
| `action_approve` → `_action_validate` | `refuse` | `validate` | Officer, or the Approver for a `manager` type **(demo, Officer)** |
| `action_back_to_approval` (`:1206-1208`) → `_move_validate_leave_to_confirm` (`:1210-1213`) | `validate` | `confirm` | only if `can_back_to_approve` (`:737-739`): Officer **(demo)** |
| `action_refuse` (`:1308-1327`, writes `refuse` at `:1315-1316`) | `confirm` | `refuse` | Officer; the Approver if the type is not `hr` **(demo, Approver)** |
| `action_refuse` | `validate1` | `refuse` | Officer; the Approver for a `both` type **(demo, Approver)** |
| `action_refuse` | `validate` | `refuse` | Officer; the Approver if the type is not `hr` **(demo, Officer)** |
| `action_cancel` (`:1173-1187`) opens wizard `hr.holidays.cancel.leave`; `action_cancel_leave` (`wizard/hr_holidays_cancel_leave.py:14-17`) → `_action_user_cancel` (`:1347-1352`) → `_force_cancel` (`:1354-1400`, sets `cancel` at `:1398`) | `validate1`, `validate`, `refuse` | `cancel` | the Employee on their own request, if it has not started yet (or the user is an Officer) **(demo: from all three)**; an Officer |

`action_refuse` itself raises `UserError` unless the state is `confirm`, `validate1` or `validate`
(`:1310-1311`).

## How permissions are enforced

1. **Allowed-next-state table**: `_get_next_states_by_state` (`models/hr_leave.py:1417-1461`) builds, for the
   current user and request, the set of states reachable from each state:
   - Own request, not in the past (or the user is an Officer): `validate1`, `validate` and `refuse` can go to `cancel` (`:1435-1438`).
   - Officer (`:1440-1449`): `confirm` → `validate`, `refuse` (and `validate1` for `both`); `validate1` → `confirm`, `validate`, `refuse`;
     `validate` → `confirm`, `refuse`; `refuse` → `confirm`, `validate` (and `validate1` for `both`); `cancel` → `confirm`, `validate`, `refuse` (and `validate1` for `both`).
   - Approver, not an Officer (`:1450-1459`): not `hr` type: `confirm` → `refuse` and `validate` → `refuse`; `both`: `confirm` → `validate1` and `validate1` → `refuse`;
     `manager`: `confirm` → `validate` and `refuse` → `validate`.
2. **Gate on every state write**: `write` calls `_check_approval_update(new_state)` (`:983-984`). It
   (`:1463-1518`) raises `UserError` if the state does not change, if `validate1` is asked for a non-`both`
   type, if the request is already `cancel` ("A cancelled leave cannot be modified.", `:1480-1481`), or if
   the target is not in the table above. The `cancel` → … entries in the Officer table are therefore never
   reached by a non-superuser, because the `:1480` check comes first.
3. **Double-validation rules** for `both` types: `_check_double_validation_rules` (`:909-920`, called from
   `create` `:934-935` and `write` `:985-990`). Going to `validate1` needs the Approver or an Officer;
   going to `validate` needs an Officer. Administrators skip the check.
4. **Buttons**: `can_approve`, `can_validate`, `can_refuse`, `can_cancel` and `can_back_to_approve`
   (`models/hr_leave.py:193-197`, computes at `:732-755`) call `_check_approval_update(..., raise_if_not_possible=False)`.
   The form view shows the buttons from them (`views/hr_leave_views.xml:336-340`): Approve and Validate both call
   `action_approve`; then Back to Approval, Refuse and Cancel.

## Behaviour worth knowing (from the source)

- `action_approve` checks `can_validate` **before** `can_approve` (`:1194-1197`). So when an Officer approves
  a `both` request in `confirm`, it goes straight to `validate` and skips `validate1`, because the Officer's
  table allows `confirm` → `validate`. Only an Approver who is not an Officer produces `validate1`.
- If neither `can_validate` nor `can_approve` holds, `action_approve` raises
  `UserError("You cannot approve this leave.")` (`:1198-1199`). This is the illegal transition the demo shows.
- `confirm` → `cancel` is not in the table, so the Employee cannot cancel a request still waiting for its first
  approval through the wizard.
- `_action_validate` raises `ValidationError` if the employee is not supposed to work during the period (`:1286-1287`).
- Validating creates the resource leave and, if the type has `create_calendar_meeting` set, a calendar event
  (`_validate_leave_request`, `:1096-…`). Leaving `validate` removes the resource leave (`write`, `:975-979`).
  Refusing deactivates the meeting (`:1318`).
