# -*- coding: utf-8 -*-
{
    'name': 'FMS - Configs',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Fund certificates, schemes, fees and master data configuration',
    'description': """
FMS - Fund Certificate Configs (Odoo 18)
=======================================

Administrative module for managing fund certificates, schemes, fees and master data.

Key Features:
- Fund certificate management with sync
- Scheme and scheme type configuration
- Fee schedule management
- SIP (Systematic Investment Plan) settings
- Tax settings configuration
- Master data: holidays, banks, branches, countries, cities, wards
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'bus',
        'mail',
        'web',
        # FMS Modules
        'fund_management_dashboard',  # Dashboard integration
        'investor_list',              # Investor data
        'stock_data',                 # Market data
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/cron_data.xml',
        # Wizard (must load before menu_views.xml for action reference)
        'wizard/wizard_sync_fund_view.xml',
        # Fund Certificate
        'views/fund_certificate/sync_action.xml',
        # Menu
        'views/menu_views.xml',
        'views/fund_certificate/fund_certificate_page.xml',
        'views/fund_certificate/fund_certificate_form.xml',
        'views/fund_certificate/fund_certificate_edit_form.xml',
        # Scheme Type
        'views/scheme_type/scheme_type_page.xml',
        'views/scheme_type/scheme_type_form.xml',
        'views/scheme_type/scheme_type_edit_form.xml',
        # Scheme
        'views/scheme/scheme_page.xml',
        'views/scheme/scheme_form.xml',
        'views/scheme/scheme_edit_form.xml',
        # Fee Schedule
        'views/fee_schedule/fee_schedule_page.xml',
        'views/fee_schedule/fee_schedule_form.xml',
        'views/fee_schedule/fee_schedule_edit_form.xml',
        # SIP Settings
        'views/sip_settings/sip_settings_page.xml',
        'views/sip_settings/sip_settings_form.xml',
        'views/sip_settings/sip_settings_edit_form.xml',
        # Tax Settings
        'views/tax_settings/tax_settings_page.xml',
        'views/tax_settings/tax_settings_form.xml',
        'views/tax_settings/tax_settings_edit_form.xml',
        # Master Data
        'views/holiday/holiday_page.xml',
        'views/holiday/holiday_form.xml',
        'views/bank/bank_page.xml',
        'views/bank/bank_form.xml',
        'views/bank_branch/bank_branch_page.xml',
        'views/bank_branch/bank_branch_form.xml',
        'views/country/country_page.xml',
        'views/country/country_form.xml',
        'views/city/city_page.xml',
        'views/city/city_form.xml',
        'views/ward/ward_page.xml',
        'views/ward/ward_form.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Styles
            'fund_management_control/static/src/scss/style.scss',
            # Widget Mounting Service
            'fund_management_control/static/src/js/widget_mounting_service.js',
            # Fund Certificate Widget
            'fund_management_control/static/src/js/fund_certificate/fund_certificate_widget.js',
            'fund_management_control/static/src/js/fund_certificate/entrypoint.js',
            # Scheme Type Widget
            'fund_management_control/static/src/js/scheme_type/scheme_type_widget.js',
            'fund_management_control/static/src/js/scheme_type/entrypoint.js',
            # Scheme Widget
            'fund_management_control/static/src/js/scheme/scheme_widget.js',
            'fund_management_control/static/src/js/scheme/entrypoint.js',
            # Fee Schedule Widget
            'fund_management_control/static/src/js/fee_schedule/fee_schedule_widget.js',
            'fund_management_control/static/src/js/fee_schedule/entrypoint.js',
            # SIP Settings Widget
            'fund_management_control/static/src/js/sip_settings/sip_settings_widget.js',
            'fund_management_control/static/src/js/sip_settings/entrypoint.js',
            # Tax Settings Widget
            'fund_management_control/static/src/js/tax_settings/tax_settings_widget.js',
            'fund_management_control/static/src/js/tax_settings/entrypoint.js',
            # Master Data Widgets
            'fund_management_control/static/src/js/holiday/holiday_widget.js',
            'fund_management_control/static/src/js/holiday/entrypoint.js',
            'fund_management_control/static/src/js/bank/bank_widget.js',
            'fund_management_control/static/src/js/bank/entrypoint.js',
            'fund_management_control/static/src/js/bank_branch/bank_branch_widget.js',
            'fund_management_control/static/src/js/bank_branch/entrypoint.js',
            'fund_management_control/static/src/js/country/country_widget.js',
            'fund_management_control/static/src/js/country/entrypoint.js',
            'fund_management_control/static/src/js/city/city_widget.js',
            'fund_management_control/static/src/js/city/entrypoint.js',
            'fund_management_control/static/src/js/ward/ward_widget.js',
            'fund_management_control/static/src/js/ward/entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
