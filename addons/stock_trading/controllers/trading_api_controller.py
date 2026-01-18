# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class TradingAPIController(http.Controller):
    """REST API Controller cho trading operations"""
    
    @http.route('/api/trading/v1/order', type='json', auth='user', methods=['POST'], csrf=False)
    def create_order(self, **kwargs):
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {'status': 'error', 'message': 'config_id is required'}
            
            config = request.env['trading.config'].browse(config_id)
            if not config.exists():
                return {'status': 'error', 'message': 'Config not found'}
            
            # Create order
            order = request.env['trading.order'].create({
                'config_id': config_id,
                'account': kwargs.get('account'),
                'instrument_code': kwargs.get('instrument_code'),
                'market': kwargs.get('market', 'VN'),
                'buy_sell': kwargs.get('buy_sell'),
                'order_type': kwargs.get('order_type', 'stock'),
                'order_type_detail': kwargs.get('order_type_detail', 'LO'),
                'price': kwargs.get('price'),
                'quantity': kwargs.get('quantity'),
            })
            
            # Link instrument if found
            instrument = request.env['ssi.securities'].search([
                ('symbol', '=', kwargs.get('instrument_code'))
            ], limit=1)
            if instrument:
                order.instrument_id = instrument.id
            
            # Submit order
            order.action_submit_order()
            
            return {
                'status': 'success',
                'order_id': order.id,
                'order_name': order.name,
                'api_order_id': order.api_order_id,
            }
        except Exception as e:
            _logger.error(f'Error creating order: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/api/trading/v1/order/<int:order_id>/cancel', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_order(self, order_id, **kwargs):
        """Hủy order"""
        try:
            order = request.env['trading.order'].browse(order_id)
            if not order.exists():
                return {'status': 'error', 'message': 'Order not found'}
            
            order.action_cancel_order()
            
            return {
                'status': 'success',
                'message': 'Order cancelled successfully',
            }
        except Exception as e:
            _logger.error(f'Error canceling order: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/api/trading/v1/balance', type='json', auth='user', methods=['POST'], csrf=False)
    def get_balance(self, **kwargs):
        """
        Lấy số dư tài khoản
        
        Body:
        {
            "config_id": 1,
            "account": "123456",
            "balance_type": "stock"
        }
        """
        try:
            config_id = kwargs.get('config_id')
            account = kwargs.get('account')
            balance_type = kwargs.get('balance_type', 'stock')
            
            if not config_id or not account:
                return {'status': 'error', 'message': 'config_id and account are required'}
            
            config = request.env['trading.config'].browse(config_id)
            if not config.exists():
                return {'status': 'error', 'message': 'Config not found'}
            
            # Create balance record
            balance = request.env['trading.account.balance'].create({
                'config_id': config_id,
                'account': account,
                'balance_type': balance_type,
            })
            
            # Sync balance
            balance.action_sync_balance()
            
            # Parse response
            import json
            response = json.loads(balance.raw_response) if balance.raw_response else {}
            
            return {
                'status': 'success',
                'data': response.get('data', {}),
            }
        except Exception as e:
            _logger.error(f'Error getting balance: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/api/trading/v1/position', type='json', auth='user', methods=['POST'], csrf=False)
    def get_position(self, **kwargs):
        """
        Lấy vị thế
        
        Body:
        {
            "config_id": 1,
            "account": "123456",
            "position_type": "stock"
        }
        """
        try:
            config_id = kwargs.get('config_id')
            account = kwargs.get('account')
            position_type = kwargs.get('position_type', 'stock')
            
            if not config_id or not account:
                return {'status': 'error', 'message': 'config_id and account are required'}
            
            config = request.env['trading.config'].browse(config_id)
            if not config.exists():
                return {'status': 'error', 'message': 'Config not found'}
            
            # Create position record
            position = request.env['trading.position'].create({
                'config_id': config_id,
                'account': account,
                'position_type': position_type,
            })
            
            # Sync position
            position.action_sync_position()
            
            # Parse response
            import json
            response = json.loads(position.raw_response) if position.raw_response else {}
            
            return {
                'status': 'success',
                'data': response.get('data', {}),
            }
        except Exception as e:
            _logger.error(f'Error getting position: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/api/trading/v1/order-book', type='json', auth='user', methods=['POST'], csrf=False)
    def get_order_book(self, **kwargs):
        """
        Lấy sổ lệnh
        
        Body:
        {
            "config_id": 1,
            "account": "123456",
            "book_type": "normal"
        }
        """
        try:
            config_id = kwargs.get('config_id')
            account = kwargs.get('account')
            book_type = kwargs.get('book_type', 'normal')
            
            if not config_id or not account:
                return {'status': 'error', 'message': 'config_id and account are required'}
            
            config = request.env['trading.config'].browse(config_id)
            if not config.exists():
                return {'status': 'error', 'message': 'Config not found'}
            
            # Create order book record
            order_book = request.env['trading.order.book'].create({
                'config_id': config_id,
                'account': account,
                'book_type': book_type,
            })
            
            # Sync order book
            order_book.action_sync_order_book()
            
            # Parse response
            import json
            response = json.loads(order_book.raw_response) if order_book.raw_response else {}
            
            return {
                'status': 'success',
                'data': response.get('data', {}),
            }
        except Exception as e:
            _logger.error(f'Error getting order book: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/api/trading/v1/purchasing-power', type='json', auth='user', methods=['POST'], csrf=False)
    def get_purchasing_power(self, **kwargs):
        """
        Lấy sức mua cho user hiện tại (auto-detect config và account)
        
        Không cần params - tự động lấy từ user đang login
        
        Returns:
        {
            "status": "success",
            "data": {
                "purchasing_power": 1000000,
                "cash_balance": 2000000,
                "available_cash": 1500000,
                "max_buy_qty": 100,
                "max_sell_qty": 0
            }
        }
        """
        try:
            user = request.env.user
            
            # Tìm config của user hiện tại (KHÔNG fallback)
            config = request.env['trading.config'].sudo().search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ], limit=1)
            
            if not config:
                return {
                    'status': 'error', 
                    'message': 'No trading config found for user',
                    'data': {
                        'purchasing_power': 0,
                        'cash_balance': 0,
                        'available_cash': 0,
                        'max_buy_qty': 0,
                        'max_sell_qty': 0
                    }
                }
            
            # Lấy account từ config hoặc tìm trong balance records
            account = kwargs.get('account')
            if not account:
                # Tìm account từ balance records gần đây
                balance_rec = request.env['trading.account.balance'].sudo().search([
                    ('user_id', '=', user.id)
                ], order='write_date desc', limit=1)
                if balance_rec:
                    account = balance_rec.account
            
            if not account:
                # Fallback: lấy từ investor profile nếu có
                investor = request.env['investor.list'].sudo().search([
                    ('user_id', '=', user.id)
                ], limit=1)
                if investor and hasattr(investor, 'trading_account'):
                    account = investor.trading_account
            
            if not account:
                return {
                    'status': 'error',
                    'message': 'No trading account found for user',
                    'data': {
                        'purchasing_power': 0,
                        'cash_balance': 0,
                        'available_cash': 0,
                        'max_buy_qty': 0,
                        'max_sell_qty': 0
                    }
                }
            
            # Tạo hoặc cập nhật balance record
            balance = request.env['trading.account.balance'].sudo().search([
                ('user_id', '=', user.id),
                ('account', '=', account),
                ('balance_type', '=', 'stock')
            ], limit=1)
            
            if not balance:
                balance = request.env['trading.account.balance'].sudo().create({
                    'user_id': user.id,
                    'account': account,
                    'balance_type': 'stock',
                    'auto_sync': True
                })
            else:
                # Sync lại nếu balance đã tồn tại
                try:
                    balance.action_sync_balance()
                except Exception as sync_err:
                    _logger.warning(f'Failed to sync balance: {sync_err}')
            
            return {
                'status': 'success',
                'data': {
                    'purchasing_power': balance.purchasing_power or 0,
                    'cash_balance': balance.cash_balance or 0,
                    'available_cash': balance.available_cash or 0,
                    'max_buy_qty': 0,  # Sẽ tính ở frontend dựa vào NAV
                    'max_sell_qty': 0,
                    'account': account,
                    'last_sync': str(balance.last_sync) if balance.last_sync else None
                }
            }
        except Exception as e:
            _logger.error(f'Error getting purchasing power: {e}')
            return {
                'status': 'error', 
                'message': str(e),
                'data': {
                    'purchasing_power': 0,
                    'cash_balance': 0,
                    'available_cash': 0,
                    'max_buy_qty': 0,
                    'max_sell_qty': 0
                }
            }
