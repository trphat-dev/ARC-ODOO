# -*- coding: utf-8 -*-
{
    'name': 'FMS - Permissions',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'User role and permission management',
    'description': """
FMS - User Permissions (Odoo 18)
================================

User permission and role management for FMS system.

Key Features:
- Role management: System Admin, Portal Admin, Fund Operator
- Automatic sync with Odoo groups
- User permission management interface
- Timezone auto-fix cron job
- Access denied page handling
    """,
    'author': 'https://github.com/billzcasso',
    'license': 'LGPL-3',
    'depends': [
        # Odoo Core
        'base',
        'mail',
        'portal',
        'web',
        'auth_signup',  # Signup API
        # FMS Modules
        'fund_management_dashboard',  # SidebarPanel component
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/timezone_fix_cron.xml',
        # Backend Views
        'views/user_permission/user_permission_backend_views.xml',
        'views/user_permission/res_users_inherit_views.xml',
        # Frontend Pages
        'views/user_permission/user_permission_page.xml',
        'views/access_denied/access_denied_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Styles
            'user_permission_management/static/src/scss/user_permission.scss',
            'user_permission_management/static/src/scss/access_denied.scss',
            # User Permission Widget
            'user_permission_management/static/src/js/user_permission/user_permission_widget.js',
            'user_permission_management/static/src/js/user_permission/user_permission_entrypoint.js',
            # Access Denied Widget
            'user_permission_management/static/src/js/access_denied/access_denied_widget.js',
            'user_permission_management/static/src/js/access_denied/access_denied_entrypoint.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
