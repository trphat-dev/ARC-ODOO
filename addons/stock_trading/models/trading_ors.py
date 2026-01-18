# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class TradingORS(models.Model):
    """Online Right Subscription - Đăng ký quyền mua"""
    _name = 'trading.ors'
    _description = 'Online Right Subscription'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )
    
    config_id = fields.Many2one(
        'trading.config',
        string='API Configuration',
        required=True,
        ondelete='restrict'
    )
    
    account = fields.Char(
        string='Account',
        required=True
    )
    
    instrument_id = fields.Many2one(
        'ssi.securities',
        string='Instrument',
        required=True,
        ondelete='restrict'
    )
    
    instrument_code = fields.Char(
        related='instrument_id.symbol',
        string='Instrument Code',
        store=True,
        readonly=True
    )
    
    entitlement_id = fields.Char(
        string='Entitlement ID',
        required=True,
        help='ID quyền mua'
    )
    
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        help='Khối lượng đăng ký'
    )
    
    amount = fields.Float(
        string='Amount',
        required=True,
        digits=(20, 3),
        help='Số tiền'
    )
    
    code = fields.Char(
        string='Code',
        help='OTP code (cần thiết khi submit)'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)
    
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )
    
    submitted_at = fields.Datetime(
        string='Submitted At',
        readonly=True
    )

    def action_submit_ors(self):
        """Submit ORS registration"""
        self.ensure_one()
        
        if not self.code:
            raise UserError(_('Vui lòng nhập OTP code'))
        
        try:
            client = self.config_id.get_api_client()
            
            ors_data = {
                'account': self.account,
                'instrumentID': self.instrument_code,
                'entitlementID': self.entitlement_id,
                'quantity': self.quantity,
                'amount': self.amount,
                'code': self.code,
            }
            
            result = client.create_ors(ors_data)
            
            self.write({
                'state': 'success',
                'raw_response': json.dumps(result, indent=2),
                'submitted_at': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đăng ký quyền mua thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error submitting ORS: {e}')
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Không thể đăng ký quyền mua: %s') % str(e))


class TradingORSDividend(models.Model):
    """Cổ tức ORS"""
    _name = 'trading.ors.dividend'
    _description = 'ORS Dividend'
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )
    
    config_id = fields.Many2one(
        'trading.config',
        string='API Configuration',
        required=True,
        ondelete='restrict'
    )
    
    account = fields.Char(
        string='Account',
        required=True
    )
    
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True
    )
    
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True
    )

    def action_get_dividend(self):
        """Lấy cổ tức ORS"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            result = client.get_ors_dividend(self.account)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã lấy cổ tức ORS thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error getting ORS dividend: {e}')
            raise UserError(_('Không thể lấy cổ tức ORS: %s') % str(e))

