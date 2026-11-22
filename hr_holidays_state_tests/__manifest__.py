{
    'name': 'Time Off State Machine Tests',
    'summary': 'Test-only module: checks every state transition of the stock hr_holidays (Time Off) module.',
    'description': """
Test-only module for Odoo 19.0.

It adds no models, views or data. It installs the stock hr_holidays module and runs tests that
walk fictitious time-off requests (hr.leave) through every allowed transition and check that the
illegal ones are refused. See docs/hr_holidays-state-machine.md in the repository.
""",
    'version': '19.0.1.0.0',
    'category': 'Hidden/Tests',
    'license': 'LGPL-3',
    'author': 'Ziensys IT Solution Private Limited',
    'depends': ['hr_holidays'],
    'data': [],
    'installable': True,
    'application': False,
}
