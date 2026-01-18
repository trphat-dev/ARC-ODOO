# -*- coding: utf-8 -*-
{
    'name': 'FMS - Reports',
    'version': '18.0.1.0.23',
    'category': 'Finance',
    'summary': 'Comprehensive balance, transaction and investor reports',
    'description': """
FMS - Reports (Odoo 18)
=======================

Comprehensive reporting module for fund management.

Report Types:
- Balance reports
- Transaction reports
- Order history reports
- Contract statistics reports
- Early sale reports
- Contract summary reports
- Purchase/Sell contract reports
- AOC (Assets on Custody) reports
- Investor reports
- User list reports
- Tenors and interest rates list

Features:
- PDF export for all report types
- Frontend report pages
- Backend report views
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'web',
        # FMS Modules
        'fund_management',  # Portfolio investment model
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Backend Views
        'views/report_list_backend_views.xml',
        # Balance Report
        'views/report_balance/report_balance_page.xml',
        'views/report_balance/report_balance_pdf_template.xml',
        # Transaction Report
        'views/report_transaction/report_transaction_page.xml',
        'views/report_transaction/report_transaction_pdf_template.xml',
        # Order History Report
        'views/report_order_history/report_order_history_page.xml',
        'views/report_order_history/report_order_history_pdf_template.xml',
        # Contract Statistics Report
        'views/report_contract_statistics/report_contract_statistics_page.xml',
        'views/report_contract_statistics/report_contract_statistics_pdf_template.xml',
        # Early Sale Report
        'views/report_early_sale/report_early_sale_page.xml',
        'views/report_early_sale/report_early_sale_pdf_template.xml',
        # Contract Summary Report
        'views/report_contract_summary/report_contract_summary_page.xml',
        'views/report_contract_summary/report_contract_summary_pdf_template.xml',
        # Purchase Contract Report
        'views/report_purchase_contract/report_purchase_contract_page.xml',
        'views/report_purchase_contract/report_purchase_contract_pdf_template.xml',
        # Sell Contract Report
        'views/report_sell_contract/report_sell_contract_page.xml',
        'views/report_sell_contract/report_sell_contract_pdf_template.xml',
        # AOC Report
        'views/aoc_report/aoc_report_page.xml',
        'views/aoc_report/aoc_report_pdf_template.xml',
        # Investor Report
        'views/investor_report/investor_report_page.xml',
        'views/investor_report/investor_report_pdf_template.xml',
        # User List Report
        'views/user_list_report/user_list_report_page.xml',
        'views/user_list_report/user_list_report_pdf_template.xml',
        # Tenors Interest Rates
        'views/list_tenors_interest_rates/list_tenors_interest_rates_page.xml',
        'views/list_tenors_interest_rates/list_tenors_interest_rates_pdf_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'report_list/static/src/scss/report_list.scss',
            # Report Widgets
            'report_list/static/src/js/report_balance/report_balance_widget.js',
            'report_list/static/src/js/report_balance/entrypoint.js',
            'report_list/static/src/js/report_transaction/report_transaction_widget.js',
            'report_list/static/src/js/report_transaction/entrypoint.js',
            'report_list/static/src/js/report_order_history/report_order_history_widget.js',
            'report_list/static/src/js/report_order_history/entrypoint.js',
            'report_list/static/src/js/report_contract_statistics/report_contract_statistics_widget.js',
            'report_list/static/src/js/report_contract_statistics/entrypoint.js',
            'report_list/static/src/js/report_early_sale/report_early_sale_widget.js',
            'report_list/static/src/js/report_early_sale/entrypoint.js',
            'report_list/static/src/js/report_contract_summary/report_contract_summary_widget.js',
            'report_list/static/src/js/report_contract_summary/entrypoint.js',
            'report_list/static/src/js/report_purchase_contract/report_purchase_contract_widget.js',
            'report_list/static/src/js/report_purchase_contract/entrypoint.js',
            'report_list/static/src/js/report_sell_contract/report_sell_contract_widget.js',
            'report_list/static/src/js/report_sell_contract/entrypoint.js',
            'report_list/static/src/js/aoc_report/aoc_report_widget.js',
            'report_list/static/src/js/aoc_report/entrypoint.js',
            'report_list/static/src/js/investor_report/investor_report_widget.js',
            'report_list/static/src/js/investor_report/entrypoint.js',
            'report_list/static/src/js/user_list_report/user_list_report_widget.js',
            'report_list/static/src/js/user_list_report/entrypoint.js',
            'report_list/static/src/js/list_tenors_interest_rates/list_tenors_interest_rates_widget.js',
            'report_list/static/src/js/list_tenors_interest_rates/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}