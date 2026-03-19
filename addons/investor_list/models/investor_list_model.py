from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class InvestorList(models.Model):
    _name = 'investor.list'
    _description = 'Danh sách nhà đầu tư'
    _rec_name = 'partner_name'
    _order = 'create_date desc'

    # Thông tin cơ bản từ res.users (portal users)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='user_id.partner_id', string='Partner', store=True)
    
    # Ngày mở TK - lấy từ thời gian tạo user
    open_date = fields.Datetime(string='Ngày mở TK', related='user_id.create_date', store=True)
    
    # Số tài khoản - lấy từ status_info
    account_number = fields.Char(string='Số tài khoản', compute='_compute_account_number', store=True)
    
    # Thông tin cá nhân - có thể chỉnh sửa nhưng vẫn đồng bộ từ module hồ sơ cá nhân
    partner_name = fields.Char(string='Họ tên', compute='_compute_profile_info', store=True, readonly=False)
    phone = fields.Char(string='Số điện thoại', compute='_compute_profile_info', store=True, readonly=False)
    email = fields.Char(string='Email', compute='_compute_profile_info', store=True, readonly=False)
    id_number = fields.Char(string='ĐKSH', compute='_compute_profile_info', store=True, readonly=False)
    
    # Thông tin địa chỉ - có thể chỉnh sửa nhưng vẫn đồng bộ từ module hồ sơ cá nhân
    province_city = fields.Char(string='Tỉnh/Thành phố', compute='_compute_address_info', store=True, readonly=False)
    
    # Track xem các trường đã được chỉnh sửa thủ công hay chưa
    partner_name_manual = fields.Boolean(string='Họ tên thủ công', default=False)
    phone_manual = fields.Boolean(string='SĐT thủ công', default=False)
    email_manual = fields.Boolean(string='Email thủ công', default=False)
    id_number_manual = fields.Boolean(string='ĐKSH thủ công', default=False)
    province_city_manual = fields.Boolean(string='Tỉnh/TP thủ công', default=False)
    
    # Trạng thái quản lý (Lifecycle Status)
    status = fields.Selection([
        ('draft', 'Chưa cập nhật'),       # Hồ sơ chưa hoàn thiện
        ('pending', 'Chờ KYC'),           # Hồ sơ đã xong, chờ eKYC
        ('active', 'KYC'),                # eKYC thành công
        ('vsd', 'VSD'),                   # Đã lên VSD
        ('rejected', 'Từ chối')           # Từ chối
    ], string='Trạng thái', compute='_compute_lifecycle_status', store=True, readonly=False)
    
    # Track xem trạng thái đã được set thủ công hay chưa
    status_manual = fields.Boolean(string='Manual Status', default=False)
    
    # Thông tin từ status.info - Chuyển thành compute để tự động đồng bộ
    account_status = fields.Selection([
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected')
    ], string='Account Status', compute='_compute_status_info_fields', store=True, readonly=False)
    
    profile_status = fields.Selection([
        ('complete', 'Complete'),
        ('incomplete', 'Incomplete')
    ], string='Profile Status', compute='_compute_status_info_fields', store=True, readonly=False)
    
    # Các trường tính toán
    @api.depends('partner_id')
    def _compute_account_number(self):
        for record in self:
            if record.partner_id:
                # Tìm status_info cho partner này
                status_info = self.env['status.info'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                record.account_number = status_info.account_number if status_info else ''
            else:
                record.account_number = ''
    
    @api.depends('partner_id')
    def _compute_profile_info(self):
        for record in self:
            if record.partner_id:
                # Tìm investor_profile cho partner này
                profile = self.env['investor.profile'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                
                if profile:
                    # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                    if not record.partner_name_manual:
                        record.partner_name = profile.name or record.partner_id.name
                    if not record.phone_manual:
                        record.phone = profile.phone or record.partner_id.phone
                    if not record.email_manual:
                        record.email = profile.email or record.partner_id.email
                    if not record.id_number_manual:
                        record.id_number = profile.id_number
                else:
                    # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                    if not record.partner_name_manual:
                        record.partner_name = record.partner_id.name
                    if not record.phone_manual:
                        record.phone = record.partner_id.phone
                    if not record.email_manual:
                        record.email = record.partner_id.email
                    if not record.id_number_manual:
                        record.id_number = ''
            else:
                # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                if not record.partner_name_manual:
                    record.partner_name = ''
                if not record.phone_manual:
                    record.phone = ''
                if not record.email_manual:
                    record.email = ''
                if not record.id_number_manual:
                    record.id_number = ''
    
    @api.depends('partner_id')
    def _compute_address_info(self):
        for record in self:
            if record.partner_id:
                # Tìm investor_address cho partner này
                address = self.env['investor.address'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('address_type', '=', 'permanent')
                ], limit=1)
                
                if address and address.state_id:
                    # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                    if not record.province_city_manual:
                        record.province_city = address.state_id.name
                else:
                    # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                    if not record.province_city_manual:
                        record.province_city = ''
            else:
                # Chỉ cập nhật nếu chưa được chỉnh sửa thủ công
                if not record.province_city_manual:
                    record.province_city = ''

    @api.depends('partner_id')
    def _compute_status_info_fields(self):
        """Đồng bộ account_status và profile_status từ status.info"""
        for record in self:
            if record.partner_id:
                status_info = self.env['status.info'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                if status_info:
                    record.account_status = status_info.account_status
                    record.profile_status = status_info.profile_status
                else:
                    record.account_status = 'pending'
                    record.profile_status = 'incomplete'
            else:
                record.account_status = 'pending'
                record.profile_status = 'incomplete'
    
    @api.onchange('account_status', 'profile_status')
    def _onchange_status_info(self):
        """Update status when status.info changes"""
        for record in self:
            # Update status.info if exists
            if record.partner_id:
                status_info = self.env['status.info'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                
                if status_info:
                    status_info.write({
                        'account_status': record.account_status,
                        'profile_status': record.profile_status
                    })
    
    @api.depends('account_status', 'profile_status', 'status_manual')
    def _compute_lifecycle_status(self):
        """
        New International Standard Algorithm for Status Calculation:
        - Draft: Profile not complete.
        - Pending: Profile complete but Account not approved (Waiting for review/eKYC).
        - Active: Account approved (eKYC verified or Manually approved).
        - Rejected: Account rejected.
        """
        for record in self:
            # Nếu trạng thái đã được set thủ công, không override
            if record.status_manual:
                continue
                
            if record.account_status == 'rejected':
                record.status = 'rejected'
            elif record.account_status == 'approved':
                record.status = 'active'
            elif record.profile_status == 'complete':
                # Completed profile but not approved yet -> Pending
                record.status = 'pending'
            else:
                # Incomplete profile -> Draft
                record.status = 'draft'
    
    @api.model
    def create(self, vals):
        # Đảm bảo chỉ tạo cho portal users
        if 'user_id' in vals:
            user = self.env['res.users'].browse(vals['user_id'])
            if user.share != True:  # share=True là portal user
                raise ValidationError(_('Chỉ có thể tạo danh sách cho tài khoản portal.'))
        
        record = super().create(vals)
        
        # Gửi bus notification
        record._notify_investor_change('create')
        
        return record
    
    def write(self, vals):
        # Track các trường được chỉnh sửa thủ công
        if 'partner_name' in vals:
            vals['partner_name_manual'] = True
        if 'phone' in vals:
            vals['phone_manual'] = True
        if 'email' in vals:
            vals['email_manual'] = True
        if 'id_number' in vals:
            vals['id_number_manual'] = True
        if 'province_city' in vals:
            vals['province_city_manual'] = True
        if 'status' in vals:
            vals['status_manual'] = True
        
        result = super().write(vals)
        
        # Gửi bus notification
        self._notify_investor_change('write')
        
        return result
    
    def _notify_investor_change(self, event_type):
        """Gửi bus notification khi investor data thay đổi"""
        if not self or not self.env.user:
            return
        
        channel = (self._cr.dbname, 'investor_list', 'update')
        message = {
            'type': event_type,
            'ids': self.ids,
            'user_id': self.env.user.id,
        }
        self.env['bus.bus']._sendone(channel, 'investor_list/update', message)
    
    @api.constrains('user_id')
    def _check_user_type(self):
        for record in self:
            if record.user_id and not record.user_id.share:
                raise ValidationError(_('Chỉ có thể thêm tài khoản portal vào danh sách.'))
    
    @api.constrains('user_id')
    def _check_unique_user(self):
        for record in self:
            if record.user_id:
                duplicate = self.search([
                    ('user_id', '=', record.user_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Tài khoản này đã có trong danh sách.'))
    
    def action_refresh_data(self):
        """Làm mới dữ liệu từ các module khác"""
        for record in self:
            record._compute_account_number()
            record._compute_profile_info()
            record._compute_address_info()
            record._compute_status_info_fields()
            record._compute_lifecycle_status()
        return True
    
    def reset_manual_fields(self):
        """Reset tất cả các trường về tự động (không thủ công)"""
        for record in self:
            record.partner_name_manual = False
            record.phone_manual = False
            record.email_manual = False
            record.id_number_manual = False
            record.province_city_manual = False
            record.status_manual = False
            # Trigger recompute
            record._compute_profile_info()
            record._compute_address_info()
            record._compute_status_info_fields()
            record._compute_lifecycle_status()
        return True
    
    @api.model
    def sync_portal_users(self):
        """Đồng bộ tất cả portal users vào danh sách"""
        portal_users = self.env['res.users'].search([
            ('share', '=', True),
            ('active', '=', True)
        ])
        
        for user in portal_users:
            # Kiểm tra xem đã có trong danh sách chưa
            existing = self.search([('user_id', '=', user.id)], limit=1)
            if not existing:
                self.create({
                    'user_id': user.id,
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã đồng bộ %d tài khoản portal.') % len(portal_users),
                'type': 'success',
                'sticky': False,
            }
        } 

class StatusInfo(models.Model):
    _inherit = 'status.info'

    def write(self, vals):
        res = super(StatusInfo, self).write(vals)
        # If status changed, trigger recompute in investor.list
        if any(field in vals for field in ['account_status', 'profile_status']):
            for record in self:
                investor_records = self.env['investor.list'].sudo().search([
                    ('partner_id', '=', record.partner_id.id)
                ])
                if investor_records:
                    # Force recompute by invalidating computed fields and calling compute methods
                    investor_records.invalidate_recordset([
                        'account_status', 'profile_status', 'status', 'account_number'
                    ])
                    investor_records._compute_status_info_fields()
                    investor_records._compute_lifecycle_status()
                    investor_records._compute_account_number()
        return res