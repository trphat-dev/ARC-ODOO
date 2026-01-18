# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class TradingStockTransfer(models.Model):
    """Chuyển khoản cổ phiếu"""
    _name = 'trading.stock.transfer'
    _description = 'Stock Transfer'
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
    
    beneficiary_account = fields.Char(
        string='Beneficiary Account',
        required=True,
        help='Tài khoản nhận'
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
    
    exchange_id = fields.Char(
        string='Exchange ID',
        required=True,
        help='Mã sàn (HOSE, HNX, UPCOM)'
    )
    
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        help='Khối lượng chuyển'
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
        """Submit stock transfer"""
        self.ensure_one()
        
        if not self.code:
            raise UserError(_('Vui lòng nhập OTP code'))
        
        try:
            client = self.config_id.get_api_client()
            
            transfer_data = {
                'account': self.account,
                'beneficiaryAccount': self.beneficiary_account,
                'exchangeID': self.exchange_id,
                'instrumentID': self.instrument_code,
                'quantity': self.quantity,
                'code': self.code,
            }
            
            result = client.create_stock_transfer(transfer_data)
            
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
                    'message': _('Chuyển khoản cổ phiếu thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error submitting stock transfer: {e}')
            self.write({
                'state': 'error',
                'error_message': str(e),
            })
            raise UserError(_('Không thể chuyển khoản cổ phiếu: %s') % str(e))


class TradingStockTransferable(models.Model):
    """Cổ phiếu có thể chuyển"""
    _name = 'trading.stock.transferable'
    _description = 'Stock Transferable'
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

    def action_get_transferable(self):
        """Lấy cổ phiếu có thể chuyển"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            result = client.get_stock_transferable(self.account)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã lấy danh sách cổ phiếu có thể chuyển thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error getting transferable: {e}')
            raise UserError(_('Không thể lấy danh sách cổ phiếu có thể chuyển: %s') % str(e))


class TradingStockTransferHistory(models.Model):
    """Lịch sử chuyển khoản cổ phiếu"""
    _name = 'trading.stock.transfer.history'
    _description = 'Stock Transfer History'
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
    
    start_date = fields.Date(
        string='Start Date',
        required=True
    )
    
    end_date = fields.Date(
        string='End Date',
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
        """Sync lịch sử chuyển khoản"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            
            # Format date: DD/MM/YYYY
            start_date_str = self.start_date.strftime('%d/%m/%Y')
            end_date_str = self.end_date.strftime('%d/%m/%Y')
            
            from ssi_fctrading.models import fcmodel_requests
            req = fcmodel_requests.StockTransferHistory(
                account=self.account,
                startDate=start_date_str,
                endDate=end_date_str
            )
            result = client._client.get_stock_transfer_history(req)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã sync lịch sử chuyển khoản thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error syncing transfer history: {e}')
            raise UserError(_('Không thể sync lịch sử chuyển khoản: %s') % str(e))

