# -*- coding: utf-8 -*-
{
    'name': 'FMS - Market Trading',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Stock trading via SSI FastConnect Trading API',
    'description': """
FMS - Market Trading (Odoo 18)
=======================

Stock trading management via SSI FastConnect Trading API.

Key Features:
- API configuration (Consumer ID, Secret, Private Key)
- Buy/Sell orders for Stock & Derivatives
- Order management (Modify, Cancel)
- Account balance & position view
- Cash management
- Online Right Subscription (ORS)
- Stock transfer
- Transaction history & order book
- Real-time SignalR streaming
- Trading portal for investors
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
        'stock_data',  # Market data source
    ],
    'external_dependencies': {
        'python': [
            'ssi-fctrading',  # SSI FastConnect Trading SDK
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/trading_cron.xml',
        'data/trading_sequence.xml',
        # Backend Views
        'views/trading_config_views.xml',
        'views/trading_order_views.xml',
        'views/trading_account_views.xml',
        'views/trading_cash_views.xml',
        'views/trading_ors_views.xml',
        'views/trading_stock_transfer_views.xml',
        'views/trading_history_views.xml',
        'views/trading_menus.xml',
        # Frontend Portal
        'views/trading_portal/trading_portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Backend Styles
            'stock_trading/static/src/css/trading.css',
        ],
        'web.assets_frontend': [
            # Trading Portal Styles
            'stock_trading/static/src/scss/_trading_portal.scss',
            # Trading Portal Widget
            'stock_trading/static/src/js/trading_portal.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
