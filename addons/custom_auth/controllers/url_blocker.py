# -*- coding: utf-8 -*-
"""
Custom Auth - URL Blocker Controller
=====================================
Chặn truy cập vào các URL không mong muốn và điều hướng người dùng 
về trang phù hợp dựa trên permission_type.

Permission Access Rules:
- system_admin: Full access (không bị block)
- fund_operator: Block /my, /my/home, /my/account
- investor_user: Block /web, /odoo, /my, /my/home, /my/account
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


class URLBlockerController(http.Controller):
    """
    Controller để chặn truy cập vào các URL không mong muốn
    và điều hướng người dùng về trang phù hợp
    """
    
    def _get_user_permission_type(self, user):
        """
        Lấy permission_type của user từ user.permission.management
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
            
            # Fallback: Infer from groups
            if user.has_group('base.group_system'):
                return PERMISSION_SYSTEM_ADMIN
            elif user.has_group('base.group_portal'):
                return PERMISSION_INVESTOR_USER
            elif user.has_group('base.group_user'):
                return PERMISSION_FUND_OPERATOR
            
            return False
            
        except Exception as e:
            _logger.error("Error getting permission type: %s", str(e))
            return False
    
    def _get_default_redirect(self, permission_type):
        """
        Lấy URL redirect mặc định dựa trên permission_type
        """
        return get_redirect_url(permission_type)
    
    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def block_my_home(self, **kw):
        """Chặn truy cập vào /my và /my/home"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        
        # System admin có full access
        if permission_type == PERMISSION_SYSTEM_ADMIN:
            # Allow access but redirect to proper dashboard
            return request.redirect(get_redirect_url(PERMISSION_SYSTEM_ADMIN))
        
        redirect_url = self._get_default_redirect(permission_type)
        _logger.info("Blocking /my for user %s, redirecting to %s", user.login, redirect_url)
        return request.redirect(redirect_url)
    
    @http.route('/my/account', type='http', auth='user', website=True)
    def block_my_account(self, **kw):
        """Chặn truy cập vào /my/account"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        
        # System admin có full access
        if permission_type == PERMISSION_SYSTEM_ADMIN:
            return request.redirect(get_redirect_url(PERMISSION_SYSTEM_ADMIN))
        
        redirect_url = self._get_default_redirect(permission_type)
        _logger.info("Blocking /my/account for user %s, redirecting to %s", user.login, redirect_url)
        return request.redirect(redirect_url)
    
    @http.route('/odoo', type='http', auth='user', website=True)
    def block_odoo_root(self, **kw):
        """Chặn truy cập vào /odoo cho portal users"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        
        # Chỉ system_admin mới có thể truy cập /odoo
        if permission_type == PERMISSION_SYSTEM_ADMIN:
            return request.redirect(get_redirect_url(PERMISSION_SYSTEM_ADMIN))
        
        # Portal admin bị chặn
        redirect_url = self._get_default_redirect(permission_type)
        _logger.info("Blocking /odoo for portal user %s, redirecting to %s", user.login, redirect_url)
        return request.redirect(redirect_url)
    
    @http.route('/web', type='http', auth='user', website=True)
    def handle_web_root(self, **kw):
        """Xử lý /web - redirect về đúng dashboard"""
        user = request.env.user
        permission_type = self._get_user_permission_type(user)
        
        # Chỉ system_admin mới có thể truy cập /web
        if permission_type == PERMISSION_SYSTEM_ADMIN:
            return request.redirect(get_redirect_url(PERMISSION_SYSTEM_ADMIN))
        
        # Portal admin redirect về investment dashboard
        redirect_url = self._get_default_redirect(permission_type)
        _logger.info("Handling /web for user %s, redirecting to %s", user.login, redirect_url)
        return request.redirect(redirect_url)