import json
from unittest.mock import patch

from odoo.tests.common import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'sample_sm', 'sample_sm_http')
class TestBookingStatusRoute(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = 'sample_state_machine.group_sample_booking_user'
        cls.user_a = new_test_user(cls.env, login='sm_http_a', groups=group_user)
        cls.user_b = new_test_user(cls.env, login='sm_http_b', groups=group_user)
        cls.booking = cls.env['sample.booking'].with_user(cls.user_a).create({
            'name': 'Fictitious microphone',
            'date_start': '2030-03-01',
            'date_end': '2030-03-03',
        })

    def _get(self, booking_id):
        return self.url_open(f'/sample/booking/{booking_id}/status', allow_redirects=False)

    def test_owner_gets_the_status(self):
        self.authenticate('sm_http_a', 'sm_http_aaa')
        response = self._get(self.booking.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], 'draft')

    def test_unknown_id_is_a_clean_404(self):
        self.authenticate('sm_http_a', 'sm_http_aaa')
        response = self._get(999999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'not_found'})

    def test_other_users_booking_is_not_exposed(self):
        self.authenticate('sm_http_b', 'sm_http_bbb')
        response = self._get(self.booking.id)
        # Same answer as an unknown id, so record ids cannot be probed.
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'not_found'})
        self.assertNotIn('microphone', response.text)

    def test_anonymous_request_gets_no_data(self):
        self.authenticate(None, None)
        response = self._get(self.booking.id)
        self.assertNotEqual(response.status_code, 200)
        self.assertNotIn('microphone', response.text)

    def test_unexpected_error_shows_no_stack_trace(self):
        self.authenticate('sm_http_a', 'sm_http_aaa')
        with patch('odoo.addons.sample_state_machine.controllers.main._booking_payload',
                   side_effect=RuntimeError('secret internal detail')), \
                self.assertLogs('odoo.addons.sample_state_machine.controllers.main', 'ERROR'):
            response = self._get(self.booking.id)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.text), {'error': 'server_error'})
        self.assertNotIn('Traceback', response.text)
        self.assertNotIn('secret internal detail', response.text)
