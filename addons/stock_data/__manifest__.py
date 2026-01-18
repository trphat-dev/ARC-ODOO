# -*- coding: utf-8 -*-
{
    'name': 'FMS - Market Data',
    'version': '18.0.1.0.0',
    'category': 'Financial',
    'summary': 'Vietnamese stock market data via SSI FastConnect API',
    'description': """
FMS - Market Data (Odoo 18)
===========================

Stock market data integration via SSI FastConnect Data API.

Key Features:
- Securities list (HOSE, HNX, UPCOM)
- Daily OHLC data
- Intraday OHLC data
- Index list and components
- Automatic data synchronization
- Real-time WebSocket streaming
- Stock board with price ticker
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'bus',
        'web',
    ],
    'external_dependencies': {
        'python': [
            'ssi_fc_data',  # SSI FastConnect Data SDK
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/api_config_data.xml',
        # Views
        'views/api_config_views.xml',
        'views/securities_views.xml',
        'views/daily_ohlc_views.xml',
        'views/intraday_ohlc_views.xml',
        'views/fetch_data_wizard_views.xml',
        'views/menus.xml',
        'views/server_actions.xml',
        'views/stock_board_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Styles
            'stock_data/static/src/scss/price_ticker.scss',
            'stock_data/static/src/components/stock_board/stock_board.scss',
            # Stock Board Components
            'stock_data/static/src/components/**/*.js',
            'stock_data/static/src/components/**/*.xml',
            'stock_data/static/src/js/**/*.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
