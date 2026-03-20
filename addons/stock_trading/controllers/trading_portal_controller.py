# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from ..utils.timezone_utils import format_datetime_user_tz
import json
import logging

_logger = logging.getLogger(__name__)


class TradingPortalController(CustomerPortal):
    """Portal Controller cho Trading - Nhà đầu tư"""
    
    @http.route('/my-account', type='http', auth='user', website=True)
    def trading_portal_page(self, **kwargs):
        """Trang portal cho nhà đầu tư - Hiển thị số dư và liên kết tài khoản"""
        # Lấy user hiện tại
        current_user = request.env.user
        
        # Lấy thông tin investor từ status.info (nếu có)
        investor = request.env['status.info'].sudo().search([
            ('partner_id', '=', current_user.partner_id.id)
        ], limit=1)
        
        # Lấy tất cả configs của user (hỗ trợ nhiều tài khoản)
        configs = request.env['trading.config'].sudo().search([
            ('user_id', '=', current_user.id),
            ('active', '=', True)
        ])
        
        # Lấy tất cả account balances của user
        balances = request.env['trading.account.balance'].sudo().search([
            ('user_id', '=', current_user.id)
        ], order='last_sync desc')
        
        # Prepare accounts data - mỗi account có balance riêng
        accounts_data = []
        for config in configs:
            # Tìm balance tương ứng với account này
            balance = balances.filtered(lambda b: b.account == config.account)[:1]
            account_data = {
                'id': config.id,
                'name': config.name or config.account,
                'account': config.account,
                'consumer_id': config.consumer_id,
                'balance': None,
            }
            if balance:
                account_data['balance'] = {
                    'cash_balance': balance.cash_balance,
                    'available_cash': balance.available_cash,
                    'purchasing_power': balance.purchasing_power,
                    'last_sync': format_datetime_user_tz(request.env, balance.last_sync) if balance.last_sync else '',
                }
            accounts_data.append(account_data)
        
        # Backward compatibility: giữ lại balance_data cho tài khoản đầu tiên
        balance_data = accounts_data[0]['balance'] if accounts_data and accounts_data[0]['balance'] else None

        return request.render('stock_trading.portal_trading_page', {
            'investor': investor,
            'config': configs[:1] if configs else None,  # Backward compatible
            'balance': balances[:1] if balances else None,  # Backward compatible
            'balance_data': balance_data,
            'accounts': accounts_data,  # NEW: danh sách tất cả tài khoản
            'page_name': 'trading',
        })
    
    @http.route('/my-account/link_account', type='http', auth='user', methods=['POST'], csrf=False, website=True)
    def link_account(self, **kwargs):
        """Liên kết tài khoản SSI - Tạo hoặc cập nhật config"""
        try:
            # Parse JSON từ request body
            request_data = {}
            try:
                # Kiểm tra Content-Type
                content_type = request.httprequest.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    # Try get_json first (Werkzeug)
                    if hasattr(request.httprequest, 'get_json'):
                        request_data = request.httprequest.get_json(silent=True) or {}
                    # Fallback: get_data()
                    if not request_data:
                        raw_data = request.httprequest.get_data()
                        if raw_data:
                            request_data = json.loads(raw_data.decode('utf-8'))
                else:
                    # Nếu không phải JSON, dùng kwargs
                    request_data = kwargs
                
                # Final fallback: kwargs
                if not request_data:
                    request_data = kwargs
                    
                _logger.info(f'Parsed request data: {list(request_data.keys())}')
            except (json.JSONDecodeError, AttributeError, ValueError, UnicodeDecodeError) as e:
                _logger.warning(f'Error parsing JSON request: {e}, using kwargs')
                request_data = kwargs
            
            # Lấy user hiện tại
            current_user = request.env.user
            
            # Lấy dữ liệu từ form
            consumer_id = request_data.get('consumer_id', '').strip()
            consumer_secret = request_data.get('consumer_secret', '').strip()
            account = request_data.get('account', '').strip().upper()
            private_key = request_data.get('private_key', '').strip()
            
            # Validate
            if not consumer_id:
                return request.make_response(
                    json.dumps({'status': 'error', 'message': 'Consumer ID không được để trống'}),
                    headers=[('Content-Type', 'application/json')]
                )
            if not consumer_secret:
                return request.make_response(
                    json.dumps({'status': 'error', 'message': 'Consumer Secret không được để trống'}),
                    headers=[('Content-Type', 'application/json')]
                )
            if not account:
                return request.make_response(
                    json.dumps({'status': 'error', 'message': 'Account không được để trống'}),
                    headers=[('Content-Type', 'application/json')]
                )
            if not private_key:
                return request.make_response(
                    json.dumps({'status': 'error', 'message': 'Private Key không được để trống'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Tìm hoặc tạo config
            config = request.env['trading.config'].sudo().search([
                ('user_id', '=', current_user.id),
                ('active', '=', True)
            ], limit=1)
            
            if config:
                # Cập nhật config
                config.sudo().write({
                    'consumer_id': consumer_id,
                    'consumer_secret': consumer_secret,
                    'account': account,
                    'private_key': private_key,
                })
            else:
                # Tạo config mới với tên user
                user_name = current_user.name or current_user.login
                config = request.env['trading.config'].sudo().create({
                    'name': user_name,
                    'user_id': current_user.id,
                    'consumer_id': consumer_id,
                    'consumer_secret': consumer_secret,
                    'account': account,
                    'private_key': private_key,
                    'active': True,
                })
            
            # Tạo hoặc cập nhật account balance
            balance = request.env['trading.account.balance'].sudo().search([
                ('user_id', '=', current_user.id),
                ('balance_type', '=', 'stock')
            ], limit=1)
            
            if not balance:
                balance = request.env['trading.account.balance'].sudo().create({
                    'user_id': current_user.id,
                    'account': account,
                    'balance_type': 'stock',
                    'auto_sync': True,
                })
            else:
                balance.sudo().write({
                    'account': account,
                })
            
            # Tự động sync balance
            try:
                balance.sudo().action_sync_balance()
            except Exception as e:
                _logger.warning(f'Error syncing balance after link account: {e}')
            
            return request.make_response(
                json.dumps({
                    'status': 'success',
                    'message': 'Đã liên kết tài khoản SSI thành công!',
                    'config_id': config.id,
                    'balance_id': balance.id,
                }),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f'Error linking account: {e}')
            return request.make_response(
                json.dumps({
                    'status': 'error',
                    'message': 'Lỗi hệ thống khi liên kết tài khoản.'
                }),
                headers=[('Content-Type', 'application/json')]
            )
    
    @http.route('/my-account/get_balance', type='http', auth='user', methods=['POST'], csrf=False, website=True)
    def get_balance(self, **kwargs):
        """Lấy số dư tài khoản"""
        try:
            # Lấy user hiện tại
            current_user = request.env.user
            
            # Lấy config
            config = request.env['trading.config'].sudo().search([
                ('user_id', '=', current_user.id),
                ('active', '=', True)
            ], limit=1)
            
            if not config:
                return request.make_response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Chưa liên kết tài khoản SSI. Vui lòng liên kết tài khoản trước.'
                    }),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Lấy hoặc tạo account balance
            balance = request.env['trading.account.balance'].sudo().search([
                ('user_id', '=', current_user.id),
                ('balance_type', '=', 'stock')
            ], limit=1)
            
            if not balance:
                balance = request.env['trading.account.balance'].sudo().create({
                    'user_id': current_user.id,
                    'account': config.account or '',
                    'balance_type': 'stock',
                    'auto_sync': True,
                })
            
            # Sync balance
            balance.sudo().action_sync_balance()
            
            # Parse response
            balance_data = {}
            if balance.raw_response:
                try:
                    response = json.loads(balance.raw_response)
                    balance_data = response.get('data', {})
                except:
                    pass
            
            return request.make_response(
                json.dumps({
                    'status': 'success',
                    'balance': {
                        'cash_balance': balance.cash_balance,
                        'available_cash': balance.available_cash,
                        'purchasing_power': balance.purchasing_power,
                        'last_sync': format_datetime_user_tz(request.env, balance.last_sync) or '',
                        'raw_data': balance_data,
                    }
                }),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f'Error getting balance: {e}')
            return request.make_response(
                json.dumps({
                    'status': 'error',
                    'message': 'Lỗi hệ thống khi lấy số dư.'
                }),
                headers=[('Content-Type', 'application/json')]
            )

