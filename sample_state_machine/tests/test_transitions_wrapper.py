"""Thin wrapper: runs the plain-Python table checks inside the Odoo test runner.

The same checks run as plain Python in CI (no database, no Enterprise source)
and, through this wrapper, on the Odoo.sh build, so tag subsets give identical
results in both places.
"""
from odoo.tests.common import BaseCase, tagged

from .plain.test_transitions_plain import TransitionTableChecks


@tagged('standard', 'at_install', 'sample_sm', 'sample_sm_plain')
class TestTransitionTableInOdoo(TransitionTableChecks, BaseCase):
    # Odoo's loader only collects methods defined on the class itself; the checks are inherited.
    allow_inherited_tests_method = True
