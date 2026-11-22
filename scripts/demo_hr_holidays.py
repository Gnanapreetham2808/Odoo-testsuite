"""Walk fictitious time-off requests (hr.leave) through every transition of the stock hr_holidays module.

Run inside `odoo shell` against a scratch database (see scripts/demo-hr-holidays.ps1):
    odoo shell -d hr_demo --no-http < demo_hr_holidays.py

`env` is provided by odoo shell. All people and data are fictitious. Every change is rolled back at the
end, so the script can be re-run on the same database.
"""
from datetime import date

from odoo.exceptions import AccessError, UserError, ValidationError

# --- fictitious setup -------------------------------------------------------------------------------
company = env.ref('base.main_company')
calendar = company.resource_calendar_id
groups_field = 'group_ids' if 'group_ids' in env['res.users']._fields else 'groups_id'


def make_user(login, name, *group_xmlids):
    user = env['res.users'].with_context(no_reset_password=True).create({
        'name': name, 'login': login, 'tz': 'UTC',
        groups_field: [(6, 0, [env.ref(x).id for x in ('base.group_user',) + group_xmlids])],
    })
    env['hr.employee'].create({'name': name, 'user_id': user.id, 'resource_calendar_id': calendar.id, 'tz': 'UTC'})
    return user


officer = make_user('demo_officer', 'Olive Officer (fictitious)', 'hr_holidays.group_hr_holidays_user')
approver = make_user('demo_approver', 'Arlo Approver (fictitious)')
employee_user = make_user('demo_employee', 'Ezra Employee (fictitious)')
employee = employee_user.employee_id
employee.leave_manager_id = approver  # the "Employee's Approver"


def make_type(name, validation):
    return env['hr.leave.type'].create({
        'name': name, 'leave_validation_type': validation, 'requires_allocation': False,
        'employee_requests': True, 'company_id': company.id,
    })


type_both = make_type('Demo leave: approver + officer', 'both')
type_manager = make_type('Demo leave: approver only', 'manager')
type_none = make_type('Demo leave: no approval', 'no_validation')

# Distinct future weekdays, one per request, so requests never overlap.
DAYS = iter([date(2031, 3, d) for d in (3, 4, 5, 6, 7, 10, 11)])


def new_leave(leave_type, label):
    day = next(DAYS)
    leave = env['hr.leave'].with_user(employee_user).create({
        'name': label, 'employee_id': employee.id, 'holiday_status_id': leave_type.id,
        'request_date_from': day, 'request_date_to': day,
    })
    show(leave, f'created by employee ({leave_type.leave_validation_type})')
    return leave


def show(leave, step):
    leave.invalidate_recordset()
    print(f'  {leave.name:<10} {step:<52} -> state = {leave.state}')


def cancel_by_employee(leave):
    wizard = env['hr.holidays.cancel.leave'].with_user(employee_user).create(
        {'leave_id': leave.id, 'reason': 'Fictitious reason'})
    wizard.action_cancel_leave()
    show(leave, 'employee: action_cancel -> wizard action_cancel_leave')


# --- walk-through -----------------------------------------------------------------------------------
print('\n=== hr.leave state machine demo (fictitious data) ===')

print('\nRequest A: double validation (approver, then officer)')
a = new_leave(type_both, 'Request A')
a.with_user(approver).action_approve();          show(a, 'approver: action_approve (first approval)')
a.with_user(officer).action_approve();           show(a, 'officer: action_approve (second approval)')
a.with_user(officer).action_back_to_approval();  show(a, 'officer: action_back_to_approval')
a.with_user(officer).action_refuse();            show(a, 'officer: action_refuse')
a.with_user(officer).action_approve();           show(a, 'officer: action_approve (re-approve refused)')
cancel_by_employee(a)

print('\nRequest B: refused after the first approval')
b = new_leave(type_both, 'Request B')
b.with_user(approver).action_approve();          show(b, 'approver: action_approve (first approval)')
b.with_user(approver).action_refuse();           show(b, 'approver: action_refuse')
cancel_by_employee(b)

print('\nRequest C: approver-only validation, refused after approval')
c = new_leave(type_manager, 'Request C')
c.with_user(approver).action_approve();          show(c, 'approver: action_approve')
c.with_user(officer).action_refuse();            show(c, 'officer: action_refuse')

print('\nRequest D: refused straight away')
d = new_leave(type_manager, 'Request D')
d.with_user(approver).action_refuse();           show(d, 'approver: action_refuse')

print('\nRequest E: double validation, cancelled while waiting for the second approval')
e = new_leave(type_both, 'Request E')
e.with_user(approver).action_approve();          show(e, 'approver: action_approve (first approval)')
cancel_by_employee(e)

print('\nRequest F: no approval needed (approved automatically on create), then cancelled')
f = new_leave(type_none, 'Request F')
cancel_by_employee(f)

print('\nIllegal transition: the employee tries to approve their own request')
g = new_leave(type_both, 'Request G')
try:
    with env.cr.savepoint():
        g.with_user(employee_user).action_approve()
    print('  UNEXPECTED: no error raised')
except (UserError, AccessError, ValidationError) as exc:
    print(f'  refused with {type(exc).__name__}: {exc}')
show(g, 'after the refused attempt')

env.cr.rollback()
print('\nDone. All demo changes were rolled back.')
