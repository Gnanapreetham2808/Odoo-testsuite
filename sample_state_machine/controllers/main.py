import logging

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


def _booking_payload(booking):
    """Data returned for a booking. Kept apart so tests can replace it."""
    return {
        'id': booking.id,
        'name': booking.name,
        'state': booking.state,
    }


class SampleBookingController(http.Controller):

    @http.route('/sample/booking/<int:booking_id>/status', type='http', auth='user',
                methods=['GET'], csrf=False)
    def booking_status(self, booking_id, **kwargs):
        """Plain HTTP route (not JSON-RPC): errors are short JSON, never a stack trace."""
        try:
            booking = request.env['sample.booking'].browse(booking_id).exists()
            if not booking:
                return request.make_json_response({'error': 'not_found'}, status=404)
            booking.check_access('read')
            return request.make_json_response(_booking_payload(booking))
        except AccessError:
            # Same answer as an unknown id, so ids of other users' records are not revealed.
            return request.make_json_response({'error': 'not_found'}, status=404)
        except Exception:
            # Details go to the server log only; the caller gets a generic answer.
            _logger.exception("Booking status route failed for id %s", booking_id)
            return request.make_json_response({'error': 'server_error'}, status=500)
