from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class NavMonthly(models.Model):
    _name = 'nav.monthly'
    _description = 'NAV Tháng'
    _rec_name = 'period'
    _order = 'period desc'

    # Thông tin cơ bản
    fund_id = fields.Many2one('portfolio.fund', string='Quỹ', required=True)
    period = fields.Char(string='Thời gian', required=True, help='Format: MM/YYYY (ví dụ: 12/2021)')
    nav_beginning = fields.Float(string='NAV đầu kỳ', required=True, digits=(16, 2))
    nav_ending = fields.Float(string='NAV cuối kỳ', required=True, digits=(16, 2))
    upload_date = fields.Datetime(string='Ngày upload', default=fields.Datetime.now, readonly=True)
    
    # Thông tin bổ sung
    description = fields.Text(string='Mô tả')
    status = fields.Selection([
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động')
    ], string='Trạng thái', default='active')
    
    # Computed fields
    nav_change = fields.Float(string='Thay đổi NAV', compute='_compute_nav_change', store=True)
    nav_change_percent = fields.Float(string='% Thay đổi NAV', compute='_compute_nav_change_percent', store=True)
    
    @api.depends('nav_beginning', 'nav_ending')
    def _compute_nav_change(self):
        for record in self:
            record.nav_change = record.nav_ending - record.nav_beginning
    
    @api.depends('nav_beginning', 'nav_ending')
    def _compute_nav_change_percent(self):
        for record in self:
            if record.nav_beginning > 0:
                record.nav_change_percent = ((record.nav_ending - record.nav_beginning) / record.nav_beginning) * 100
            else:
                record.nav_change_percent = 0.0
    
    # Constraints
    @api.constrains('nav_beginning', 'nav_ending')
    def _check_nav_values(self):
        for record in self:
            if record.nav_beginning <= 0:
                raise ValidationError(_('NAV đầu kỳ phải lớn hơn 0.'))
            if record.nav_ending <= 0:
                raise ValidationError(_('NAV cuối kỳ phải lớn hơn 0.'))
    
    @api.constrains('period')
    def _check_period_format(self):
        for record in self:
            if record.period:
                # Kiểm tra format MM/YYYY
                try:
                    month, year = record.period.split('/')
                    month = int(month)
                    year = int(year)
                    if month < 1 or month > 12:
                        raise ValidationError(_('Tháng phải từ 1 đến 12.'))
                    if year < 2000 or year > 2100:
                        raise ValidationError(_('Năm phải từ 2000 đến 2100.'))
                except ValueError:
                    raise ValidationError(_('Định dạng thời gian không đúng. Vui lòng sử dụng MM/YYYY (ví dụ: 12/2021).'))
    
    @api.constrains('period', 'fund_id')
    def _check_unique_period_fund(self):
        for record in self:
            if record.period and record.fund_id:
                duplicate = self.search([
                    ('period', '=', record.period),
                    ('fund_id', '=', record.fund_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('NAV tháng này đã tồn tại cho quỹ được chọn.'))
    
    def action_export_nav_data(self):
        """Xuất dữ liệu NAV tháng"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/nav_management/export_nav_monthly/{self.id}',
            'target': 'new',
        }
    
    @api.model
    def get_nav_data_by_fund(self, fund_id):
        """Lấy dữ liệu NAV tháng theo quỹ"""
        return self.search([
            ('fund_id', '=', fund_id),
            ('status', '=', 'active')
        ])
    
    @api.model
    def create_monthly_nav(self, fund_id, period, nav_beginning, nav_ending, description=''):
        """Tạo NAV tháng mới"""
        return self.create({
            'fund_id': fund_id,
            'period': period,
            'nav_beginning': nav_beginning,
            'nav_ending': nav_ending,
            'description': description
        })
