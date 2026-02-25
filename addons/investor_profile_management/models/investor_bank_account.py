from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class InvestorBankAccount(models.Model):
    _name = 'investor.bank.account'
    _description = 'Investor Bank Account'

    active = fields.Boolean(default=True, string='Active')
    investor_id = fields.Many2one('investor.profile', string='Investor', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='investor_id.partner_id', string='Partner', store=True)
    bank_name = fields.Char(string='Tên ngân hàng', required=True)
    account_number = fields.Char(string='Số tài khoản', required=True)
    account_holder = fields.Char(string='Tên chủ tài khoản', required=True)
    branch = fields.Char(string='Chi nhánh', required=True)
    is_default = fields.Boolean(string='Default Account')

    # New fields from 'Thông tin khác'
    company_name = fields.Char(string='Công ty nơi làm việc')
    company_address = fields.Char(string='Địa chỉ Công ty')
    occupation = fields.Char(string='Nghề nghiệp')
    monthly_income = fields.Float(string='Mức thu nhập hàng tháng')
    position = fields.Char(string='Chức vụ')

    @api.model
    def create(self, vals):
        if not vals.get('investor_id') and vals.get('partner_id'):
            investor_profile = self.env['investor.profile'].search([('partner_id', '=', vals['partner_id'])], limit=1)
            if investor_profile:
                vals['investor_id'] = investor_profile.id
            else:
                raise ValidationError(_('Không tìm thấy hồ sơ nhà đầu tư cho đối tác này.'))

        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.env['investor.profile'].browse(vals.get('investor_id')).partner_id.id),
                ('is_default', '=', True)
            ]).write({'is_default': False})
        record = super().create(vals)
        if record.partner_id:
            self.env['status.info']._check_and_update_profile_status(record.partner_id.id)
        return record

    def write(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.partner_id.id),
                ('is_default', '=', True),
                ('id', '!=', self.id)
            ]).write({'is_default': False})
        res = super().write(vals)
        if self.partner_id:
            self.env['status.info']._check_and_update_profile_status(self.partner_id.id)
        return res

    @api.constrains('account_number')
    def _check_account_number(self):
        for record in self:
            if record.account_number:
                if not re.match(r'^[0-9]{9,19}$', record.account_number):
                    raise ValidationError(_('Số tài khoản không hợp lệ. Vui lòng nhập 9-19 chữ số.'))

    @api.constrains('monthly_income')
    def _check_monthly_income(self):
        for record in self:
            if record.monthly_income and record.monthly_income < 0:
                raise ValidationError(_('Mức thu nhập không thể âm.'))

    @api.constrains('bank_name', 'account_number')
    def _check_unique_account(self):
        for record in self:
            if record.bank_name and record.account_number:
                duplicate = self.search([
                    ('bank_name', '=', record.bank_name),
                    ('account_number', '=', record.account_number),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Tài khoản ngân hàng này đã tồn tại trong hệ thống.'))

    def toggle_active(self):
        for record in self:
            record.active = not record.active
