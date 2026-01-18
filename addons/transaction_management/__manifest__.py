# -*- coding: utf-8 -*-
{
    'name': 'FMS - User Transactions',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Investor transaction management portal',
    'description': """
FMS - Transaction Management (Odoo 18)
======================================

Investor-facing transaction management portal.

Key Features:
- Pending transactions view
- Order history view  
- Periodic investment management (SIP)
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'mail',
        'portal',
        'web',
    ],
    'data': [
        # Frontend Pages
        'views/transaction_trading/transaction_pending_page.xml',
        'views/transaction_trading/transaction_order_page.xml',
        'views/transaction_trading/transaction_periodic_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'transaction_management/static/src/scss/transaction_management.scss',
            # Transaction Widgets
            'transaction_management/static/src/js/transaction_management/pending_widget.js',
            'transaction_management/static/src/js/transaction_management/order_widget.js',
            'transaction_management/static/src/js/transaction_management/periodic_widget.js',
            'transaction_management/static/src/js/transaction_management/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
