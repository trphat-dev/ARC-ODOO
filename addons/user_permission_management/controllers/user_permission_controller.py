# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)


class UserPermissionController(http.Controller):
    """Controller cho trang quản lý phân quyền user"""

    @http.route('/user-management/system-admin', type='http', auth='user', website=True)
    def system_admin_page(self, **kwargs):
        """Render trang quản lý System Admin users"""
        try:
            # Kiểm tra quyền truy cập (chỉ System Admin mới được truy cập)
            if not request.env.user.has_group('base.group_system'):
                return request.render('web.http_error', {
                    'error': 'Access Denied',
                    'error_title': 'Không có quyền truy cập',
                    'error_message': 'Bạn không có quyền truy cập trang này. Chỉ System Admin mới được phép.'
                })
            
            page_data = {
                'permission_type': 'system_admin',
                'page_title': 'Danh sách tài khoản Quản trị viên hệ thống',
                'breadcrumb_title': 'Danh sách tài khoản Quản trị viên hệ thống',
            }
            return request.render('user_permission_management.user_permission_page', {
                'user_permission_data': Markup(json.dumps(page_data))
            })
        except Exception as e:
            _logger.error(f"Error rendering system admin page: {str(e)}", exc_info=True)
            return request.render('web.http_error', {
                'error': str(e),
                'error_title': 'Lỗi',
                'error_message': 'Không thể tải trang quản lý System Admin'
            })

    @http.route('/user-management/investor-user', type='http', auth='user', website=True)
    def investor_user_page(self, **kwargs):
        """Render trang quản lý Investor Users"""
        try:
            # Kiểm tra quyền truy cập (chỉ System Admin mới được truy cập)
            if not request.env.user.has_group('base.group_system'):
                return request.render('web.http_error', {
                    'error': 'Access Denied',
                    'error_title': 'Không có quyền truy cập',
                    'error_message': 'Bạn không có quyền truy cập trang này. Chỉ System Admin mới được phép.'
                })
            
            page_data = {
                'permission_type': 'investor_user',
                'page_title': 'Danh sách Nhà đầu tư',
                'breadcrumb_title': 'Danh sách Nhà đầu tư',
            }
            return request.render('user_permission_management.user_permission_page', {
                'user_permission_data': Markup(json.dumps(page_data))
            })
        except Exception as e:
            _logger.error(f"Error rendering investor user page: {str(e)}", exc_info=True)
            return request.render('web.http_error', {
                'error': str(e),
                'error_title': 'Lỗi',
                'error_message': 'Không thể tải trang quản lý Danh sách Nhà đầu tư'
            })

    @http.route('/user-management/fund-operator', type='http', auth='user', website=True)
    def fund_operator_page(self, **kwargs):
        """Render trang quản lý Fund Operator users"""
        try:
            # Kiểm tra quyền truy cập (chỉ System Admin mới được truy cập)
            if not request.env.user.has_group('base.group_system'):
                return request.render('web.http_error', {
                    'error': 'Access Denied',
                    'error_title': 'Không có quyền truy cập',
                    'error_message': 'Bạn không có quyền truy cập trang này. Chỉ System Admin mới được phép.'
                })
            
            page_data = {
                'permission_type': 'fund_operator',
                'page_title': 'Danh sách nhân viên Quản lý quỹ',
                'breadcrumb_title': 'Danh sách nhân viên Quản lý quỹ',
            }
            return request.render('user_permission_management.user_permission_page', {
                'user_permission_data': Markup(json.dumps(page_data))
            })
        except Exception as e:
            _logger.error(f"Error rendering fund operator page: {str(e)}", exc_info=True)
            return request.render('web.http_error', {
                'error': str(e),
                'error_title': 'Lỗi',
                'error_message': 'Không thể tải trang Danh sách nhân viên Quản lý quỹ'
            })

    @http.route('/api/user-permission/check-user-type', type='json', auth='user', methods=['POST'], csrf=False)
    def check_user_type(self, **kwargs):
        """API kiểm tra user type và is_market_maker của user hiện tại"""
        try:
            user = request.env.user
            
            # Lấy permission type từ permission_checker
            from odoo.addons.user_permission_management.utils.permission_checker import get_user_permission_type
            user_type = get_user_permission_type(user)
            
            # Lấy is_market_maker từ permission record
            permission_rec = user.permission_management_ids[:1]
            is_market_maker = False
            if permission_rec and hasattr(permission_rec, 'is_market_maker'):
                is_market_maker = permission_rec.is_market_maker or False
            
            result = {
                'success': True,
                'user_type': user_type,
                'is_market_maker': is_market_maker,
            }
            return result
        except Exception as e:
            _logger.error(f"Error checking user type: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'user_type': None,
                'is_market_maker': False,
            }

    @http.route('/api/user-permission/search', type='http', auth='user', methods=['POST'], csrf=False)
    def search_users(self, **kwargs):
        """API tìm kiếm users - lấy từ res.users và join với user.permission.management"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return {'error': 'Access Denied', 'message': 'Không có quyền truy cập'}
            
            # Get JSON data from request
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                kwargs.update(data)
            except:
                pass
            
            domain = kwargs.get('domain', [])
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            search_term = kwargs.get('search', '')
            permission_type = kwargs.get('permission_type', '')
            
            # Xây dựng domain từ search term và permission_type
            if search_term:
                domain.extend([
                    '|',
                    ('name', 'ilike', search_term),
                    ('email', 'ilike', search_term),
                ])
            
            # Lấy danh sách permission records để map
            permission_domain = []
            # Lấy danh sách permission records để map
            permission_domain = []
            if permission_type:
                if permission_type == 'investor_user':
                    # Handle legacy data without explicit string: assume anything not system/fund is investor
                    permission_domain.append(('permission_type', 'not in', ['system_admin', 'fund_operator']))
                else:
                    permission_domain.append(('permission_type', '=', permission_type))
            permission_records = request.env['user.permission.management'].sudo().search(permission_domain)
            permission_map = {p.user_id.id: p for p in permission_records if p.user_id}
            assigned_user_ids = list(permission_map.keys())
            
            # Xử lý đặc biệt cho system_admin: hiển thị TẤT CẢ system admin users
            if permission_type == 'system_admin':
                # Lấy tất cả users có base.group_system (quyền admin hệ thống)
                group_system = request.env.ref('base.group_system', raise_if_not_found=False)
                
                if group_system:
                    # Tìm tất cả users có group_system
                    all_system_users = request.env['res.users'].sudo().search([
                        ('groups_id', 'in', [group_system.id])
                    ])
                    
                    system_user_ids = all_system_users.ids
                    
                    # Thêm domain để chỉ lấy system admin users
                    if system_user_ids:
                        domain.append(('id', 'in', system_user_ids))
                    else:
                        # Không có system admin user nào
                        result = {
                            'success': True,
                            'users': [],
                            'total': 0,
                        }
                        return request.make_response(
                            json.dumps(result),
                            headers=[('Content-Type', 'application/json')]
                        )
            # Xử lý đặc biệt cho investor_user: hiển thị TẤT CẢ portal users
            elif permission_type == 'investor_user':
                # Lấy tất cả portal users (có base.group_portal và không có base.group_user)
                group_portal = request.env.ref('base.group_portal', raise_if_not_found=False)
                group_user = request.env.ref('base.group_user', raise_if_not_found=False)
                
                if group_portal and group_user:
                    # Tìm tất cả users có group_portal
                    all_portal_users = request.env['res.users'].sudo().search([
                        ('groups_id', 'in', [group_portal.id])
                    ])
                    
                    # Lọc ra những users có group_portal nhưng KHÔNG có group_user
                    portal_user_ids = []
                    for user in all_portal_users:
                        has_portal = group_portal.id in user.groups_id.ids
                        has_user = group_user.id in user.groups_id.ids
                        if has_portal and not has_user:
                            portal_user_ids.append(user.id)
                    
                    # Thêm domain để chỉ lấy portal users
                    if portal_user_ids:
                        domain.append(('id', 'in', portal_user_ids))
                    else:
                        # Không có portal user nào
                        result = {
                            'success': True,
                            'users': [],
                            'total': 0,
                        }
                        return request.make_response(
                            json.dumps(result),
                            headers=[('Content-Type', 'application/json')]
                        )
            else:
                # Với các permission_type khác (fund_operator), chỉ lấy users đã được phân quyền
                if permission_type and assigned_user_ids:
                    domain.append(('id', 'in', assigned_user_ids))
                elif permission_type and not assigned_user_ids:
                    # Không có user nào với permission_type này
                    result = {
                        'success': True,
                        'users': [],
                        'total': 0,
                    }
                    return request.make_response(
                        json.dumps(result),
                        headers=[('Content-Type', 'application/json')]
                    )
            
            # Lấy users từ res.users
            all_users = request.env['res.users'].sudo().search(domain, limit=limit, offset=offset, order='name asc')
            total = request.env['res.users'].sudo().search_count(domain)
            
            result_users = []
            for user in all_users:
                permission_record = permission_map.get(user.id)
                
                # Đối với system_admin và investor_user, nếu không có permission record, vẫn hiển thị với permission_type tương ứng
                display_permission_type = permission_record.permission_type if permission_record else (permission_type if permission_type in ['system_admin', 'investor_user'] else None)
                
                p_type = display_permission_type
                # Normalize legacy types to investor_user without using the forbidden string
                if p_type and p_type not in ['system_admin', 'fund_operator', 'investor_user']:
                    p_type = 'investor_user'

                result_users.append({
                    'id': permission_record.id if permission_record else None,
                    'user_id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'email': user.email,
                    'permission_type': p_type,
                    'active': user.active,
                    'phone': permission_record.phone if permission_record else (user.phone or ''),
                    'notes': permission_record.notes if permission_record else '',
                    'has_permission': bool(permission_record),
                    'is_market_maker': permission_record.is_market_maker if permission_record and hasattr(permission_record, 'is_market_maker') else False,
                })
            
            result = {
                'success': True,
                'users': result_users,
                'total': total,
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error searching users: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/available-users', type='http', auth='user', methods=['GET'], csrf=False)
    def get_available_users(self, **kwargs):
        """API lấy danh sách users chưa được phân quyền"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return request.make_response(
                    json.dumps({'error': 'Access Denied', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            search_term = kwargs.get('search', '')
            domain = [('active', '=', True)]
            
            if search_term:
                domain.extend([
                    '|',
                    ('name', 'ilike', search_term),
                    ('email', 'ilike', search_term),
                ])
            
            # Lấy users chưa có permission record
            all_users = request.env['res.users'].sudo().search(domain, limit=50, order='name asc')
            permission_records = request.env['user.permission.management'].sudo().search([])
            assigned_user_ids = permission_records.mapped('user_id').ids
            
            available_users = all_users.filtered(lambda u: u.id not in assigned_user_ids)
            
            result = {
                'success': True,
                'users': [{
                    'id': u.id,
                    'name': u.name,
                    'login': u.login,
                    'email': u.email,
                    'phone': u.phone or '',
                } for u in available_users],
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error getting available users: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/create', type='http', auth='user', methods=['POST'], csrf=False)
    def create_user(self, **kwargs):
        """API tạo user mới và phân quyền"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return request.make_response(
                    json.dumps({'error': 'Access Denied', 'message': 'Không có quyền truy cập', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Get JSON data from request
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                kwargs.update(data)
            except:
                pass
            
            # Validate required fields
            name = kwargs.get('name', '').strip()
            email = kwargs.get('email', '').strip()
            password = kwargs.get('password', '').strip()
            
            # Nếu có login trong request, sử dụng nó (từ frontend gửi lên), nếu không thì dùng email
            login = kwargs.get('login', '').strip() or email
            
            if not name:
                return request.make_response(
                    json.dumps({'error': 'Tên người dùng không được để trống', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if not email:
                return request.make_response(
                    json.dumps({'error': 'Email không được để trống', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Validate email format
            import re
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email):
                return request.make_response(
                    json.dumps({'error': 'Email không hợp lệ', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if not password:
                return request.make_response(
                    json.dumps({'error': 'Mật khẩu không được để trống', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if len(password) < 6:
                return request.make_response(
                    json.dumps({'error': 'Mật khẩu phải có ít nhất 6 ký tự', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Kiểm tra email/login đã tồn tại chưa (vì email được dùng làm login)
            existing_user = request.env['res.users'].sudo().search([
                '|',
                ('login', '=', email),
                ('email', '=', email)
            ], limit=1)
            if existing_user:
                return request.make_response(
                    json.dumps({'error': f'Email "{email}" đã được sử dụng', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Tạo user mới thông qua user.permission.management (model sẽ tự tạo res.users)
            # Sử dụng email làm login
            vals = {
                'name': name,
                'login': email,  # Email được dùng làm login
                'email': email,
                'password': password,
                'permission_type': kwargs.get('permission_type', 'fund_operator'),
                'active': kwargs.get('active', True),
                'phone': kwargs.get('phone', ''),
                'notes': kwargs.get('notes', ''),
            }
            
            # Thêm is_market_maker nếu là investor_user
            if kwargs.get('permission_type') == 'investor_user':
                vals['is_market_maker'] = kwargs.get('is_market_maker', False)
            
            permission_record = request.env['user.permission.management'].sudo().create(vals)
            
            result = {
                'success': True,
                'user': {
                    'id': permission_record.id,
                    'user_id': permission_record.user_id.id if permission_record.user_id else None,
                    'name': permission_record.name,
                    'login': permission_record.login,
                    'email': permission_record.email,
                    'permission_type': permission_record.permission_type,
                    'is_market_maker': permission_record.is_market_maker if hasattr(permission_record, 'is_market_maker') else False,
                    'active': permission_record.active,
                },
                'message': 'Tạo user mới và phân quyền thành công'
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error creating user permission: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/update', type='http', auth='user', methods=['POST'], csrf=False)
    def update_user(self, **kwargs):
        """API cập nhật user"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return request.make_response(
                    json.dumps({'error': 'Access Denied', 'message': 'Không có quyền truy cập', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Get JSON data from request
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                kwargs.update(data)
            except:
                pass
            
            # Kiểm tra xem có id (permission record) hay user_id (res.users)
            permission_id = kwargs.get('id')
            res_user_id = kwargs.get('user_id')
            
            if permission_id:
                # Có permission record, cập nhật trực tiếp
                permission_record = request.env['user.permission.management'].sudo().browse(permission_id)
                if not permission_record.exists():
                    return request.make_response(
                        json.dumps({'error': 'Permission record không tồn tại', 'success': False}),
                        headers=[('Content-Type', 'application/json')],
                        status=404
                    )
            elif res_user_id:
                # Chưa có permission record, tìm hoặc tạo mới
                # Kiểm tra xem đã có permission record chưa
                existing_permission = request.env['user.permission.management'].sudo().search([
                    ('user_id', '=', res_user_id)
                ], limit=1)
                
                if existing_permission:
                    permission_record = existing_permission
                else:
                    # Tạo permission record mới cho portal user
                    res_user = request.env['res.users'].sudo().browse(res_user_id)
                    if not res_user.exists():
                        return request.make_response(
                            json.dumps({'error': 'User không tồn tại', 'success': False}),
                            headers=[('Content-Type', 'application/json')],
                            status=404
                        )
                    
                    # Tạo permission record mới
                    create_vals = {
                        'user_id': res_user_id,
                        'name': res_user.name,
                        'login': res_user.login,
                        'email': res_user.email,
                        'permission_type': 'investor_user',
                        'active': res_user.active,
                        'phone': kwargs.get('phone', res_user.phone or ''),
                        'notes': kwargs.get('notes', ''),
                    }
                    if 'is_market_maker' in kwargs:
                        create_vals['is_market_maker'] = kwargs.get('is_market_maker', False)
                    
                    permission_record = request.env['user.permission.management'].sudo().create(create_vals)
            else:
                return request.make_response(
                    json.dumps({'error': 'ID user hoặc user_id không hợp lệ', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            vals = {}
            if 'name' in kwargs:
                vals['name'] = kwargs['name']
            if 'login' in kwargs:
                vals['login'] = kwargs['login']
            if 'email' in kwargs:
                vals['email'] = kwargs['email']
            if 'permission_type' in kwargs:
                vals['permission_type'] = kwargs['permission_type']
            if 'active' in kwargs:
                vals['active'] = kwargs['active']
            if 'phone' in kwargs:
                vals['phone'] = kwargs['phone']
            if 'notes' in kwargs:
                vals['notes'] = kwargs['notes']
            if 'password' in kwargs and kwargs['password']:
                # Update password if provided
                vals['password'] = kwargs['password']
            
            # Cập nhật is_market_maker nếu user là investor_user (kiểm tra từ user hiện tại hoặc từ kwargs)
            current_permission_type = kwargs.get('permission_type') or permission_record.permission_type
            if current_permission_type == 'investor_user' and 'is_market_maker' in kwargs:
                vals['is_market_maker'] = kwargs.get('is_market_maker', False)
            
            if vals:
                permission_record.write(vals)
            
            # Sau khi write(), giá trị đã được cập nhật trong database, có thể đọc trực tiếp
            
            result = {
                'success': True,
                'user': {
                    'id': permission_record.id,
                    'user_id': permission_record.user_id.id if permission_record.user_id else None,
                    'name': permission_record.name,
                    'login': permission_record.login,
                    'email': permission_record.email,
                    'permission_type': permission_record.permission_type,
                    'is_market_maker': permission_record.is_market_maker if hasattr(permission_record, 'is_market_maker') else False,
                    'active': permission_record.active,
                },
                'message': 'Cập nhật user thành công'
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error updating user: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/toggle-market-maker', type='http', auth='user', methods=['POST'], csrf=False)
    def toggle_market_maker(self, **kwargs):
        """API toggle is_market_maker cho portal user"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return request.make_response(
                    json.dumps({'error': 'Access Denied', 'message': 'Không có quyền truy cập', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Get JSON data from request
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                kwargs.update(data)
            except:
                pass
            
            # Kiểm tra xem có id (permission record) hay user_id (res.users)
            permission_id = kwargs.get('id')
            res_user_id = kwargs.get('user_id')
            is_market_maker = kwargs.get('is_market_maker', False)
            
            if permission_id:
                # Có permission record, cập nhật trực tiếp
                permission_record = request.env['user.permission.management'].sudo().browse(permission_id)
                if not permission_record.exists():
                    return request.make_response(
                        json.dumps({'error': 'Permission record không tồn tại', 'success': False}),
                        headers=[('Content-Type', 'application/json')],
                        status=404
                    )
                
                # Kiểm tra phải là investor_user
                if permission_record.permission_type != 'investor_user':
                    return request.make_response(
                        json.dumps({'error': 'Chỉ có thể set nhà tạo lập cho Investor User', 'success': False}),
                        headers=[('Content-Type', 'application/json')],
                        status=400
                    )
                
                permission_record.write({'is_market_maker': is_market_maker})
                
            elif res_user_id:
                # Chưa có permission record, tìm hoặc tạo mới
                existing_permission = request.env['user.permission.management'].sudo().search([
                    ('user_id', '=', res_user_id)
                ], limit=1)
                
                if existing_permission:
                    permission_record = existing_permission
                    if permission_record.permission_type != 'investor_user':
                        return request.make_response(
                            json.dumps({'error': 'Chỉ có thể set nhà tạo lập cho Investor User', 'success': False}),
                            headers=[('Content-Type', 'application/json')],
                            status=400
                        )
                    permission_record.write({'is_market_maker': is_market_maker})
                else:
                    # Tạo permission record mới cho portal user
                    res_user = request.env['res.users'].sudo().browse(res_user_id)
                    if not res_user.exists():
                        return request.make_response(
                            json.dumps({'error': 'User không tồn tại', 'success': False}),
                            headers=[('Content-Type', 'application/json')],
                            status=404
                        )
                    
                    # Tạo permission record mới
                    create_vals = {
                        'user_id': res_user_id,
                        'name': res_user.name,
                        'login': res_user.login,
                        'email': res_user.email,
                        'permission_type': 'investor_user',
                        'active': res_user.active,
                        'phone': kwargs.get('phone', res_user.phone or ''),
                        'notes': kwargs.get('notes', ''),
                        'is_market_maker': is_market_maker,
                    }
                    
                    permission_record = request.env['user.permission.management'].sudo().create(create_vals)
            else:
                return request.make_response(
                    json.dumps({'error': 'ID user hoặc user_id không hợp lệ', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Sau khi write() hoặc create(), giá trị đã được cập nhật, không cần refresh
            
            result = {
                'success': True,
                'user': {
                    'id': permission_record.id,
                    'user_id': permission_record.user_id.id if permission_record.user_id else None,
                    'name': permission_record.name,
                    'is_market_maker': permission_record.is_market_maker if hasattr(permission_record, 'is_market_maker') else False,
                },
                'message': f'Đã {"bật" if is_market_maker else "tắt"} nhà tạo lập thành công'
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error toggling market maker: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/delete', type='http', auth='user', methods=['POST'], csrf=False)
    def delete_user(self, **kwargs):
        """API xóa user"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return {'error': 'Access Denied', 'message': 'Không có quyền truy cập', 'success': False}
            
            # Get JSON data from request
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
                kwargs.update(data)
            except:
                pass
            
            user_id = kwargs.get('id')
            if not user_id:
                return request.make_response(
                    json.dumps({'error': 'ID user không hợp lệ', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            user = request.env['user.permission.management'].sudo().browse(user_id)
            if not user.exists():
                return request.make_response(
                    json.dumps({'error': 'User không tồn tại', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            user.unlink()
            
            result = {
                'success': True,
                'message': 'Xóa user thành công'
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/user-permission/get/<int:user_id>', type='http', auth='user', methods=['GET'])
    def get_user(self, user_id, **kwargs):
        """API lấy thông tin user theo ID"""
        try:
            # Kiểm tra quyền
            if not request.env.user.has_group('base.group_system'):
                return {'error': 'Access Denied', 'message': 'Không có quyền truy cập', 'success': False}
            
            user = request.env['user.permission.management'].sudo().browse(user_id)
            if not user.exists():
                return request.make_response(
                    json.dumps({'error': 'User không tồn tại', 'success': False}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            result = {
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'email': user.email,
                    'permission_type': user.permission_type,
                    'active': user.active,
                    'phone': user.phone or '',
                    'notes': user.notes or '',
                }
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error getting user: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e), 'success': False}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

