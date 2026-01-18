# -*- coding: utf-8 -*-
"""
Custom Auth - Redirect Controller
==================================
Xử lý điều hướng người dùng sau khi đăng nhập dựa trên permission_type
từ user.permission.management model.

Permission Types:
- system_admin: Full access -> /odoo/apps
- fund_operator: Internal limited -> /investor_list
- investor_user: Portal access -> /investment_dashboard
"""

import logging
from odoo import http
from odoo.http import request
from odoo.addons.custom_auth.constants import (
    PERMISSION_SYSTEM_ADMIN,
    PERMISSION_FUND_OPERATOR,
    PERMISSION_INVESTOR_USER,
    get_redirect_url
)

_logger = logging.getLogger(__name__)


class CustomAuthRedirectController(http.Controller):
    """
    Controller để xử lý điều hướng người dùng sau khi đăng nhập
    dựa trên permission_type từ user.permission.management
    """
    
    def _get_user_permission_type(self, user):
        """
        Lấy permission_type của user từ user.permission.management
        
        Returns:
            str: 'system_admin', 'fund_operator', 'investor_user' hoặc False
        """
        if not user or user._is_public():
            return False
        
        try:
            permission_mgmt = request.env['user.permission.management'].sudo().search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ], limit=1)
            
            if permission_mgmt:
                return permission_mgmt.permission_type
            
            # Fallback: Infer from groups if no permission_management record
            if user.has_group('base.group_system'):
                return PERMISSION_SYSTEM_ADMIN
            elif user.has_group('base.group_portal'):
                return PERMISSION_INVESTOR_USER
            elif user.has_group('base.group_user'):
                return PERMISSION_FUND_OPERATOR
            
            return False
            
        except Exception as e:
            _logger.error("Error getting permission type for user %s: %s", user.id, str(e))
            return False
    
    def _get_redirect_url(self, permission_type):
        """
        Lấy URL redirect dựa trên permission_type
        
        Args:
            permission_type: 'system_admin', 'fund_operator', 'investor_user'
            
        Returns:
            str: URL để redirect
        """
        return get_redirect_url(permission_type)
    
    @http.route('/web/login_redirect', type='http', auth='user', website=True)
    def login_redirect(self, **kw):
        """Route để điều hướng người dùng sau khi đăng nhập"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        redirect_url = self._get_redirect_url(permission_type)
        
        _logger.info("Redirecting user %s (permission: %s) to %s", 
                     user.login, permission_type, redirect_url)
        
        return request.redirect(redirect_url)
    
    @http.route('/web/session/redirect_after_login', type='json', auth='user')
    def redirect_after_login(self, **kw):
        """JSON endpoint để xác định URL điều hướng sau khi đăng nhập"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        redirect_url = self._get_redirect_url(permission_type)
        
        return {'url': redirect_url, 'permission_type': permission_type}