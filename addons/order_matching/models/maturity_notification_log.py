# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import json
import logging

_logger = logging.getLogger(__name__)


class MaturityNotificationLog(models.Model):
    _name = 'maturity.notification.log'
    _description = 'Lịch sử gửi thông báo đáo hạn'
    _order = 'sent_at desc'

    name = fields.Char(string='Mã log', required=True, readonly=True, default=lambda self: _('New'))
    maturity_notification_id = fields.Many2one(
        'transaction.maturity.notification',
        string='Thông báo đáo hạn',
        required=True,
        ondelete='cascade',
        index=True
    )
    notification_type = fields.Selection([
        ('maturity_notification', 'Thông báo đáo hạn'),
        ('maturity_confirmation', 'Xác nhận bán')
    ], string='Loại thông báo', required=True, default='maturity_notification')
    
    user_id = fields.Many2one('res.users', string='Nhà đầu tư', related='maturity_notification_id.user_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Đối tác', required=True, readonly=True)
    transaction_id = fields.Many2one('portfolio.transaction', string='Lệnh giao dịch', related='maturity_notification_id.transaction_id', store=True, readonly=True)
    fund_id = fields.Many2one('portfolio.fund', string='Quỹ', related='maturity_notification_id.fund_id', store=True, readonly=True)
    
    title = fields.Char(string='Tiêu đề', readonly=True)
    message = fields.Text(string='Nội dung', readonly=True)
    
    sent_at = fields.Datetime(string='Thời gian gửi', required=True, readonly=True, default=fields.Datetime.now)
    sent_status = fields.Selection([
        ('success', 'Thành công'),
        ('failed', 'Thất bại')
    ], string='Trạng thái gửi', default='success', readonly=True)
    error_message = fields.Text(string='Thông báo lỗi', readonly=True)
    
    channel_name = fields.Char(string='Channel', readonly=True, help='Channel đã gửi qua bus')
    payload_data = fields.Text(string='Dữ liệu payload', readonly=True, help='Dữ liệu JSON đã gửi')
    
    sell_order_id = fields.Many2one('portfolio.transaction', string='Lệnh bán', readonly=True, help='Lệnh bán đã tạo (nếu là xác nhận)')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            try:
                sequence = self.env['ir.sequence'].next_by_code('maturity.notification.log')
                if sequence:
                    vals['name'] = sequence
                else:
                    from odoo import fields as fields_module
                    today = fields_module.Date.today()
                    vals['name'] = f"LOG/{today.strftime('%Y%m%d')}/NEW"
            except Exception:
                from odoo import fields as fields_module
                today = fields_module.Date.today()
                vals['name'] = f"LOG/{today.strftime('%Y%m%d')}/FALLBACK"
        return super(MaturityNotificationLog, self).create(vals)

