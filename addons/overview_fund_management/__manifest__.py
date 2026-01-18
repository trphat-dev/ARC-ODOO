# -*- coding: utf-8 -*-
{
    'name': 'FMS - User Overview',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Fund investment portfolio overview for investors',
    'description': """
FMS - Overview (Odoo 18)
========================

Investor-facing portfolio overview with premium UI.

Key Features:
- Fund investment portfolio overview
- Header and footer components
- Global loader with animations
- Premium dashboard styling
- Maturity notification bus service
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
        'fund_management',  # Portfolio investment model
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Frontend Pages
        'views/overview_fund_management/overview_fund_management_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Global Loader
            'overview_fund_management/static/src/scss/loader.scss',
            'overview_fund_management/static/src/js/components/loader.js',
            # Header & Footer Components
            'overview_fund_management/static/src/js/components/header.js',
            'overview_fund_management/static/src/js/components/footer.js',
            'overview_fund_management/static/src/js/components/entrypoint.js',
            # Overview Widget
            'overview_fund_management/static/src/js/overview_fund_management/overview_fund_management_widget.js',
            'overview_fund_management/static/src/js/overview_fund_management/entrypoint.js',
            # Styles
            'overview_fund_management/static/src/scss/header.scss',
            'overview_fund_management/static/src/scss/footer.scss',
            'overview_fund_management/static/src/scss/overview_fund_management.scss',
        ],
        'web.assets_backend': [
            # Global Loader
            'overview_fund_management/static/src/scss/loader.scss',
            'overview_fund_management/static/src/js/components/loader.js',
            # Header & Footer Components
            'overview_fund_management/static/src/js/components/header.js',
            'overview_fund_management/static/src/js/components/footer.js',
            'overview_fund_management/static/src/js/components/entrypoint.js',
            'overview_fund_management/static/src/scss/header.scss',
            'overview_fund_management/static/src/scss/footer.scss',
            # Maturity Notification Bus
            'order_matching/static/src/js/maturity_notification_bus.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
