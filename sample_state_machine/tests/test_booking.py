from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from .. import transitions

# Legal way to reach each state from a fresh draft booking.
PATH_TO_STATE = {
    'draft': [],
    'submitted': ['submit'],
    'approved': ['submit', 'approve'],
    'done': ['submit', 'approve', 'complete'],
    'cancelled': ['cancel'],
}
# Model method behind each action (cancel has three source states, one method).
METHOD = {
    'submit': 'action_submit',
    'approve': 'action_approve',
    'reject': 'action_reject',
    'complete': 'action_complete',
    'cancel': 'action_cancel',
}


@tagged('standard', 'sample_sm', 'sample_sm_model')
class TestBookingStateMachine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = 'sample_state_machine.group_sample_booking_user'
        group_manager = 'sample_state_machine.group_sample_booking_manager'
        cls.user_a = new_test_user(cls.env, login='sm_user_a', groups=group_user)
        cls.user_b = new_test_user(cls.env, login='sm_user_b', groups=group_user)
        cls.manager = new_test_user(cls.env, login='sm_manager', groups=group_manager)

    def _booking(self, user=None, state='draft'):
        """Create a fictitious booking and walk it to `state` with a manager."""
        booking = self.env['sample.booking'].with_user(user or self.user_a).create({
            'name': 'Fictitious projector',
            'date_start': '2030-01-10',
            'date_end': '2030-01-12',
        })
        manager_booking = booking.with_user(self.manager)
        for action in PATH_TO_STATE[state]:
            getattr(manager_booking, METHOD[action])()
        return booking

    def test_new_booking_is_draft(self):
        self.assertEqual(self._booking().state, 'draft')

    def test_all_legal_and_illegal_transitions(self):
        for state in transitions.STATES:
            for action, method in METHOD.items():
                with self.subTest(state=state, action=action):
                    booking = self._booking(state=state).with_user(self.manager)
                    expected = transitions.target_state(action, state)
                    if expected is None:
                        with self.assertRaises(UserError):
                            getattr(booking, method)()
                        self.assertEqual(booking.state, state)
                    else:
                        getattr(booking, method)()
                        self.assertEqual(booking.state, expected)

    def test_state_cannot_be_written_directly(self):
        booking = self._booking()
        with self.assertRaises(UserError):
            booking.write({'state': 'done'})

    def test_cannot_create_in_a_later_state(self):
        with self.assertRaises(UserError):
            self.env['sample.booking'].create({
                'name': 'Fictitious camera',
                'date_start': '2030-02-01',
                'date_end': '2030-02-02',
                'state': 'approved',
            })

    def test_end_date_before_start_date_is_refused(self):
        with self.assertRaises(ValidationError):
            self.env['sample.booking'].create({
                'name': 'Fictitious laptop',
                'date_start': '2030-02-05',
                'date_end': '2030-02-01',
            })

    def test_user_cannot_approve_or_reject(self):
        booking = self._booking(state='submitted').with_user(self.user_a)
        with self.assertRaises(AccessError):
            booking.action_approve()
        with self.assertRaises(AccessError):
            booking.action_reject()
        self.assertEqual(booking.state, 'submitted')

    def test_override_force_cancel_by_manager(self):
        booking = self._booking(state='done').with_user(self.manager)
        booking.action_force_cancel()
        self.assertEqual(booking.state, 'cancelled')

    def test_override_refused_for_plain_user(self):
        booking = self._booking(state='done').with_user(self.user_a)
        with self.assertRaises(AccessError):
            booking.action_force_cancel()
        self.assertEqual(booking.state, 'done')

    def test_override_only_from_done(self):
        for state in ('draft', 'submitted', 'approved', 'cancelled'):
            with self.subTest(state=state):
                booking = self._booking(state=state).with_user(self.manager)
                with self.assertRaises(UserError):
                    booking.action_force_cancel()

    def test_users_only_see_their_own_bookings(self):
        own = self._booking(user=self.user_a)
        other = self._booking(user=self.user_b)
        visible = self.env['sample.booking'].with_user(self.user_a).search([])
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)
        all_visible = self.env['sample.booking'].with_user(self.manager).search([])
        self.assertIn(own, all_visible)
        self.assertIn(other, all_visible)
