# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import json

_logger = logging.getLogger(__name__)


class TradingAccountBalance(models.Model):
    """Số dư tài khoản chứng khoán"""
    _name = 'trading.account.balance'
    _description = 'Trading Account Balance'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Prefer using user_id; investor_id kept for backward compatibility
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='restrict',
        help='Owner user of this trading account balance'
    )
    investor_id = fields.Many2one(
        'investor.list',
        string='Investor',
        required=False,
        ondelete='restrict',
        help='Backward compatibility: old link to investor list'
    )
    
    config_id = fields.Many2one(
        'trading.config',
        string='API Configuration',
        compute='_compute_config_id',
        store=True,
        readonly=True,
        help='API Configuration (tự động lấy từ Investor)'
    )
    
    @api.depends('user_id', 'investor_id')
    def _compute_config_id(self):
        """Lấy config từ investor (qua user_id)"""
        for record in self:
            target_user_id = False
            if record.user_id:
                target_user_id = record.user_id.id
            elif record.investor_id and record.investor_id.user_id:
                target_user_id = record.investor_id.user_id.id
            if target_user_id:
                config = self.env['trading.config'].search([
                    ('user_id', '=', target_user_id),
                    ('active', '=', True)
                ], limit=1)
                record.config_id = config.id if config else False
            else:
                record.config_id = False

    @api.constrains('user_id')
    def _check_user_has_config(self):
        for record in self:
            if record.user_id and not record.config_id:
                raise ValidationError(_('User "%s" chưa có API Configuration.') % (record.user_id.name))
    
    account = fields.Char(
        string='Account',
        required=True,
        help='Tài khoản chứng khoán'
    )
    
    balance_type = fields.Selection([
        ('stock', 'Stock Account'),
        ('derivative', 'Derivative Account'),
        ('pp_mmr', 'PP & MMR Account'),
    ], string='Balance Type', required=True, default='stock')
    
    # Response Data (JSON)
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True,
        help='Raw JSON response từ API'
    )
    
    # Parsed fields (có thể parse từ JSON nếu cần)
    cash_balance = fields.Float(
        string='Cash Balance',
        digits=(20, 3),
        readonly=True
    )
    
    available_cash = fields.Float(
        string='Available Cash',
        digits=(20, 3),
        readonly=True
    )
    
    purchasing_power = fields.Float(
        string='Purchasing Power',
        digits=(20, 3),
        readonly=True,
        help='Sức mua (số tiền có thể dùng để mua chứng khoán)'
    )
    
    # Timestamps
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True
    )
    
    # Notes
    notes = fields.Text(string='Notes')
    
    auto_sync = fields.Boolean(
        string='Auto Sync',
        default=True,
        help='Tự động sync balance khi tạo hoặc cập nhật record'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động sync balance khi tạo record mới"""
        records = super().create(vals_list)
        # Auto sync sau khi tạo nếu có đủ thông tin
        for record in records:
            if record.auto_sync and record.config_id and record.account:
                try:
                    record.action_sync_balance()
                except Exception as e:
                    _logger.warning(f'Auto sync balance failed for new record {record.id}: {e}')
        return records
    
    def write(self, vals):
        """Tự động sync balance khi update config_id hoặc account"""
        # Lưu giá trị auto_sync trước khi write (nếu không có trong vals)
        auto_sync_enabled = {}
        for record in self:
            auto_sync_enabled[record.id] = vals.get('auto_sync', record.auto_sync) if 'auto_sync' in vals else record.auto_sync
        
        result = super().write(vals)
        
        # Auto sync nếu update config_id, account, hoặc balance_type và có đủ thông tin
        # Chỉ sync nếu auto_sync = True (có thể bị tắt trong lần update này)
        if vals.get('config_id') or vals.get('account') or vals.get('balance_type'):
            for record in self:
                if auto_sync_enabled.get(record.id, True) and record.config_id and record.account:
                    try:
                        record.action_sync_balance()
                    except Exception as e:
                        _logger.warning(f'Auto sync balance failed for record {record.id}: {e}')
        return result
    
    @api.onchange('config_id', 'account')
    def _onchange_config_or_account(self):
        """Tự động sync khi thay đổi config_id hoặc account (trong form)"""
        if self.auto_sync and self.config_id and self.account:
            try:
                # Chỉ sync nếu record đã có ID (đã lưu vào database)
                if self.id:
                    self.action_sync_balance()
            except Exception as e:
                _logger.warning(f'Auto sync balance failed on onchange: {e}')
                # Không raise error để không block user input

    def action_sync_balance(self):
        """Sync balance từ API"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            
            # Chuẩn hoá account: trim + uppercase để đồng nhất với các API khác
            account_clean = str(self.account or '').strip().upper()
            if not account_clean:
                raise UserError(_('Account không được để trống'))
            
            if self.balance_type == 'stock':
                result = client.get_stock_account_balance(account_clean)
            elif self.balance_type == 'derivative':
                result = client.get_derivative_account_balance(account_clean)
            else:  # pp_mmr
                from ssi_fctrading.models import fcmodel_requests
                req = fcmodel_requests.PPMMRAccount(account=account_clean)
                result = client._client.get_pp_mmr_account(req)
            
            # Save response
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            # Parse và lưu các field quan trọng nếu có (linh hoạt dict/list, tên key)
            if isinstance(result, dict):
                status = result.get('status')
                data = result.get('data')
                # Một số API trả trực tiếp dict mà không có status/data
                parsed = None
                if isinstance(data, dict):
                    parsed = data
                elif isinstance(data, list) and data:
                    # Lấy phần tử đầu nếu list
                    parsed = data[0] if isinstance(data[0], dict) else None
                elif status is None:
                    # Không có status/data: coi result là payload
                    parsed = result
                
                if isinstance(parsed, dict):
                    # Hỗ trợ nhiều biến thể key từ API
                    cash_balance = (
                        parsed.get('cashBalance') or parsed.get('cash_balance') or parsed.get('cash') or parsed.get('cashBal') or 0
                    )
                    available_cash = (
                        parsed.get('availableCash') or parsed.get('available_cash') or parsed.get('available') or parsed.get('withdrawable') or 0
                    )
                    purchasing_power = (
                        parsed.get('purchasingPower') or parsed.get('purchasing_power') or parsed.get('purchasingPower') or available_cash or 0
                    )
                    try:
                        cash_balance = float(cash_balance)
                    except Exception:
                        cash_balance = 0.0
                    try:
                        available_cash = float(available_cash)
                    except Exception:
                        available_cash = 0.0
                    try:
                        purchasing_power = float(purchasing_power)
                    except Exception:
                        purchasing_power = available_cash if available_cash > 0 else 0.0
                    self.write({
                        'cash_balance': cash_balance,
                        'available_cash': available_cash,
                        'purchasing_power': purchasing_power,
                    })
            elif isinstance(result, list) and result:
                # Một số API có thể trả list các mục số dư
                first = result[0]
                if isinstance(first, dict):
                    cash_balance = first.get('cashBalance') or first.get('cash') or first.get('cashBal') or 0
                    available_cash = first.get('availableCash') or first.get('available') or first.get('withdrawable') or 0
                    purchasing_power = first.get('purchasingPower') or first.get('purchasing_power') or available_cash or 0
                    try:
                        cash_balance = float(cash_balance)
                    except Exception:
                        cash_balance = 0.0
                    try:
                        available_cash = float(available_cash)
                    except Exception:
                        available_cash = 0.0
                    try:
                        purchasing_power = float(purchasing_power)
                    except Exception:
                        purchasing_power = available_cash if available_cash > 0 else 0.0
                    self.write({
                        'cash_balance': cash_balance,
                        'available_cash': available_cash,
                        'purchasing_power': purchasing_power,
                    })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã sync số dư thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error syncing balance: {e}')
            raise UserError(_('Không thể sync số dư: %s') % str(e))

    @api.model
    def cron_sync_balances(self):
        """Cron: Tự động sync số dư cho các bản ghi gần đây"""
        # Lấy tối đa 50 bản ghi gần nhất để tránh chạy quá lâu
        records = self.search([], order='write_date desc', limit=50)
        for rec in records:
            try:
                rec.action_sync_balance()
            except Exception as e:
                _logger.warning(f'Cron sync balance failed for {rec.id}: {e}')


class TradingPosition(models.Model):
    """Vị thế chứng khoán"""
    _name = 'trading.position'
    _description = 'Trading Position'
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
        required=True,
        help='Tài khoản'
    )
    
    position_type = fields.Selection([
        ('stock', 'Stock Position'),
        ('derivative', 'Derivative Position'),
    ], string='Position Type', required=True, default='stock')
    
    query_summary = fields.Boolean(
        string='Query Summary',
        default=True,
        help='Lấy summary position (chỉ cho derivative)'
    )
    
    # Response Data
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True
    )
    
    # Timestamps
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True
    )
    
    # Notes
    notes = fields.Text(string='Notes')

    detail_ids = fields.One2many(
        'trading.position.detail',
        'position_id',
        string='Position Details'
    )

    def action_sync_position(self):
        """Sync position từ API"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            
            if self.position_type == 'stock':
                result = client.get_stock_position(self.account)
            else:
                result = client.get_derivative_position(self.account, self.query_summary)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            # Xóa chi tiết cũ
            self.detail_ids.unlink()
            
            # Parse và tạo chi tiết mới
            if result.get('status') == 200:
                data = result.get('data')
                
                # Chuẩn hóa data thành list
                items = []
                if isinstance(data, dict):
                    # Trường hợp API trả về dict object bọc list (thường là 'stockPositions' hoặc tương tự)
                    # Nếu data chính là list các vị thế
                     items = [data]
                elif isinstance(data, list):
                    items = data
                
                # Map fields
                details_to_create = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                        
                    # Support API variants
                    symbol = item.get('instrumentID') or item.get('symbol') or item.get('code') or ''
                    
                    # Logic xác định số lượng
                    quantity = float(item.get('quantity') or item.get('onHand') or 0)
                    available = float(item.get('transferable') or item.get('available') or 0)
                    market_price = float(item.get('marketPrice') or item.get('closePrice') or 0)
                    avg_price = float(item.get('avgPrice') or item.get('averagePrice') or 0)
                    
                    # T+ fields (Tên field có thể thay đổi tùy version)
                    receiving_t0 = float(item.get('boughtT0') or item.get('receivingT0') or 0)
                    receiving_t1 = float(item.get('boughtT1') or item.get('receivingT1') or 0)
                    receiving_t2 = float(item.get('boughtT2') or item.get('receivingT2') or 0)
                    
                    details_to_create.append({
                        'position_id': self.id,
                        'symbol': symbol,
                        'quantity': quantity,
                        'available': available,
                        'market_price': market_price,
                        'avg_price': avg_price,
                        'market_value': quantity * market_price,
                        'receiving_t0': receiving_t0,
                        'receiving_t1': receiving_t1,
                        'receiving_t2': receiving_t2,
                        'profit_loss': (market_price - avg_price) * quantity if quantity > 0 else 0,
                        'profit_loss_rate': ((market_price - avg_price) / avg_price * 100) if avg_price > 0 else 0,
                    })
                
                if details_to_create:
                    self.env['trading.position.detail'].create(details_to_create)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã sync vị thế thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error syncing position: {e}')
            raise UserError(_('Không thể sync vị thế: %s') % str(e))

    @api.model
    def cron_sync_positions(self):
        """Cron: Tự động sync vị thế cho các bản ghi gần đây"""
        records = self.search([], order='write_date desc', limit=50)
        for rec in records:
            try:
                rec.action_sync_position()
            except Exception as e:
                _logger.warning(f'Cron sync position failed for {rec.id}: {e}')


class TradingPositionDetail(models.Model):
    """Chi tiết vị thế (List View items)"""
    _name = 'trading.position.detail'
    _description = 'Trading Position Detail'
    
    position_id = fields.Many2one('trading.position', string='Position', ondelete='cascade')
    
    symbol = fields.Char(string='Mã CK')
    quantity = fields.Float(string='Tổng KL', digits=(16, 0))
    available = fields.Float(string='Khả dụng', digits=(16, 0))
    
    avg_price = fields.Float(string='Giá TB', digits=(16, 2))
    market_price = fields.Float(string='Giá TT', digits=(16, 2))
    market_value = fields.Float(string='Giá trị TT', digits=(20, 0))
    
    profit_loss = fields.Float(string='Lãi/Lỗ', digits=(20, 0))
    profit_loss_rate = fields.Float(string='% Lãi/Lỗ', digits=(6, 2))
    
    # T+ fields
    receiving_t0 = fields.Float(string='T+0 (Hôm nay)', digits=(16, 0))
    receiving_t1 = fields.Float(string='T+1 (Về mai)', digits=(16, 0))
    receiving_t2 = fields.Float(string='T+2 (Về kia)', digits=(16, 0))



class TradingMaxQuantity(models.Model):
    """Khối lượng mua/bán tối đa"""
    _name = 'trading.max.quantity'
    _description = 'Trading Max Quantity'
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
    
    price = fields.Float(
        string='Price',
        required=True,
        digits=(16, 3)
    )
    
    quantity_type = fields.Selection([
        ('buy', 'Max Buy Quantity'),
        ('sell', 'Max Sell Quantity'),
    ], string='Quantity Type', required=True, default='buy')
    
    max_quantity = fields.Integer(
        string='Max Quantity',
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

    def action_get_max_quantity(self):
        """Lấy max quantity từ API"""
        self.ensure_one()
        
        try:
            client = self.config_id.get_api_client()
            
            if self.quantity_type == 'buy':
                result = client.get_max_buy_qty(self.account, self.instrument_code, self.price)
            else:
                result = client.get_max_sell_qty(self.account, self.instrument_code, str(self.price))
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
            
            # Parse max quantity
            if result.get('status') == 200 and result.get('data'):
                data = result['data']
                if isinstance(data, dict):
                    max_qty = data.get('maxQuantity') or data.get('maxQty') or 0
                    self.write({'max_quantity': int(max_qty)})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã lấy max quantity thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error getting max quantity: {e}')
            raise UserError(_('Không thể lấy max quantity: %s') % str(e))

    @api.model
    def cron_get_max_quantities(self):
        """Cron: Tự động lấy max quantity cho các bản ghi gần đây"""
        records = self.search([], order='write_date desc', limit=50)
        for rec in records:
            try:
                rec.action_get_max_quantity()
            except Exception as e:
                _logger.warning(f'Cron get max quantity failed for {rec.id}: {e}')

