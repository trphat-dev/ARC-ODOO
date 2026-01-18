# -*- coding: utf-8 -*-

import json
import logging
import random
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from .utils import (
    TokenConstants,
    TimeFormatConstants,
    is_token_expired,
    get_token_expires_in,
)

_logger = logging.getLogger(__name__)


class TradingOrder(models.Model):
    """
    Unified Trading Order Model
    
    Architecture:
    1. REQUEST_ID (Odoo UUID) is the primary correlation key.
    2. API_ORDER_ID (Exchange ID) is treated as a secondary key, hydrated via Sync.
    3. STATUS SYNC source of truth is the ORDER HISTORY api (via uniqueID matching).
    """
    _name = 'trading.order'
    _description = 'Trading Order'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --- BASIC INFO ---
    name = fields.Char(string='Order Reference', required=True, readonly=True, default=lambda self: _('New'), copy=False)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='restrict', default=lambda self: self.env.user)
    
    # --- CONFIGURATION (COMPUTED) ---
    config_id = fields.Many2one('trading.config', string='API Configuration', compute='_compute_config_id', store=True, readonly=True)
    
    config_write_access_token = fields.Char(related='config_id.write_access_token', readonly=True)
    config_two_fa_type = fields.Selection(related='config_id.two_fa_type', readonly=True)
    
    # UI Helpers
    has_valid_write_token = fields.Boolean(compute='_compute_token_status')
    write_token_expires_in = fields.Char(compute='_compute_token_status')

    @api.depends('user_id')
    def _compute_config_id(self):
        for record in self:
            if record.user_id:
                record.config_id = self.env['trading.config'].search([('user_id', '=', record.user_id.id), ('active', '=', True)], limit=1)
            else:
                record.config_id = False

    @api.depends('config_id', 'config_write_access_token')
    def _compute_token_status(self):
        for record in self:
            if not record.config_id or not record.config_write_access_token:
                record.has_valid_write_token = False
                record.write_token_expires_in = ''
                continue
            try:
                record.has_valid_write_token = not is_token_expired(record.config_write_access_token, buffer_seconds=TokenConstants.EXPIRATION_BUFFER_SECONDS)
                record.write_token_expires_in = get_token_expires_in(record.config_write_access_token)
            except Exception:
                record.has_valid_write_token = False
                record.write_token_expires_in = ''

    # --- ORDER DETAILS ---
    order_type = fields.Selection([('stock', 'Stock Order'), ('derivative', 'Derivative Order')], string='Order Type', required=True, default='stock')
    market = fields.Selection([('VN', 'VN - Thị trường cơ sở'), ('VNFE', 'VNFE - Thị trường phái sinh')], string='Market', required=True, default='VN')
    
    account = fields.Char(string='Account', required=True)
    config_account = fields.Char(related='config_id.account', readonly=True)
    
    # Purchasing Power Helper
    account_balance_id = fields.Many2one('trading.account.balance', string='Account Balance', compute='_compute_purchasing_power', store=False)
    purchasing_power = fields.Float(string='Purchasing Power', compute='_compute_purchasing_power', digits=(20, 3))

    instrument_id = fields.Many2one('ssi.securities', string='Instrument', required=True)
    instrument_code = fields.Char(related='instrument_id.symbol', store=True, readonly=True)
    
    buy_sell = fields.Selection([('B', 'Buy'), ('S', 'Sell')], string='Buy/Sell', required=True)
    order_type_detail = fields.Selection([
        ('LO', 'Limit Order'), ('MP', 'Market Price'), ('ATO', 'At The Opening'), 
        ('ATC', 'At The Closing'), ('PLO', 'Post Limit Order'), ('MTL', 'Market To Limit'),
        ('MAK', 'Match and Kill'), ('MOK', 'Match or Kill')
    ], string='Order Type Detail', required=True, default='LO')
    
    quantity = fields.Integer(string='Quantity', required=True)
    price = fields.Float(string='Price', digits=(16, 2))
    
    # --- EXECUTION STATUS (Hydrated by Sync) ---
    request_id = fields.Char(string='Request ID', required=True, readonly=True, default=lambda self: self._generate_request_id())
    api_order_id = fields.Char(string='API Order ID', readonly=True, help="Exchange Order ID (populated after sync)")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('partially_filled', 'Partially Filled'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)
    
    filled_quantity = fields.Integer(string='Filled Qty', readonly=True)
    filled_price = fields.Float(string='Avg Filled Price', digits=(16, 2), readonly=True)
    cancel_quantity = fields.Integer(string='Cancel Qty', readonly=True)
    
    api_response = fields.Text(string='Raw API Response', readonly=True)
    raw_status = fields.Char(string='Raw Exchange Status', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    
    submitted_at = fields.Datetime(string='Submitted At', readonly=True)
    filled_at = fields.Datetime(string='Filled At', readonly=True)

    # --- AUTHENTICATION ---
    code = fields.Char(string='OTP Code')
    account_name = fields.Char(string='Account Name', readonly=True)
    account_verified = fields.Boolean(default=False)
    
    # --- DERIVATIVE SPECIFIC ---
    stop_order = fields.Boolean(default=False)
    stop_price = fields.Float(default=0.0)
    stop_type = fields.Char()
    stop_step = fields.Float(default=0.0)
    loss_step = fields.Float(default=0.0)
    profit_step = fields.Float(default=0.0)
    
    # --- METADATA ---
    device_id = fields.Char()
    user_agent = fields.Char()
    notes = fields.Text()
    
    # --- RELATIONS ---
    # --- RELATIONS ---
    # matched_order_id, related_order_id, is_matched_pair moved to order_matching module
    # source_transaction_id moved to fund_management module (or bridge)


    # ==========================
    # LOGIC: ID GENERATION
    # ==========================
    @api.model
    def _generate_request_id(self):
        """Generate 8-char random correlation ID used as RequestID/UniqueID"""
        import string
        chars = string.digits + string.ascii_letters
        return ''.join(random.choice(chars) for _ in range(8))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('trading.order') or _('New')
        return super().create(vals_list)

    # ==========================
    # LOGIC: SUBMIT ORDER
    # ==========================
    def action_submit_order(self):
        self.ensure_one()
        if self.state not in ['draft', 'error', 'cancelled', 'rejected']:
             raise UserError(_('Lệnh đã được gửi hoặc đang xử lý.'))

        client = self._get_client_and_verify_token()
        
        # 1. Prepare Payload
        order_data = self._prepare_order_payload(client)
        
        # 2. Execute API
        try:
            if self.order_type == 'stock':
                resp = client.new_order(order_data)
            else:
                resp = client.der_new_order(order_data)
                
            _logger.info(f"Submit Order {self.name} Response: {json.dumps(resp)}")
            
            # 3. Handle Response (Lite Check)
            # We TRUST our request_id. We do NOT immediately trust orderID from this response 
            # for 100% correctness of future lookups, as it might be temporary or garbage (TA).
            # We set state to 'submitted' and wait for Sync to hydrate the true ID.
            
            status_code = resp.get('status', 0)
            if status_code == 200:
                self.write({
                    'state': 'submitted',
                    'submitted_at': fields.Datetime.now(),
                    'api_response': json.dumps(resp, indent=2),
                    'error_message': False
                })
                return {
                    'type': 'ir.actions.client', 
                    'tag': 'display_notification',
                    'params': {'title': 'Success', 'message': 'Lệnh đã gửi thành công!', 'type': 'success'}
                }
            else:
                msg = resp.get('message', 'Unknown Error')
                self.write({'state': 'error', 'error_message': msg, 'api_response': json.dumps(resp, indent=2)})
                raise UserError(_('API Error: %s') % msg)

        except Exception as e:
            self.write({'state': 'error', 'error_message': str(e)})
            raise UserError(_('Không thể gửi lệnh: %s') % str(e))

    def _prepare_order_payload(self, client):
        account_clean = str(self.account).strip().upper()
        # Get/Set Device Info
        if not self.device_id:
            self.device_id = client.get_deviceid()
        if not self.user_agent:
            self.user_agent = client.get_user_agent()

        price_formatted = str(int(self.price)) if self.order_type == 'stock' else str(self.price)
        if self.order_type_detail in ['MP', 'ATO', 'ATC', 'MAK', 'MOK', 'MTL', 'PLO']:
             price_formatted = '0'

        payload = {
            'account': account_clean,
            'requestID': self.request_id,
            'instrumentID': self.instrument_code,
            'market': self.market,
            'buySell': self.buy_sell,
            'orderType': self.order_type_detail,
            'price': price_formatted,
            'quantity': self.quantity,
            'deviceId': self.device_id,
            'userAgent': self.user_agent,
        }
        
        if self.order_type == 'derivative':
             payload.update({
                 'code': self.code or '', # Some deriv APIs need OTP code again? (Usually handled by token)
                 # Add strict/stop logic if needed
             })
             
        return payload

    # ==========================
    # LOGIC: SYNC STATUS (The Core Logic)
    # ==========================
    def action_sync_status(self):
        """
        Synchronize order status using the Source of Truth strategy.
        1. Try to find in Order Book (Active Orders) by matching request_id.
        2. If not found, try to find in Order History (Completed Orders) by matching uniqueID/requestID.
        3. Hydrate matching data back to Odoo.
        """
        self.ensure_one()
        client = self.config_id.get_api_client()
        account_clean = str(self.account).strip().upper()
        
        # --- A. CHECK ORDER BOOK (ACTIVE) ---
        found_in_book = False
        try:
            book_res = client.get_order_book(account_clean)
            if isinstance(book_res, dict) and book_res.get('status') == 200:
                data = book_res.get('data', [])
                # Standardize to list
                items = data if isinstance(data, list) else ([data] if data else [])
                
                for item in items:
                    # Match by requestID
                    r_id = str(item.get('requestID') or item.get('request_id') or '')
                    if r_id == self.request_id:
                        self._hydrate_from_api_data(item, source='book')
                        found_in_book = True
                        break
        except Exception as e:
            _logger.warning(f"Sync Order Book error: {e}")

        if found_in_book:
            return

        # --- B. CHECK ORDER HISTORY (COMPLETED/CANCELLED) ---
        # Search window: Submitted Day - 3 days -> Today
        end_date = fields.Date.today()
        start_date = (self.submitted_at or self.create_date or fields.Datetime.now()).date() - timedelta(days=3)
        
        try:
            hist_res = client.get_order_history(
                account_clean, 
                start_date.strftime('%d/%m/%Y'), 
                end_date.strftime('%d/%m/%Y')
            )
            
            if isinstance(hist_res, dict) and hist_res.get('status') == 200:
                h_data = hist_res.get('data', {})
                # SSI history format: data.orderHistories (list)
                items = []
                if isinstance(h_data, dict):
                    items = h_data.get('orderHistories', [])
                elif isinstance(h_data, list):
                    items = h_data
                
                for item in items:
                    # Match by uniqueID (which corresponds to requestID)
                    u_id = str(item.get('uniqueID') or item.get('unique_id') or item.get('requestID') or '')
                    if u_id == self.request_id:
                        self._hydrate_from_api_data(item, source='history')
                        return
                        
        except Exception as e:
            _logger.warning(f"Sync Order History error: {e}")
            
        _logger.info(f"Order {self.name} (ReqID: {self.request_id}) not found in Book or History.")

    def _hydrate_from_api_data(self, data, source='book'):
        """Apply data from SSI to local record"""
        vals = {}
        
        # 1. Critical: Update correct Order ID
        api_id = str(data.get('orderID') or data.get('order_id') or '')
        if api_id and api_id != self.api_order_id:
            vals['api_order_id'] = api_id
            
        # 2. Status Mapping
        raw_status = str(data.get('orderStatus') or data.get('status') or '').upper()
        if raw_status:
            vals['raw_status'] = raw_status
            vals['state'] = self._map_status(raw_status)
            
        # 3. Quantities & Prices
        if 'filledQty' in data: vals['filled_quantity'] = int(data['filledQty'])
        if 'cancelQty' in data: vals['cancel_quantity'] = int(data['cancelQty'])
        if 'avgPrice' in data: vals['filled_price'] = float(data['avgPrice'])
        
        # 4. Timestamps
        if self._map_status(raw_status) == 'filled' and not self.filled_at:
            vals['filled_at'] = fields.Datetime.now()
            
        if vals:
            self.write(vals)
            _logger.info(f"Hydrated Order {self.name} from {source}: {vals}")

    def _map_status(self, code):
        mapping = {
            'FF': 'filled', 'FILLED': 'filled', 'F': 'filled',
            'PF': 'partially_filled', 'PARTIAL': 'partially_filled',
            'S': 'submitted', 'SUBMITTED': 'submitted', 'NEW': 'submitted', 'WAITING': 'pending', 'PENDING': 'pending',
            'C': 'cancelled', 'CANCELLED': 'cancelled',
            'R': 'rejected', 'REJECTED': 'rejected',
            'E': 'error'
        }
        return mapping.get(code, 'submitted')
    
    # ==========================
    # CRON: SYNC ORDER STATUS
    # ==========================
    @api.model
    def cron_sync_order_status(self):
        """
        Cron job to sync status for all active orders.
        Only syncs orders that are in 'submitted', 'pending', or 'partially_filled' states.
        """
        # Find orders that need status sync (active/pending orders)
        active_states = ['submitted', 'pending', 'partially_filled']
        orders = self.search([
            ('state', 'in', active_states),
            ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))  # Only last 7 days
        ], limit=100)  # Limit to avoid overload
        
        _logger.info("Cron: Syncing status for %d active orders", len(orders))
        
        synced = 0
        errors = 0
        for order in orders:
            try:
                order.action_sync_status()
                synced += 1
            except Exception as e:
                _logger.warning("Failed to sync order %s: %s", order.name, e)
                errors += 1
        
        _logger.info("Cron: Synced %d orders, %d errors", synced, errors)
        return True
        
    # ==========================
    # LOGIC: CANCEL & MODIFY
    # ==========================
    def action_cancel_order(self):
        self.ensure_one()
        # Must have API ID to cancel
        if not self.api_order_id:
            # Try last ditch sync
            self.action_sync_status()
            if not self.api_order_id:
                raise UserError(_('Không tìm thấy Order ID thực của sàn. Vui lòng thử sync lại.'))

        client = self._get_client_and_verify_token()
        
        cancel_data = {
            'account': str(self.account).strip().upper(),
            'requestID': str(random.randint(0, 99999999)), # New request for cancel action
            'orderID': self.api_order_id,
            'marketID': self.market,
            'instrumentID': self.instrument_code,
            'buySell': self.buy_sell,
            'deviceId': self.device_id,
            'userAgent': self.user_agent,
        }
        
        try:
            if self.order_type == 'stock':
                client.cancel_order(cancel_data)
            else:
                client.der_cancel_order(cancel_data)
            self.write({'state': 'cancelled'})
        except Exception as e:
            raise UserError(_("Cancel failed: %s") % str(e))

    # ==========================
    # HELPERS
    # ==========================
    def _get_client_and_verify_token(self):
        if not self.config_id:
            raise UserError(_('Chưa cấu hình API Trading.'))
            
        client = self.config_id.get_api_client()
        # Ensure Write Token
        if not self.has_valid_write_token:
            # Check if OTP code provided in UI
            if self.code:
                client.ensure_write_token(self.code)
                # Clear code after use
                self.code = False
            else:
                # Or if the client token is actually valid in cache but Odoo doesn't know
                try:
                    client.ensure_write_token(None)
                except UserError:
                    raise UserError(_('Vui lòng nhập OTP để xác thực giao dịch.'))
        return client

    # UI Onchanges
    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id and self.config_id and self.config_id.account:
            self.account = self.config_id.account.strip().upper()

    @api.depends('account_balance_id', 'account_balance_id.purchasing_power')
    def _compute_purchasing_power(self):
        for record in self:
            record.purchasing_power = record.account_balance_id.purchasing_power or 0.0
            if not record.purchasing_power and record.account and record.config_id:
                 # Try one-time fallback search
                 bal = self.env['trading.account.balance'].search([('account','=',record.account), ('config_id','=',record.config_id.id)], limit=1)
                 if bal: record.purchasing_power = bal.purchasing_power
