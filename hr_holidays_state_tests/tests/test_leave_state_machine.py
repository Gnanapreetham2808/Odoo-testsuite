"""State-machine tests for the stock hr_holidays module (model hr.leave).

Each test follows one row of the transition table in docs/hr_holidays-state-machine.md.
All users, employees and leave types are fictitious and created here; no demo data is used.
"""
from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

LEAVE_DAY = date(2031, 3, 3)  # a future Monday, so the employee is expected to work that day


@tagged('hr_leave_sm')
class TestLeaveStateMachine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref('base.main_company')
        calendar = company.resource_calendar_id

        def make_person(login, name, groups):
            user = new_test_user(cls.env, login=login, name=name, groups=groups, tz='UTC')
            cls.env['hr.employee'].create({
                'name': name, 'user_id': user.id, 'resource_calendar_id': calendar.id, 'tz': 'UTC',
            })
            return user

        cls.officer = make_person('sm_officer', 'Olive Officer (fictitious)',
                                  'base.group_user,hr_holidays.group_hr_holidays_user')
        cls.approver = make_person('sm_approver', 'Arlo Approver (fictitious)', 'base.group_user')
        cls.employee_user = make_person('sm_employee', 'Ezra Employee (fictitious)', 'base.group_user')
        cls.employee = cls.employee_user.employee_id
        cls.employee.leave_manager_id = cls.approver  # the "Employee's Approver"

        def make_type(name, validation):
            return cls.env['hr.leave.type'].create({
                'name': name, 'leave_validation_type': validation, 'requires_allocation': False,
                'employee_requests': True, 'company_id': company.id,
            })

        cls.type_both = make_type('Test leave: approver + officer', 'both')
        cls.type_manager = make_type('Test leave: approver only', 'manager')
        cls.type_hr = make_type('Test leave: officer only', 'hr')
        cls.type_none = make_type('Test leave: no approval', 'no_validation')

    # --- helpers ------------------------------------------------------------------------------------

    def _new_leave(self, leave_type):
        return self.env['hr.leave'].with_user(self.employee_user).create({
            'name': 'Fictitious request', 'employee_id': self.employee.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': LEAVE_DAY, 'request_date_to': LEAVE_DAY,
        })

    def _cancel_as_employee(self, leave):
        wizard = self.env['hr.holidays.cancel.leave'].with_user(self.employee_user).create(
            {'leave_id': leave.id, 'reason': 'Fictitious reason'})
        wizard.action_cancel_leave()

    def assertState(self, leave, expected):
        leave.invalidate_recordset()
        self.assertEqual(leave.state, expected)

    # --- creation -----------------------------------------------------------------------------------

    def test_create_starts_in_confirm(self):
        self.assertState(self._new_leave(self.type_both), 'confirm')

    def test_no_validation_type_is_approved_on_create(self):
        self.assertState(self._new_leave(self.type_none), 'validate')

    # --- approving ----------------------------------------------------------------------------------

    def test_double_validation_approver_then_officer(self):
        leave = self._new_leave(self.type_both)
        leave.with_user(self.approver).action_approve()
        self.assertState(leave, 'validate1')
        leave.with_user(self.officer).action_approve()
        self.assertState(leave, 'validate')

    def test_officer_skips_second_approval_step(self):
        # action_approve checks can_validate before can_approve, so an Officer goes straight to validate.
        leave = self._new_leave(self.type_both)
        leave.with_user(self.officer).action_approve()
        self.assertState(leave, 'validate')

    def test_approver_validates_manager_type(self):
        leave = self._new_leave(self.type_manager)
        leave.with_user(self.approver).action_approve()
        self.assertState(leave, 'validate')

    def test_officer_validates_hr_type(self):
        leave = self._new_leave(self.type_hr)
        leave.with_user(self.officer).action_approve()
        self.assertState(leave, 'validate')

    def test_officer_sends_approved_back_to_approval(self):
        leave = self._new_leave(self.type_both)
        leave.with_user(self.officer).action_approve()
        leave.with_user(self.officer).action_back_to_approval()
        self.assertState(leave, 'confirm')

    def test_officer_reapproves_refused(self):
        leave = self._new_leave(self.type_both)
        leave.with_user(self.officer).action_refuse()
        self.assertState(leave, 'refuse')
        leave.with_user(self.officer).action_approve()
        self.assertState(leave, 'validate')

    # --- refusing -----------------------------------------------------------------------------------

    def test_approver_refuses_waiting_request(self):
        leave = self._new_leave(self.type_manager)
        leave.with_user(self.approver).action_refuse()
        self.assertState(leave, 'refuse')

    def test_approver_refuses_after_first_approval(self):
        leave = self._new_leave(self.type_both)
        leave.with_user(self.approver).action_approve()
        leave.with_user(self.approver).action_refuse()
        self.assertState(leave, 'refuse')

    def test_officer_refuses_approved_request(self):
        leave = self._new_leave(self.type_manager)
        leave.with_user(self.approver).action_approve()
        leave.with_user(self.officer).action_refuse()
        self.assertState(leave, 'refuse')

    # --- cancelling ---------------------------------------------------------------------------------

    def test_employee_cancels_from_second_approval(self):
        leave = self._new_leave(self.type_both)
        leave.with_user(self.approver).action_approve()
        self._cancel_as_employee(leave)
        self.assertState(leave, 'cancel')

    def test_employee_cancels_approved_request(self):
        leave = self._new_leave(self.type_none)
        self._cancel_as_employee(leave)
        self.assertState(leave, 'cancel')

    def test_employee_cancels_refused_request(self):
        leave = self._new_leave(self.type_manager)
        leave.with_user(self.approver).action_refuse()
        self._cancel_as_employee(leave)
        self.assertState(leave, 'cancel')

    # --- illegal moves ------------------------------------------------------------------------------

    def test_employee_cannot_approve_own_request(self):
        leave = self._new_leave(self.type_both)
        with self.assertRaises(UserError):
            leave.with_user(self.employee_user).action_approve()
        self.assertState(leave, 'confirm')

    def test_employee_cannot_cancel_request_waiting_for_approval(self):
        leave = self._new_leave(self.type_both)
        with self.assertRaises(ValidationError):
            self._cancel_as_employee(leave)
        self.assertState(leave, 'confirm')

    def test_approver_cannot_refuse_officer_only_type(self):
        leave = self._new_leave(self.type_hr)
        with self.assertRaises(UserError):
            leave.with_user(self.approver).action_refuse()
        self.assertState(leave, 'confirm')

    def test_cancelled_request_cannot_be_approved(self):
        leave = self._new_leave(self.type_none)
        self._cancel_as_employee(leave)
        with self.assertRaises(UserError):
            leave.with_user(self.officer).action_approve()
        self.assertState(leave, 'cancel')
