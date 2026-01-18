# -*- coding: utf-8 -*-
{
    'name': 'FMS - Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Fund management dashboard for staff operations',
    'description': """
FMS - Dashboard (Odoo 18)
=========================

Administrative dashboard for fund management staff.

Key Features:
- Investor transaction overview
- Total accounts and investment statistics
- Daily fund certificate buy/sell movements
- Sidebar navigation panel
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
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/dashboard/dashboard_page.xml',
        'views/dashboard_detail_views.xml',
        'views/fund_dashboard_daily_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Dashboard Widget (Frontend)
            'fund_management_dashboard/static/src/js/dashboard/dashboard_widget.js',
            'fund_management_dashboard/static/src/js/dashboard/sidebar_panel.js',
            'fund_management_dashboard/static/src/js/dashboard/entrypoint.js',
            'fund_management_dashboard/static/src/scss/sidebar.scss',
            'fund_management_dashboard/static/src/scss/dashboard.scss',
        ],
        'web.assets_backend': [
            # Dashboard Widget (Backend)
            'fund_management_dashboard/static/src/js/dashboard/dashboard_widget.js',
            'fund_management_dashboard/static/src/js/dashboard/sidebar_panel.js',
            'fund_management_dashboard/static/src/scss/sidebar.scss',
            'fund_management_dashboard/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
