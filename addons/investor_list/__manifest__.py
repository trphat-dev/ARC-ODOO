# -*- coding: utf-8 -*-
{
    'name': 'FMS - Investors',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Investor list management for staff',
    'description': """
FMS - Investors (Odoo 18)
=========================

Investor list management module for fund staff operations.

Key Features:
- Investor list with search and filter
- Header navigation component
- Frontend investor list page
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
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/menu_views.xml',
        'views/investor_list_views.xml',
        'views/investor_list/investor_list_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'investor_list/static/src/scss/investor_list.scss',
            'investor_list/static/src/scss/_header.scss',
            # Header Component
            'investor_list/static/src/js/components/header.js',
            'investor_list/static/src/js/components/entrypoint.js',
            # Investor List Widget
            'investor_list/static/src/js/investor_list/investor_list_widget.js',
            'investor_list/static/src/js/investor_list/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
