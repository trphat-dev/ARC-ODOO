# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class UserPermissionManagement(models.Model):
    """Model quản lý phân quyền user trong hệ thống"""
    _name = 'user.permission.management'
    _description = 'User Permission Management'
    _order = 'name asc'

    name = fields.Char(string='Tên người dùng', required=True, compute='_compute_name', store=True, readonly=True)
    login = fields.Char(string='Tên đăng nhập', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    active = fields.Boolean(string='Kích hoạt', default=True)
    
    # Phân quyền
    permission_type = fields.Selection([
        ('system_admin', 'System Admin'),
        ('investor_user', 'Investor User'),
        ('fund_operator', 'Fund Operator'),
    ], string='Loại quyền', required=True, default='fund_operator')
    
    # Phân quyền đặc biệt cho Portal User
    is_market_maker = fields.Boolean(
        string='Nhà tạo lập',
        default=False,
        help='Nếu được bật, Portal User này sẽ được phép truy cập trang sổ lệnh (order_matching). '
             'Chỉ áp dụng cho Investor User.'
    )
    
    # Thông tin user Odoo
    user_id = fields.Many2one('res.users', string='User Odoo', required=False, ondelete='cascade', index=True)
    
    # Thông tin bổ sung
    phone = fields.Char(string='Số điện thoại')
    notes = fields.Text(string='Ghi chú')
    
    # Temporary field for password (not stored in database)
    password = fields.Char(string='Mật khẩu', help='Nhập mật khẩu khi tạo mới user. Để trống nếu không muốn đặt mật khẩu.')
    
    # Audit fields
    create_date = fields.Datetime(string='Ngày tạo', readonly=True)
    write_date = fields.Datetime(string='Ngày cập nhật', readonly=True)
    create_uid = fields.Many2one('res.users', string='Người tạo', readonly=True)
    write_uid = fields.Many2one('res.users', string='Người cập nhật', readonly=True)

    @api.depends('user_id')
    def _compute_name(self):
        for rec in self:
            if rec.user_id:
                rec.name = rec.user_id.name
            else:
                rec.name = rec.login or ''

    @api.model
    def create(self, vals):
        """Tạo user permission với validation"""
        # Kiểm tra login đã tồn tại chưa
        if vals.get('login'):
            existing = self.search([('login', '=', vals['login'])], limit=1)
            if existing:
                raise ValidationError(_("Login '%(login)s' already exists!") % {'login': vals['login']})
        
        # Kiểm tra email đã tồn tại chưa
        if vals.get('email'):
            existing = self.search([('email', '=', vals['email'])], limit=1)
            if existing:
                raise ValidationError(_("Email '%(email)s' already exists!") % {'email': vals['email']})
        
        # Validate required fields
        if not vals.get('login'):
            raise ValidationError(_("Login is required!"))
        if not vals.get('email'):
            raise ValidationError(_("Email is required!"))
        # Ensure name is provided to avoid NOT NULL constraint issue.
        if not vals.get('name'):
            vals['name'] = vals.get('login') or vals.get('email') or 'Unknown User'
        
        # Tạo hoặc tìm user Odoo
        if not vals.get('user_id'):
            user_vals = {
                'name': vals.get('name', vals.get('login', '')),
                'login': vals.get('login'),
                'email': vals.get('email'),
                'active': vals.get('active', True),
            }
            
            # Set password nếu có
            if vals.get('password'):
                user_vals['password'] = vals.get('password')
            
            # Gán groups theo permission_type
            group_ids = self._get_group_ids_for_permission(vals.get('permission_type', 'fund_operator'))
            if group_ids:
                user_vals['groups_id'] = [(6, 0, group_ids)]
            
            user = self.env['res.users'].sudo().create(user_vals)
            vals['user_id'] = user.id
        
        # Remove password from vals before saving (it's not a stored field)
        if 'password' in vals:
            del vals['password']
        
        return super().create(vals)

    def write(self, vals):
        """Update user permission — call super first, then sync linked res.users"""
        # Remove password from vals before saving (it's not a stored field)
        password = vals.pop('password', None)
        
        res = super().write(vals)
        
        # Now update linked Odoo users
        for rec in self:
            user_vals = {}
            
            if 'name' in vals:
                user_vals['name'] = vals['name']
            if 'login' in vals:
                user_vals['login'] = vals['login']
            if 'email' in vals:
                user_vals['email'] = vals['email']
            if 'active' in vals:
                user_vals['active'] = vals['active']
            # Update groups if permission_type changed
            if 'permission_type' in vals:
                group_ids = self._get_group_ids_for_permission(vals['permission_type'])
                user_vals['groups_id'] = [(6, 0, group_ids)]
            
            if user_vals and rec.user_id:
                rec.user_id.sudo().write(user_vals)
            
            # Update password if provided (separate from other updates)
            if password and rec.user_id:
                rec.user_id.sudo().write({'password': password})
        
        return res

    def _get_group_ids_for_permission(self, permission_type):
        """Lấy danh sách group IDs theo loại quyền - Chỉ dùng groups mặc định của Odoo
        
        Phân quyền:
        - System Admin: base.group_user + base.group_system (Internal User với quyền System Admin)
          -> Truy cập TẤT CẢ trang/modules
        - Fund Operator: base.group_user (Internal User, KHÔNG có System Admin)
          -> Chỉ truy cập các modules: fund_management_dashboard, report_list, nav_management,
             transaction_list, investor_list, order_matching
        - Investor User: base.group_portal (Portal User, KHÔNG có base.group_user)
          -> Chỉ truy cập các modules: transaction_management, asset_management, fund_management,
             investor_profile_management, overview_fund_management
        """
        group_ids = []
        
        user_group = self.env.ref('base.group_user', raise_if_not_found=False)
        system_group = self.env.ref('base.group_system', raise_if_not_found=False)
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        
        if permission_type == 'system_admin':
            # System Admin: Internal User + System Admin (full permissions)
            if user_group:
                group_ids.append(user_group.id)
            if system_group:
                group_ids.append(system_group.id)
        
        elif permission_type == 'fund_operator':
            # Fund Operator: Chỉ Internal User (KHÔNG có System Admin)
            if user_group:
                group_ids.append(user_group.id)
            # Đảm bảo loại bỏ base.group_system nếu có
            if system_group and system_group.id in group_ids:
                group_ids.remove(system_group.id)
        
        elif permission_type == 'investor_user':
            # Investor User: Chỉ Portal User (KHÔNG có base.group_user)
            if portal_group:
                group_ids.append(portal_group.id)
            # Đảm bảo loại bỏ base.group_user và base.group_system nếu có
            if user_group and user_group.id in group_ids:
                group_ids.remove(user_group.id)
            if system_group and system_group.id in group_ids:
                group_ids.remove(system_group.id)
        
        return group_ids

    @api.model
    def search_users(self, domain=None, limit=100, offset=0):
        """Tìm kiếm users với pagination"""
        if domain is None:
            domain = []
        
        users = self.search(domain, limit=limit, offset=offset)
        total = self.search_count(domain)
        
        return {
            'users': users.read(),
            'total': total,
        }

    def action_deactivate(self):
        """Vô hiệu hóa user"""
        self.write({'active': False})
        if self.user_id:
            self.user_id.sudo().write({'active': False})

    def action_activate(self):
        """Kích hoạt user"""
        self.write({'active': True})
        if self.user_id:
            self.user_id.sudo().write({'active': True})

    def action_view_user(self):
        """Mở form view của user Odoo"""
        self.ensure_one()
        if not self.user_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'User',
            'res_model': 'res.users',
            'res_id': self.user_id.id,
            'view_mode': 'form',
            'target': 'current',
            'domain': [],  # Explicit empty domain to avoid parsing errors
            'context': {},  # Explicit empty context
        }

    @api.constrains('email')
    def _check_email(self):
        """Kiểm tra email hợp lệ"""
        import re
        for rec in self:
            if rec.email:
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(pattern, rec.email):
                    raise ValidationError(_("Invalid email format!"))

    @api.constrains('login')
    def _check_login(self):
        """Kiểm tra login không được trùng"""
        for rec in self:
            if rec.login:
                existing = self.search([
                    ('login', '=', rec.login),
                    ('id', '!=', rec.id)
                ], limit=1)
                if existing:
                    raise ValidationError(_("Login '%(login)s' already exists!") % {'login': rec.login})

