from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import transitions


class SampleBooking(models.Model):
    _name = 'sample.booking'
    _description = 'Equipment Booking Request'
    _order = 'id desc'

    name = fields.Char(string='Equipment', required=True)
    requester_id = fields.Many2one(
        'res.users', string='Requester', required=True, default=lambda self: self.env.user,
    )
    date_start = fields.Date(string='From', required=True)
    date_end = fields.Date(string='To', required=True)
    note = fields.Text()
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft', required=True, readonly=True, copy=False, index=True,
    )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for booking in self:
            if booking.date_end < booking.date_start:
                raise ValidationError(_("The end date cannot be before the start date."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft':
                raise UserError(_("A booking can only be created in the draft state."))
        return super().create(vals_list)

    def write(self, vals):
        # The state only moves through the transition methods below.
        if 'state' in vals and not self.env.context.get('sample_state_transition'):
            raise UserError(_("The state cannot be changed directly; use the workflow buttons."))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Transition engine
    # ------------------------------------------------------------------
    def _apply_action(self, action):
        for booking in self:
            target = transitions.target_state(action, booking.state)
            if target is None:
                raise UserError(_(
                    "Action '%(action)s' is not allowed from state '%(state)s'.",
                    action=action, state=booking.state,
                ))
            booking.with_context(sample_state_transition=True).write({'state': target})
        return True

    # ------------------------------------------------------------------
    # Regular transitions (seven in total, see transitions.TRANSITIONS)
    # ------------------------------------------------------------------
    def action_submit(self):
        return self._apply_action('submit')

    def action_approve(self):
        self._check_manager()
        return self._apply_action('approve')

    def action_reject(self):
        self._check_manager()
        return self._apply_action('reject')

    def action_complete(self):
        return self._apply_action('complete')

    def action_cancel(self):
        return self._apply_action('cancel')

    # ------------------------------------------------------------------
    # The override: manager-only, leaves the regular table
    # ------------------------------------------------------------------
    def action_force_cancel(self):
        """Cancel a booking that is already done. Managers only."""
        self._check_manager()
        for booking in self:
            target = transitions.override_target_state('force_cancel', booking.state)
            if target is None:
                raise UserError(_("Only a done booking can be force-cancelled."))
            booking.with_context(sample_state_transition=True).write({'state': target})
        return True

    def _check_manager(self):
        if not self.env.user.has_group('sample_state_machine.group_sample_booking_manager'):
            raise AccessError(_("Only a booking manager can do this."))
