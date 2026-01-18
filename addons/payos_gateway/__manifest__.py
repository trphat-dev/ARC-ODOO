# -*- coding: utf-8 -*-
{
    'name': 'FMS - Payment Gateway',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment',
    'summary': 'PayOS payment integration with webhook verification',
    'description': """
FMS - Payment Gateway (Odoo 18)
===============================

PayOS payment gateway integration for fund transactions.

Key Features:
- PayOS payment link creation
- Webhook signature verification
- Payment status tracking
- Secure credential management
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'web',
    ],
    'external_dependencies': {
        'python': [
            'requests',  # HTTP requests
            'Crypto',    # Signature verification
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/payos_credentials_data.xml',
        # Views
        'views/payos_settings.xml',
        'views/payos_config_views.xml',
    ],
    'installable': True,
    'application': True,
}
