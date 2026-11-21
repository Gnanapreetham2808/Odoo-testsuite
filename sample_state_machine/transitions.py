"""Transition table of the booking state machine.

Plain Python on purpose: this file must not import Odoo, so the table can be
tested without a database (see tests/plain/).
"""

STATES = ('draft', 'submitted', 'approved', 'done', 'cancelled')

# action -> {current state: target state}. Seven regular transitions in total.
TRANSITIONS = {
    'submit': {'draft': 'submitted'},
    'approve': {'submitted': 'approved'},
    'reject': {'submitted': 'draft'},
    'complete': {'approved': 'done'},
    'cancel': {
        'draft': 'cancelled',
        'submitted': 'cancelled',
        'approved': 'cancelled',
    },
}

# The one override: outside the regular table, manager-only (enforced by the model).
OVERRIDES = {
    'force_cancel': {'done': 'cancelled'},
}


def target_state(action, current):
    """Return the state reached by `action` from `current`, or None if not allowed."""
    return TRANSITIONS.get(action, {}).get(current)


def override_target_state(action, current):
    """Same as target_state() but for the override table."""
    return OVERRIDES.get(action, {}).get(current)


def allowed_actions(current):
    """Regular actions that can be applied in state `current`."""
    return sorted(a for a, moves in TRANSITIONS.items() if current in moves)


def transition_count():
    """Number of regular (action, from-state) transitions."""
    return sum(len(moves) for moves in TRANSITIONS.values())
