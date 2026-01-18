# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class TradingOrderHistory(models.Model):
    """Lịch sử lệnh (Report)"""
    _name = 'trading.order.history'
    _description = 'Order History Report'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))
    config_id = fields.Many2one('trading.config', string='API Configuration', required=True, ondelete='restrict')
    account = fields.Char(string='Account', required=True)
    
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today)
    
    line_ids = fields.One2many('trading.order.history.line', 'history_id', string='Order Lines', readonly=True)
    
    raw_response = fields.Text(string='Raw Response', readonly=True)
    last_sync = fields.Datetime(string='Last Sync', readonly=True)

    def action_sync_history(self):
        """Sync lịch sử lệnh và parse vào lines"""
        self.ensure_one()
        try:
            client = self.config_id.get_api_client()
            start_str = self.start_date.strftime('%d/%m/%Y')
            end_str = self.end_date.strftime('%d/%m/%Y')
            
            result = client.get_order_history(self.account, start_str, end_str)
            
            # Clear old lines
            self.line_ids.unlink()
            
            lines_to_create = []
            if isinstance(result, dict) and result.get('status') == 200:
                data = result.get('data', {})
                # Handle inconsistent API format (dict vs list)
                items = []
                if isinstance(data, dict):
                    items = data.get('orderHistories', [])
                elif isinstance(data, list):
                    items = data
                    
                for item in items:
                    line_vals = {
                        'history_id': self.id,
                        'unique_id': str(item.get('uniqueID') or item.get('requestID') or ''),
                        'order_id': str(item.get('orderID') or ''),
                        'buy_sell': str(item.get('buySell') or ''),
                        'price': float(item.get('price') or 0.0),
                        'quantity': int(item.get('quantity') or 0),
                        'filled_qty': int(item.get('filledQty') or 0),
                        'order_status': str(item.get('orderStatus') or ''),
                        'market_id': str(item.get('marketID') or ''),
                        'instrument_id': str(item.get('instrumentID') or ''),
                        'input_time': str(item.get('inputTime') or ''),
                        'avg_price': float(item.get('avgPrice') or 0.0),
                        'cancel_qty': int(item.get('cancelQty') or 0),
                        'reject_reason': str(item.get('rejectReason') or ''),
                    }

                    # --- UPSERT TRADING ORDER LOGIC ---
                    linked_order_id = False
                    try:
                        req_id = str(item.get('uniqueID') or item.get('requestID') or '')
                        api_id = str(item.get('orderID') or '')
                        
                        # Find existing order by request_id (primary) or api_order_id (fallback)
                        domain = []
                        if req_id:
                            domain = [('request_id', '=', req_id)]
                        elif api_id:
                            domain = [('api_order_id', '=', api_id)]
                        
                        existing_order = self.env['trading.order'].search(domain, limit=1) if domain else None
                        
                        # Map Status
                        raw_status = str(item.get('orderStatus') or '').upper()
                        state = self.env['trading.order']._map_status(raw_status) if hasattr(self.env['trading.order'], '_map_status') else 'submitted'
                        
                        vals = {
                            'api_order_id': api_id,
                            'filled_quantity': int(item.get('filledQty') or 0),
                            'cancel_quantity': int(item.get('cancelQty') or 0),
                            'filled_price': float(item.get('avgPrice') or 0.0),
                            'state': state,
                            'raw_status': raw_status,
                        }
                        
                        if state == 'filled':
                             vals['filled_at'] = fields.Datetime.now() # Approximate

                        if existing_order:
                            # UPDATE
                            existing_order.write(vals)
                            linked_order_id = existing_order.id
                        else:
                            # CREATE NEW
                            # Need to resolve dependencies for creation
                            symbol = str(item.get('instrumentID') or '')
                            instrument = self.env['ssi.securities'].search([('symbol', '=', symbol)], limit=1)
                            
                            
                            if instrument and req_id: # Only create if we have instrument and request_id
                                vals.update({
                                    'name': _('History Sync'), # Will be auto-numbered by create
                                    'user_id': self.config_id.user_id.id or self.env.user.id,
                                    'account': self.account,
                                    'request_id': req_id,
                                    'instrument_id': instrument.id,
                                    'market': str(item.get('marketID') or 'VN'),
                                    'buy_sell': str(item.get('buySell') or 'B'),
                                    'quantity': int(item.get('quantity') or 0),
                                    'price': float(item.get('price') or 0.0),
                                    'order_type': 'stock', # Default assumption
                                    'order_type_detail': 'LO', # Default assumption
                                    'notes': _('Auto-created from Order History Sync'),
                                    'submitted_at': fields.Datetime.now(), # Approximate
                                })
                                new_order = self.env['trading.order'].create(vals)
                                linked_order_id = new_order.id
                                _logger.info(f"Created new trading order from history: {new_order.name} (ReqID: {req_id})")
                            else:
                                _logger.warning(f"Skipping creation for item {req_id}: Instrument found={bool(instrument)} ({symbol}), RequestID={req_id}")

                    except Exception as ex:
                        _logger.error(f"Failed to upsert trading order for item {item}: {ex}", exc_info=True)
                    
                    # Add linked order ID to history line
                    line_vals['trading_order_id'] = linked_order_id
                    lines_to_create.append(line_vals)
                    # ----------------------------------
            
            self.env['trading.order.history.line'].create(lines_to_create)
            
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })

        except Exception as e:
            _logger.error(f'Error syncing order history: {e}')
            raise UserError(_('Không thể sync lịch sử lệnh: %s') % str(e))


class TradingOrderHistoryLine(models.Model):
    """Chi tiết dòng lịch sử lệnh"""
    _name = 'trading.order.history.line'
    _description = 'Order History Line'

    history_id = fields.Many2one('trading.order.history', string='History Reference', ondelete='cascade')
    
    unique_id = fields.Char(string='Unique/Request ID')
    order_id = fields.Char(string='Order ID')
    instrument_id = fields.Char(string='Symbol')
    market_id = fields.Char(string='Market')
    buy_sell = fields.Char(string='B/S')
    price = fields.Float(string='Price')
    quantity = fields.Integer(string='Qty')
    filled_qty = fields.Integer(string='Filled Qty')
    avg_price = fields.Float(string='Avg Price')
    cancel_qty = fields.Integer(string='Cancel Qty')
    order_status = fields.Char(string='Status')
    input_time = fields.Char(string='Input Time')
    reject_reason = fields.Char(string='Reject Reason')
    
    trading_order_id = fields.Many2one('trading.order', string='Trading Order', readonly=True)


class TradingOrderBook(models.Model):
    """Sổ lệnh (Active Orders)"""
    _name = 'trading.order.book'
    _description = 'Order Book Report'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))
    config_id = fields.Many2one('trading.config', string='API Configuration', required=True, ondelete='restrict')
    account = fields.Char(string='Account', required=True)
    book_type = fields.Selection([('normal', 'Order Book'), ('audit', 'Audit Order Book')], default='normal', required=True)
    
    line_ids = fields.One2many('trading.order.book.line', 'book_id', string='Order Lines', readonly=True)
    
    raw_response = fields.Text(string='Raw Response', readonly=True)
    last_sync = fields.Datetime(string='Last Sync', readonly=True)

    def action_sync_order_book(self):
        self.ensure_one()
        try:
            client = self.config_id.get_api_client()
            
            if self.book_type == 'normal':
                result = client.get_order_book(self.account)
            else:
                result = client.get_audit_order_book(self.account)
            
            # Clear old lines
            self.line_ids.unlink()
            
            lines_to_create = []
            if isinstance(result, dict) and result.get('status') == 200:
                data = result.get('data')
                # API format: list or single dict
                items = data if isinstance(data, list) else ([data] if data else [])
                
                for item in items:
                     lines_to_create.append({
                        'book_id': self.id,
                        'request_id': str(item.get('requestID') or ''),
                        'order_id': str(item.get('orderID') or ''),
                        'symbol': str(item.get('instrumentID') or ''),
                        'buy_sell': str(item.get('buySell') or ''),
                        'price': float(item.get('price') or 0.0),
                        'quantity': int(item.get('quantity') or 0),
                        'filled_qty': int(item.get('filledQty') or 0),
                        'order_status': str(item.get('orderStatus') or ''),
                        'os_status': str(item.get('osStatus') or ''), # Audit specific
                        'reject_reason': str(item.get('rejectReason') or ''),
                    })
            
            self.env['trading.order.book.line'].create(lines_to_create)

            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })

        except Exception as e:
            _logger.error(f'Error syncing order book: {e}')
            raise UserError(_('Không thể sync sổ lệnh: %s') % str(e))


class TradingOrderBookLine(models.Model):
    """Chi tiết dòng sổ lệnh"""
    _name = 'trading.order.book.line'
    _description = 'Order Book Line'

    book_id = fields.Many2one('trading.order.book', string='Book Reference', ondelete='cascade')
    
    request_id = fields.Char(string='Request ID')
    order_id = fields.Char(string='Order ID')
    symbol = fields.Char(string='Symbol')
    buy_sell = fields.Char(string='B/S')
    price = fields.Float(string='Price')
    quantity = fields.Integer(string='Qty')
    filled_qty = fields.Integer(string='Filled Qty')
    order_status = fields.Char(string='Status')
    os_status = fields.Char(string='OS Status')
    reject_reason = fields.Char(string='Reject Reason')


class TradingRateLimit(models.Model):
    """Rate Limit (Simple view kept as is)"""
    _name = 'trading.rate.limit'
    _description = 'Rate Limit'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, default=lambda self: _('New'))
    config_id = fields.Many2one('trading.config', required=True)
    raw_response = fields.Text(readonly=True)
    last_sync = fields.Datetime(readonly=True)

    def action_get_rate_limit(self):
        self.ensure_one()
        try:
            client = self.config_id.get_api_client()
            result = client.get_rate_limit()
            self.write({
                'raw_response': json.dumps(result, indent=2),
                'last_sync': fields.Datetime.now(),
            })
        except Exception as e:
             raise UserError(_("Error: %s") % str(e))
