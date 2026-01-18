# -*- coding: utf-8 -*-
{
    'name': 'FMS - AI Consultant',
    'version': '18.0.2.0.0',
    'category': 'Finance',
    'summary': 'AI Trading Assistant with FinRL Deep Reinforcement Learning',
    'description': """
FMS - AI Consultant (Odoo 18)
=============================

AI-powered trading assistant integrating FinRL Deep Reinforcement Learning 
with SSI FastConnect API for Vietnamese stock market.

Key Features:
- SSI FastConnect integration for HOSE, HNX, UPCOM data
- Multiple DRL algorithms: PPO, A2C, SAC, TD3, DDPG
- Technical indicators: RSI, MACD, Bollinger Bands, ATR, SMA
- Model training with TensorBoard visualization
- Backtesting with Sharpe ratio, max drawdown metrics
- Automated trading with dry-run and live modes
- AI investment chatbot with chart generation
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'web',
        'mail',
        'bus',
        # FMS Modules
        'stock_data',      # Market data source
        'stock_trading',   # Trading order execution
    ],
    'external_dependencies': {
        'python': [
            'stable_baselines3',  # DRL algorithms
            'gymnasium',          # RL environment
            'torch',              # PyTorch backend
            'pandas',
            'pandas_ta',          # Technical analysis
            'numpy',
            'plotly',             # Interactive charts
            'matplotlib',
            'requests',
            'openai',             # OpenRouter chatbot SDK
        ],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/ai_trading_config_data.xml',
        # Views
        'views/ai_trading_config_views.xml',
        'views/backtest_wizard_views.xml',
        'views/ai_strategy_views.xml',
        'views/ai_model_training_views.xml',
        'views/ai_prediction_views.xml',
        'views/ai_chatbot_global_config_views.xml',
        'views/ai_chatbot_views.xml',
        'views/ai_trading_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Technical Chart Widget
            'ai_trading_assistant/static/src/js/technical_chart/technical_chart_widget.js',
            'ai_trading_assistant/static/src/js/technical_chart/entrypoint.js',
            'ai_trading_assistant/static/src/scss/technical_chart.scss',
            # AI Chatbot
            'ai_trading_assistant/static/src/js/website_chatbot.js',
            'ai_trading_assistant/static/src/xml/website_chatbot.xml',
            'ai_trading_assistant/static/src/scss/website_chatbot.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
