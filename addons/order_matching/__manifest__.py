# -*- coding: utf-8 -*-
{
    'name': 'FMS - Order Matching',
    'version': '18.0.1.0.1',
    'category': 'Finance',
    'summary': 'Automatic order matching with Price-Time Priority algorithm',
    'description': """
FMS - Order Matching (Odoo 18)
==============================

Automatic order matching engine using Price-Time Priority (FIFO) algorithm.

Key Features:
- Automatic order matching engine
- Maturity notification system
- Order book with real-time updates
- Matched order pair management
- Completed, negotiated, and normal order tracking
- Background auto-match worker
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
        'stock_trading',  # Trading order model
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/maturity_notification_data.xml',
        # Backend Views
        'views/matched_orders_views.xml',
        'views/maturity_notification_log_views.xml',
        'views/maturity_notification_views.xml',
        'views/menu_views.xml',
        'views/sent_orders_views.xml',
        # Frontend Pages
        'views/pages/order_book_page.xml',
        'views/pages/completed_orders_page.xml',
        'views/pages/negotiated_orders_page.xml',
        'views/pages/normal_orders_page.xml',
        'views/pages/maturity_notification_response_page.xml',
    ],
    'assets': {
        'web.assets_backend': [],
        'web.assets_frontend': [
            # Order Matching Actions
            'order_matching/static/src/js/order_matching_actions.js',
            # Order Book Components
            'order_matching/static/src/js/order_book/order_book_component.js',
            'order_matching/static/src/js/order_book/entrypoint.js',
            'order_matching/static/src/js/order_book/completed_orders_component.js',
            'order_matching/static/src/js/order_book/negotiated_orders_component.js',
            'order_matching/static/src/js/order_book/normal_orders_component.js',
            'order_matching/static/src/css/order_book.css',
            # Auto Match Background Worker
            'order_matching/static/src/js/auto_match_worker.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
