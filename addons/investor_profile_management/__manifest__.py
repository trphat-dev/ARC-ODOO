# -*- coding: utf-8 -*-
{
    'name': 'FMS - User Profile',
    'version': '18.0.1.0.0',
    'category': 'Investor',
    'summary': 'Investor profile management with eKYC integration',
    'description': """
FMS - Investor Profile (Odoo 18)
================================

Complete investor profile management with eKYC verification.

Key Features:
- Personal information with OCR auto-fill
- Bank accounts management
- Address information management
- eKYC verification with face detection
- Premium UI with animations and responsive design
- Res.Partner integration for profiles, bank, address, status
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'portal',
        'web',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/ekyc_api_config_data.xml',
        # Backend Views
        'views/menu_views.xml',
        'views/ekyc_api_config_views.xml',
        'views/ekyc_records_view.xml',
        'views/api_records_view.xml',
        'views/status_info_views.xml',
        'views/personal_info_view.xml',
        'views/bank_info_view.xml',
        'views/address_info_view.xml',
        'views/res_partner_profiles_views.xml',
        'views/res_partner_bank_views.xml',
        'views/res_partner_address_views.xml',
        'views/res_partner_hide_view.xml',
        'views/res_partner_status_views.xml',
        'views/res_config_settings_views.xml',
        # Frontend Pages
        'views/personal_profile/personal_profile_page.xml',
        'views/bank_info/bank_info_page.xml',
        'views/address_info/address_info_page.xml',
        'views/verification/verification_page.xml',
        'views/verification/ekyc_verification_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'investor_profile_management/static/src/scss/_investor_variables.scss',
            'investor_profile_management/static/src/scss/investor_profile.scss',
            # Personal Profile Widget
            'investor_profile_management/static/src/js/personal_profile/entrypoint.js',
            'investor_profile_management/static/src/js/personal_profile/personal_profile_widget.js',
            # Bank Info Widget
            'investor_profile_management/static/src/js/bank_info/entrypoint.js',
            'investor_profile_management/static/src/js/bank_info/bank_info_widget.js',
            # Address Info Widget
            'investor_profile_management/static/src/js/address_info/entrypoint.js',
            'investor_profile_management/static/src/js/address_info/address_info_widget.js',
            # Verification Widget
            'investor_profile_management/static/src/js/verification/entrypoint.js',
            'investor_profile_management/static/src/js/verification/verification_widget.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
