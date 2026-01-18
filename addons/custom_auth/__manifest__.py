# -*- coding: utf-8 -*-
{
    'name': 'FMS - Authentication Pages',
    'version': '18.0.1.2.0',
    'category': 'Website',
    'summary': 'Custom login, signup and password reset pages',
    'description': """
FMS - Custom Auth Pages (Odoo 18)
=================================

Customized authentication pages with modern Bootstrap styling.

Key Features:
- Custom login page design
- Custom signup page design
- Custom password reset page design
- SCSS-based theming with variables
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'web',
        'auth_signup',  # Signup functionality
    ],
    'data': [
        # Views - Auth Templates
        'views/custom_login_template.xml',
        'views/custom_signup_template.xml',
        'views/custom_reset_password_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Auth Styles
            'custom_auth/static/src/scss/_variables.scss',
            'custom_auth/static/src/scss/_auth_common.scss',
        ],
    },
    'installable': True,
    'application': True,
}