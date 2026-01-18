# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Extend res.users to add permission management"""
    _inherit = 'res.users'

    # One2many relationship to user.permission.management
    permission_management_ids = fields.One2many(
        'user.permission.management',
        'user_id',
        string='Quản lý Phân quyền',
        help='Thông tin phân quyền của user này'
    )
    
    # Computed field to get permission type
    permission_type = fields.Selection([
        ('system_admin', 'System Admin'),
        ('investor_user', 'Investor User'),
        ('fund_operator', 'Fund Operator'),
    ], string='Loại quyền', compute='_compute_permission_type', readonly=True, search='_search_permission_type')
    
    # Editable field to set permission type directly
    editable_permission_type = fields.Selection([
        ('system_admin', 'System Admin'),
        ('investor_user', 'Investor User'),
        ('fund_operator', 'Fund Operator'),
    ], string='Phân quyền', compute='_compute_editable_permission_type', inverse='_inverse_editable_permission_type', store=False)
    
    # Computed field to get is_market_maker from permission_management_ids
    is_market_maker = fields.Boolean(
        string='Nhà tạo lập',
        compute='_compute_is_market_maker',
        readonly=True,
        help='Đánh dấu Portal User là nhà tạo lập, được phép truy cập trang sổ lệnh (order_matching)'
    )
    
    @api.depends('permission_management_ids.permission_type')
    def _compute_permission_type(self):
        """Compute permission type from permission_management_ids"""
        for user in self:
            permission_rec = user.permission_management_ids[:1]  # Get first record
            if permission_rec:
                user.permission_type = permission_rec.permission_type
            else:
                user.permission_type = False
    
    @api.depends('permission_management_ids.permission_type')
    def _compute_editable_permission_type(self):
        """Compute editable permission type from permission_management_ids"""
        for user in self:
            permission_rec = user.permission_management_ids[:1]  # Get first record
            if permission_rec:
                user.editable_permission_type = permission_rec.permission_type
            else:
                user.editable_permission_type = False
    
    @api.depends('permission_management_ids.is_market_maker')
    def _compute_is_market_maker(self):
        """Compute is_market_maker from permission_management_ids"""
        for user in self:
            permission_rec = user.permission_management_ids[:1]  # Get first record
            if permission_rec:
                user.is_market_maker = permission_rec.is_market_maker
            else:
                user.is_market_maker = False
    
    def _inverse_editable_permission_type(self):
        """Inverse method to update permission_management when editable_permission_type changes"""
        for user in self:
            if not user.editable_permission_type:
                continue

            # Get or create permission management record
            permission_rec = user.permission_management_ids[:1]
            if not permission_rec:
                # Create new permission management record
                # IMPORTANT: provide 'name' explicitly to avoid NOT NULL constraint error
                vals = {
                    'user_id': user.id,
                    'name': user.name or user.login or (user.email or ''),
                    'login': user.login,
                    'email': user.email or '',
                    'permission_type': user.editable_permission_type,
                    'active': user.active,
                }
                permission_rec = self.env['user.permission.management'].sudo().create(vals)
            else:
                # Update existing permission management record
                permission_rec.sudo().write({
                    'permission_type': user.editable_permission_type,
                    # Keep name in sync with user name
                    'name': user.name or user.login or (user.email or ''),
                })

            # Update groups based on permission type
            user._update_groups_from_permission_type(user.editable_permission_type)

    def _search_permission_type(self, operator, value):
        """Search permission type by searching in permission_management_ids"""
        if operator == '=':
            return [('permission_management_ids.permission_type', '=', value)]
        elif operator == '!=':
            return [('permission_management_ids.permission_type', '!=', value)]
        elif operator == 'in':
            return [('permission_management_ids.permission_type', 'in', value)]
        elif operator == 'not in':
            return [('permission_management_ids.permission_type', 'not in', value)]
        return []

    def _infer_permission_type_from_groups(self):
        """Infer permission type from user's groups - Chỉ dùng groups mặc định của Odoo
        
        Logic phân quyền:
        - system_admin: Có base.group_user VÀ base.group_system (Internal User với System Admin)
          -> Truy cập TẤT CẢ trang/modules
        - fund_operator: Có base.group_user NHƯNG KHÔNG có base.group_system (Internal User thường)
          -> Chỉ truy cập các modules của Fund Operator
        - investor_user: Có base.group_portal VÀ KHÔNG có base.group_user (Portal User)
          -> Chỉ truy cập các modules của Portal User
        """
        self.ensure_one()
        group_system = self.env.ref('base.group_system', raise_if_not_found=False)
        group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
        group_user = self.env.ref('base.group_user', raise_if_not_found=False)
        
        has_user = group_user and group_user.id in self.groups_id.ids
        has_system = group_system and group_system.id in self.groups_id.ids
        has_portal = group_portal and group_portal.id in self.groups_id.ids
        
        # System Admin: Có cả base.group_user và base.group_system
        if has_user and has_system:
            return 'system_admin'
        
        # Investor User: Có base.group_portal và KHÔNG có base.group_user
        if has_portal and not has_user:
            return 'investor_user'
        
        # Fund Operator: Có base.group_user nhưng KHÔNG có base.group_system
        if has_user and not has_system:
            return 'fund_operator'
        
        return False

    @api.model
    def create(self, vals):
        """Override create to auto-create permission management"""
        user = super().create(vals)
        
        # Auto-create permission management if not exists
        if not user.permission_management_ids:
            permission_type = user._infer_permission_type_from_groups()
            if permission_type:
                try:
                    self.env['user.permission.management'].sudo().create({
                        'user_id': user.id,
                        'login': user.login,
                        'email': user.email or '',
                        'permission_type': permission_type,
                        'active': user.active,
                    })
                except Exception as e:
                    _logger.warning(f"Could not auto-create permission management for user {user.id}: {e}")
        
        return user

    def write(self, vals):
        """Override write to sync permission management"""
        result = super().write(vals)
        
        # If groups changed, try to sync permission type
        if 'groups_id' in vals:
            for user in self:
                if not user.permission_management_ids:
                    # Auto-create if not exists
                    permission_type = user._infer_permission_type_from_groups()
                    if permission_type:
                        try:
                            self.env['user.permission.management'].sudo().create({
                                'user_id': user.id,
                                'login': user.login,
                                'email': user.email or '',
                                'permission_type': permission_type,
                                'active': user.active,
                            })
                        except Exception as e:
                            _logger.warning(f"Could not auto-create permission management for user {user.id}: {e}")
                else:
                    # Update existing permission management
                    permission_type = user._infer_permission_type_from_groups()
                    if permission_type:
                        user.permission_management_ids[0].sudo().write({
                            'permission_type': permission_type,
                        })
        
        return result
    
    def _update_groups_from_permission_type(self, permission_type):
        """Update user groups based on permission type"""
        self.ensure_one()
        
        # Get group references
        user_group = self.env.ref('base.group_user', raise_if_not_found=False)
        system_group = self.env.ref('base.group_system', raise_if_not_found=False)
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        
        if not user_group or not system_group or not portal_group:
            _logger.warning("Could not find required groups for permission type update")
            return
        
        # Get current groups
        current_groups = self.groups_id.ids
        
        # Determine which groups should be assigned
        groups_to_assign = []
        
        if permission_type == 'system_admin':
            # System Admin: base.group_user + base.group_system
            groups_to_assign = [user_group.id, system_group.id]
        elif permission_type == 'fund_operator':
            # Fund Operator: base.group_user only (NOT base.group_system)
            groups_to_assign = [user_group.id]
        elif permission_type == 'investor_user':
            # Investor User: base.group_portal only (NOT base.group_user)
            groups_to_assign = [portal_group.id]
        
        # Update groups
        if groups_to_assign:
            # Remove all three groups first, then add the correct ones
            groups_to_remove = [user_group.id, system_group.id, portal_group.id]
            self.sudo().write({
                'groups_id': [(3, gid) for gid in groups_to_remove if gid in current_groups] + 
                            [(4, gid) for gid in groups_to_assign if gid not in current_groups]
            })

