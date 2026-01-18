# -*- coding: utf-8 -*-
"""
Utility module để kiểm tra quyền truy cập dựa trên user type và module

Phân quyền:
- Internal User (System Admin): Có base.group_user + base.group_system -> Truy cập TẤT CẢ trang
- Fund Operator: Có base.group_user nhưng KHÔNG có base.group_system -> Chỉ truy cập các module Fund Operator
- Portal User: Có base.group_portal, KHÔNG có base.group_user -> Chỉ truy cập các module Portal
"""

from odoo import http
from odoo.http import request
from functools import wraps
import logging

_logger = logging.getLogger(__name__)

# Định nghĩa mapping giữa module và user type được phép truy cập
# Lưu ý: 
# - 'system_admin' = Internal User (có base.group_system) -> truy cập tất cả
# - 'fund_operator' = Fund Operator (chỉ có base.group_user) -> chỉ truy cập modules của Fund Operator
# - 'portal' = Portal User -> chỉ truy cập modules của Portal
MODULE_PERMISSIONS = {
    # Fund Operator modules - Chỉ Fund Operator và System Admin được truy cập
    'fund_management_dashboard': ['fund_operator', 'system_admin'],
    'report_list': ['fund_operator', 'system_admin'],
    'nav_management': ['fund_operator', 'system_admin'],
    'transaction_list': ['fund_operator', 'system_admin'],
    'investor_list': ['fund_operator', 'system_admin'],
    # order_matching: Fund Operator, System Admin, và Portal User là nhà tạo lập (market_maker)
    'order_matching': ['fund_operator', 'system_admin', 'portal_market_maker'],
    
    # Portal User modules - Chỉ Portal User và System Admin được truy cập
    'transaction_management': ['portal', 'system_admin'],
    'asset_management': ['portal', 'system_admin'],
    'fund_management': ['portal', 'system_admin'],
    'investor_profile_management': ['portal', 'system_admin'],
    'overview_fund_management': ['portal', 'system_admin'],
}

# Mapping route patterns với module names
ROUTE_MODULE_MAPPING = {
    # Fund Operator routes
    '/fund-management-dashboard': 'fund_management_dashboard',
    '/report-balance': 'report_list',
    '/report-transaction': 'report_list',
    '/report-order-history': 'report_list',
    '/report-contract-statistics': 'report_list',
    '/report-early-sale': 'report_list',
    '/report-contract-summary': 'report_list',
    '/report-purchase-contract': 'report_list',
    '/report-sell-contract': 'report_list',
    '/aoc_report': 'report_list',
    '/investor_report': 'report_list',
    '/user_list': 'report_list',
    '/list_tenors_interest_rates': 'report_list',
    '/nav_management': 'nav_management',
    '/transaction-list': 'transaction_list',
    '/investor_list': 'investor_list',
    '/order-book': 'order_matching',
    '/completed-orders': 'order_matching',
    '/negotiated-orders': 'order_matching',
    
    # Portal User routes
    '/transaction_management': 'transaction_management',
    '/asset-management': 'asset_management',
    '/fund_management': 'fund_management',
    '/account_balance': 'fund_management',
    '/personal_profile': 'investor_profile_management',
    '/bank_info': 'investor_profile_management',
    '/address_info': 'investor_profile_management',
    '/verification': 'investor_profile_management',
    '/investment_dashboard': 'overview_fund_management',
}


def get_user_permission_type(user):
    """
    Lấy permission type của user từ user.permission.management hoặc infer từ groups
    
    Returns:
        'system_admin', 'fund_operator', 'portal', hoặc None
        
    Logic:
        - system_admin: Có base.group_user + base.group_system (Internal User với quyền System Admin)
        - fund_operator: Có base.group_user nhưng KHÔNG có base.group_system (Internal User thường)
        - portal: Có base.group_portal và KHÔNG có base.group_user (Portal User)
    """
    if not user or not user.id:
        return None
    
    # Kiểm tra từ permission_management_ids trước
    permission_rec = user.permission_management_ids[:1]
    if permission_rec:
        permission_type = permission_rec.permission_type
        # Map permission_type sang user type cho permission checking
        if permission_type == 'system_admin':
            return 'system_admin'
        elif permission_type == 'fund_operator':
            return 'fund_operator'  # Fund Operator là Internal User nhưng không phải System Admin
        elif permission_type == 'investor_user':
            return 'portal'
    
    # Nếu không có permission record, infer từ groups
    group_system = request.env.ref('base.group_system', raise_if_not_found=False)
    group_portal = request.env.ref('base.group_portal', raise_if_not_found=False)
    group_user = request.env.ref('base.group_user', raise_if_not_found=False)
    
    has_user = group_user and group_user.id in user.groups_id.ids
    has_system = group_system and group_system.id in user.groups_id.ids
    has_portal = group_portal and group_portal.id in user.groups_id.ids
    
    # System Admin: Có cả base.group_user và base.group_system (Internal User với quyền System Admin)
    if has_user and has_system:
        return 'system_admin'
    
    # Portal User: Có base.group_portal và KHÔNG có base.group_user
    if has_portal and not has_user:
        return 'portal'
    
    # Fund Operator: Có base.group_user nhưng KHÔNG có base.group_system (Internal User thường)
    if has_user and not has_system:
        return 'fund_operator'
    
    return None


def check_module_access(user, module_name):
    """
    Kiểm tra xem user có quyền truy cập module không
    
    Args:
        user: res.users record
        module_name: Tên module cần kiểm tra
    
    Returns:
        True nếu có quyền, False nếu không
    
    Logic phân quyền:
        - system_admin (Internal User với System Admin): Truy cập TẤT CẢ modules
        - fund_operator: Chỉ truy cập các modules được định nghĩa trong MODULE_PERMISSIONS
        - portal: Chỉ truy cập các modules được định nghĩa trong MODULE_PERMISSIONS
        - portal_market_maker: Portal User là nhà tạo lập, được phép truy cập order_matching
    """
    if not user or not module_name:
        return False
    
    user_type = get_user_permission_type(user)
    
    if not user_type:
        return False
    
    # System Admin (Internal User với quyền System Admin) có quyền truy cập TẤT CẢ
    if user_type == 'system_admin':
        return True
    
    # Kiểm tra quyền theo module cho Fund Operator và Portal User
    allowed_types = MODULE_PERMISSIONS.get(module_name, [])
    if not allowed_types:
        # Nếu module không có trong danh sách, chỉ System Admin mới được truy cập
        # Các user type khác không được truy cập modules không được định nghĩa
        return False
    
    # Kiểm tra user type có trong danh sách được phép không
    if user_type in allowed_types:
        return True
    
    # Xử lý trường hợp đặc biệt: Portal User là market_maker truy cập order_matching
    if user_type == 'portal' and module_name == 'order_matching':
        # Kiểm tra xem user có phải là market_maker không
        permission_rec = user.permission_management_ids[:1]
        if permission_rec and permission_rec.is_market_maker:
            return True
    
    # Kiểm tra nếu module cho phép portal_market_maker và user là portal market_maker
    if 'portal_market_maker' in allowed_types and user_type == 'portal':
        permission_rec = user.permission_management_ids[:1]
        if permission_rec and permission_rec.is_market_maker:
            return True
    
    return False


def get_module_from_route(route_path):
    """
    Lấy module name từ route path
    
    Args:
        route_path: Đường dẫn route (ví dụ: '/fund-management-dashboard')
    
    Returns:
        Module name hoặc None
    """
    # Kiểm tra exact match trước
    if route_path in ROUTE_MODULE_MAPPING:
        return ROUTE_MODULE_MAPPING[route_path]
    
    # Kiểm tra partial match
    for route_pattern, module_name in ROUTE_MODULE_MAPPING.items():
        if route_path.startswith(route_pattern):
            return module_name
    
    return None


def require_module_access(module_name=None):
    """
    Decorator để kiểm tra quyền truy cập module cho controller routes
    
    Usage:
        @http.route('/some-route', type='http', auth='user', website=True)
        @require_module_access('fund_management_dashboard')
        def some_route(self, **kwargs):
            ...
    
    Args:
        module_name: Tên module cần kiểm tra. Nếu None, sẽ tự động detect từ route
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, **kwargs):
            user = request.env.user
            
            # Nếu không có module_name, thử detect từ route
            detected_module = module_name
            if not detected_module:
                route_path = request.httprequest.path
                detected_module = get_module_from_route(route_path)
            
            # Kiểm tra quyền truy cập
            if detected_module and not check_module_access(user, detected_module):
                user_type = get_user_permission_type(user)
                allowed_types = MODULE_PERMISSIONS.get(detected_module, [])
                
                # Map user type names to Vietnamese
                type_names = {
                    'system_admin': 'System Admin (Internal User)',
                    'fund_operator': 'Fund Operator (Nhân viên quỹ)',
                    'portal': 'Portal User (Nhà đầu tư)'
                }
                
                # Map allowed types to Vietnamese names
                allowed_names_map = {
                    'system_admin': 'System Admin',
                    'fund_operator': 'Fund Operator (Nhân viên quỹ)',
                    'portal': 'Portal User (Nhà đầu tư)',
                    'portal_market_maker': 'Portal User (Nhà đầu tư - Nhà tạo lập)'
                }
                allowed_names = [allowed_names_map.get(t, t) for t in allowed_types]
                
                # Nếu module là order_matching và user là portal, thêm thông tin về market_maker
                if detected_module == 'order_matching' and user_type == 'portal':
                    permission_rec = user.permission_management_ids[:1]
                    if not permission_rec or not permission_rec.is_market_maker:
                        allowed_names.append('Portal User (Nhà đầu tư - Nhà tạo lập)')
                
                _logger.warning(
                    f"Access denied: User {user.login} (type: {type_names.get(user_type, user_type)}) "
                    f"tried to access module {detected_module}"
                )
                
                # Kiểm tra xem route có phải là JSON không (dựa vào request content-type hoặc route decorator)
                # Với type='json', Odoo sẽ parse JSON và gọi function với kwargs là dict
                # Với type='http', sẽ có request.httprequest
                is_json_request = (
                    hasattr(request, 'httprequest') and 
                    request.httprequest.content_type and 
                    'application/json' in request.httprequest.content_type
                ) or (
                    hasattr(request, 'jsonrequest') and request.jsonrequest is not None
                )
                
                if is_json_request:
                    # Trả về JSON response cho type='json'
                    error_message = f'Bạn không có quyền truy cập. Chỉ {", ".join(allowed_names) if allowed_names else "System Admin"} mới được phép.'
                    return {
                        'error': 'Access Denied',
                        'message': error_message,
                        'success': False
                    }
                else:
                    # Trả về HTML response cho type='http' với layout OWL đẹp
                    import json
                    access_denied_data = json.dumps({
                        'error_title': 'Không có quyền truy cập',
                        'error_message': f'Bạn không có quyền truy cập trang này. '
                                        f'Chỉ {", ".join(allowed_names) if allowed_names else "System Admin"} mới được phép.',
                        'allowed_types': allowed_names
                    }, ensure_ascii=False)
                    return request.render('user_permission_management.access_denied_page', {
                        'access_denied_data': access_denied_data
                    })
            
            # Nếu có quyền hoặc không cần kiểm tra, tiếp tục
            return func(self, **kwargs)
        
        return wrapper
    return decorator


def check_access_or_redirect(module_name=None, redirect_url='/web/login'):
    """
    Helper function để kiểm tra quyền và trả về True/False hoặc redirect
    
    Args:
        module_name: Tên module cần kiểm tra
        redirect_url: URL để redirect nếu không có quyền
    
    Returns:
        True nếu có quyền, False nếu không
    """
    user = request.env.user
    
    # Detect module nếu không được cung cấp
    detected_module = module_name
    if not detected_module:
        route_path = request.httprequest.path
        detected_module = get_module_from_route(route_path)
    
    # Kiểm tra quyền
    if detected_module and not check_module_access(user, detected_module):
        return False
    
    return True

