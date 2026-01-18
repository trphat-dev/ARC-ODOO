# -*- coding: utf-8 -*-
{
    'name': 'FMS - Transactions',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Transaction order list with pending/approved tabs',
    'description': """
FMS - Transactions (Odoo 18)
============================

Transaction order list management for fund staff.

Key Features:
- Pending orders tab (awaiting approval)
- Approved orders tab
- Order matching integration
- Transaction list widget
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'bus',
        'mail',
        'portal',
        'web',
        # FMS Modules
        'order_matching',  # Order matching fields (matched_units, remaining_units)
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/transaction_list_views.xml',
        'views/menu_views.xml',
        'views/transaction_list/transaction_list_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'transaction_list/static/src/scss/transaction_list.scss',
            # Transaction List Widget
            'transaction_list/static/src/js/transaction_list/transaction_list_tab.js',
            'transaction_list/static/src/js/transaction_list/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
