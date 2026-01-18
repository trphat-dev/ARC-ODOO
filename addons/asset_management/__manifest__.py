# -*- coding: utf-8 -*-
{
    'name': 'FMS - User Assets',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Investor asset portfolio management',
    'description': """
FMS - User Assets (Odoo 18)
================================

Provides investor asset portfolio management with visual dashboard.

Key Features:
- Asset portfolio overview
- Investment tracking and visualization
- Frontend and backend widget support
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'mail',
        'portal',
        'web',
        # FMS Modules
        'fund_management',  # Portfolio investment model
    ],
    'data': [
        # Views
        'views/asset_management/asset_management_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Asset Management Widget (Frontend)
            'asset_management/static/src/scss/asset_management.scss',
            'asset_management/static/src/js/asset_management/asset_management_widget.js',
            'asset_management/static/src/js/asset_management/entrypoint.js',
        ],
        'web.assets_backend': [
            # Asset Management Widget (Backend)
            'asset_management/static/src/js/asset_management/asset_management_widget.js',
            'asset_management/static/src/js/asset_management/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
