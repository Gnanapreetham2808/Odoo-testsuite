{
    'name': 'Sample State Machine',
    'summary': 'Reference module: a small state machine on a custom model, with tests.',
    'description': """
Capability sample for Odoo 19.0.

A booking request moves through five states with seven regular transitions and
one manager-only override. The module contains a plain-Python transition table,
Odoo tests (TransactionCase, HttpCase, test tags) and one plain HTTP route.
All data is fictitious.
""",
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'license': 'LGPL-3',
    'author': 'Ziensys IT Solution Private Limited',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/booking_views.xml',
    ],
    'installable': True,
    'application': False,
}
