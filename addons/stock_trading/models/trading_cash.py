# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class TradingCashInAdvance(models.Model):
    """Tiền ứng trước"""
    _name = 'trading.cash.cia'
    _description = 'Cash In Advance'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

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
    
    cia_amount = fields.Float(
        string='CIA Amount',
        digits=(20, 3),
        readonly=True
    )
    
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True
    )
    
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True
    )

    def action_get_cia_amount(self):
        """Lấy số tiền ứng trước"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            result = client.get_cash_cia_amount(self.account)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            if result.get('status') == 200 and result.get('data'):
                data = result['data']
                if isinstance(data, dict):
                    self.write({
                        'cia_amount': data.get('ciaAmount', 0),
                    })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã lấy số tiền ứng trước thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error getting CIA amount: {e}')
            raise UserError(_('Không thể lấy số tiền ứng trước: %s') % str(e))


class TradingCashTransfer(models.Model):
    """Chuyển tiền"""
    _name = 'trading.cash.transfer'
    _description = 'Cash Transfer'
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
        required=True,
        help='Tài khoản nguồn'
    )
    
    transfer_type = fields.Selection([
        ('internal', 'Internal Transfer'),
        ('vsd', 'VSD Transfer'),
    ], string='Transfer Type', required=True, default='internal')
    
    # For internal transfer
    beneficiary_account = fields.Char(
        string='Beneficiary Account',
        help='Tài khoản nhận (cho internal transfer)'
    )
    
    # For VSD transfer
    vsd_type = fields.Selection([
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
    ], string='VSD Type',
       help='Loại giao dịch VSD (cho VSD transfer)')
    
    amount = fields.Integer(
        string='Amount',
        required=True,
        help='Số tiền chuyển'
    )
    
    remark = fields.Text(
        string='Remark',
        help='Ghi chú'
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

    def action_submit_transfer(self):
        """Submit cash transfer"""
        self.ensure_one()
        
        if not self.code:
            raise UserError(_('Vui lòng nhập OTP code'))
        
        try:
            client = self.config_id.get_api_client()
            
            if self.transfer_type == 'internal':
                transfer_data = {
                    'account': self.account,
                    'beneficiaryAccount': self.beneficiary_account,
                    'amount': self.amount,
                    'remark': self.remark or '',
                    'code': self.code,
                }
                result = client.create_cash_transfer(transfer_data)
            else:  # vsd
                from ssi_fctrading.models import fcmodel_requests
                transfer_data = {
                    'account': self.account,
                    'amount': self.amount,
                    'type': 'deposit' if self.vsd_type == 'deposit' else 'withdraw',
                    'remark': self.remark or '',
                    'code': self.code,
                }
                req = fcmodel_requests.CashTransferVSD(**transfer_data)
                result = client._client.create_cash_transfer_vsd(req)
            
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
                    'message': _('Chuyển tiền thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error submitting cash transfer: {e}')
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Không thể chuyển tiền: %s') % str(e))


class TradingCashTransferHistory(models.Model):
    """Lịch sử chuyển tiền"""
    _name = 'trading.cash.transfer.history'
    _description = 'Cash Transfer History'
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
    
    from_date = fields.Date(
        string='From Date',
        required=True
    )
    
    to_date = fields.Date(
        string='To Date',
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

    def action_sync_history(self):
        """Sync lịch sử chuyển tiền"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            
            # Format date: DD/MM/YYYY
            from_date_str = self.from_date.strftime('%d/%m/%Y')
            to_date_str = self.to_date.strftime('%d/%m/%Y')
            
            result = client.get_cash_transfer_history(self.account, from_date_str, to_date_str)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã sync lịch sử chuyển tiền thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error syncing transfer history: {e}')
            raise UserError(_('Không thể sync lịch sử chuyển tiền: %s') % str(e))

