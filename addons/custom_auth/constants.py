# -*- coding: utf-8 -*-
"""
Custom Auth - Constants
========================
Centralized configuration for permission types and redirect URLs.
Single source of truth for all redirect mappings in the module.
"""

# Permission Types
PERMISSION_SYSTEM_ADMIN = 'system_admin'
PERMISSION_FUND_OPERATOR = 'fund_operator'
PERMISSION_INVESTOR_USER = 'investor_user'

# Redirect URLs for each permission type
REDIRECT_URLS = {
    PERMISSION_SYSTEM_ADMIN: '/fund-management-dashboard',
    PERMISSION_FUND_OPERATOR: '/investor_list',
    PERMISSION_INVESTOR_USER: '/fund_widget',
}

# Default redirect when permission type is unknown
DEFAULT_REDIRECT_URL = '/web/login'


def get_redirect_url(permission_type):
    """
    Get redirect URL based on permission type.
    
    Args:
        permission_type: 'system_admin', 'fund_operator', 'investor_user'
        
    Returns:
        str: URL to redirect to
    """
    return REDIRECT_URLS.get(permission_type, DEFAULT_REDIRECT_URL)
