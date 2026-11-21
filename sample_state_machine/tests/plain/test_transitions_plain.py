"""Plain-Python tests of the transition table: no Odoo, no database.

Run it by file path (the module's package __init__ imports Odoo, so do not use -m):
    python3 tests/plain/test_transitions_plain.py

The table is loaded by file path so that the module's __init__ (which imports
Odoo) is never executed.
"""
import importlib.util
import unittest
from pathlib import Path

_PATH = Path(__file__).resolve().parents[2] / 'transitions.py'
_spec = importlib.util.spec_from_file_location('sample_transitions_plain', _PATH)
transitions = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transitions)


class TransitionTableChecks:
    """Test methods shared by the plain run and the Odoo-tagged wrapper."""

    def test_state_and_transition_counts(self):
        self.assertEqual(len(transitions.STATES), 5)
        self.assertEqual(transitions.transition_count(), 7)

    def test_every_target_is_a_known_state(self):
        for action, moves in transitions.TRANSITIONS.items():
            for source, target in moves.items():
                self.assertIn(source, transitions.STATES, action)
                self.assertIn(target, transitions.STATES, action)

    def test_legal_moves(self):
        expected = {
            ('submit', 'draft'): 'submitted',
            ('approve', 'submitted'): 'approved',
            ('reject', 'submitted'): 'draft',
            ('complete', 'approved'): 'done',
            ('cancel', 'draft'): 'cancelled',
            ('cancel', 'submitted'): 'cancelled',
            ('cancel', 'approved'): 'cancelled',
        }
        for (action, source), target in expected.items():
            self.assertEqual(transitions.target_state(action, source), target)

    def test_illegal_moves_return_none(self):
        legal = {(a, s) for a, moves in transitions.TRANSITIONS.items() for s in moves}
        for action in transitions.TRANSITIONS:
            for state in transitions.STATES:
                if (action, state) not in legal:
                    self.assertIsNone(transitions.target_state(action, state), (action, state))

    def test_unknown_action_is_not_allowed(self):
        self.assertIsNone(transitions.target_state('teleport', 'draft'))

    def test_final_states_have_no_regular_exit(self):
        self.assertEqual(transitions.allowed_actions('cancelled'), [])
        self.assertEqual(transitions.allowed_actions('done'), [])

    def test_override_is_outside_the_regular_table(self):
        self.assertNotIn('force_cancel', transitions.TRANSITIONS)
        self.assertEqual(transitions.override_target_state('force_cancel', 'done'), 'cancelled')
        self.assertIsNone(transitions.override_target_state('force_cancel', 'draft'))


class TestTransitionTablePlain(TransitionTableChecks, unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
