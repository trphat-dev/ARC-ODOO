from odoo import http
from odoo.http import request, Response
import json
import logging
import traceback
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access

_logger = logging.getLogger(__name__)


class SecurityController(http.Controller):
    """
    Handles Security-related operations:
    - OTP Configuration & Verification
    - Digital Signature Helpers (PDF Path)
    """

    @http.route('/save_signed_pdf_path', type='http', auth='user', csrf=False, methods=['POST'])
    def save_signed_pdf_path(self, **kwargs):
        """Save signed PDF path to session"""
        file_path = kwargs.get("file_path")
        if file_path:
            request.session["signed_pdf_path"] = file_path
        return Response(
            json.dumps({"success": True}),
            content_type="application/json"
        )

    @http.route('/api/otp/config', type='json', auth='user', methods=['POST'], csrf=False)
    @require_module_access('fund_management')
    def api_otp_config(self, **kwargs):
        """Get OTP configuration and check write token validity."""
        try:
            current_user = request.env.user
            config = request.env['trading.config'].sudo().search([
                ('user_id', '=', current_user.id),
                ('active', '=', True)
            ], limit=1)
            
            if not config:
                return {
                    'success': False,
                    'otp_type': 'smart',  # Default
                    'has_valid_write_token': False,
                    'message': 'Vui lòng liên kết tài khoản giao dịch để tiếp tục.'
                }
            
            otp_type = config.otp_type or 'smart'
            
            # Check write token validity
            has_valid_token = False
            token_expires_in = ''
            if config.write_access_token:
                try:
                    from odoo.addons.stock_trading.models.utils import (
                        is_token_expired,
                        get_token_expires_in,
                        TokenConstants
                    )
                    has_valid_token = not is_token_expired(
                        config.write_access_token,
                        buffer_seconds=TokenConstants.EXPIRATION_BUFFER_SECONDS
                    )
                    if has_valid_token:
                        token_expires_in = get_token_expires_in(config.write_access_token)
                except Exception as e:
                    _logger.warning(f'[OTP Config] Error checking token validity: {e}')
            
            _logger.info(f'[OTP Config] User: {current_user.id}, OTP type: {otp_type}, Has valid token: {has_valid_token}')
            
            return {
                'success': True,
                'otp_type': otp_type,
                'has_valid_write_token': has_valid_token,
                'write_token_expires_in': token_expires_in
            }
        except Exception as e:
            _logger.error(f'[OTP Config] Error: {str(e)}')
            return {
                'success': False,
                'otp_type': 'smart',
                'has_valid_write_token': False,
                'message': 'Đã xảy ra lỗi. Vui lòng thử lại.'
            }

    @http.route('/api/otp/verify', type='json', auth='user', methods=['POST'], csrf=False)
    @require_module_access('fund_management')
    def api_otp_verify(self, **kwargs):
        """Verify OTP with stock_trading module integration."""
        try:
            code = (kwargs.get('otp') or kwargs.get('code') or '').strip()
            
            if not code:
                return {
                    'success': False, 
                    'message': 'Thiếu mã OTP. Vui lòng nhập mã OTP 6 chữ số.'
                }

            current_user = request.env.user
            _logger.info(f'[OTP Verify] User: {current_user.id} ({current_user.login}), OTP: {code[:2]}**')
            
            config = request.env['trading.config'].sudo().search([
                ('user_id', '=', current_user.id),
                ('active', '=', True)
            ], limit=1)
            
            if not config:
                return {
                    'success': False, 
                    'message': 'Vui lòng liên kết tài khoản giao dịch trước khi thực hiện giao dịch.'
                }

            otp_type = config.otp_type or 'smart'
            
            from odoo.addons.stock_trading.models.trading_api_client import TradingAPIClient
            from odoo.exceptions import UserError
            
            try:
                client = TradingAPIClient(config)
                token = client.verify_code(code)
                
                _logger.info(f'[OTP Verify] Success for user {current_user.id}')
                return {
                    'success': True, 
                    'message': 'OTP đã được xác thực thành công.',
                    'write_token': token,
                    'otp_type': otp_type
                }
            except UserError as ue:
                error_msg = str(ue)
                _logger.error(f'[OTP Verify] UserError: {error_msg}')
                if 'synchronization' in error_msg.lower():
                    return {'success': False, 'message': 'Mã OTP hết hạn/không hợp lệ. Vui lòng kiểm tra lại.'}
                elif 'wrong' in error_msg.lower():
                    return {'success': False, 'message': 'Mã OTP không chính xác.'}
                else:
                    return {'success': False, 'message': 'Không thể xác thực OTP. Vui lòng thử lại.'}
            except Exception as api_error:
                _logger.error(f'[OTP Verify] API Error: {api_error}')
                return {'success': False, 'message': 'Lỗi hệ thống khi xác thực OTP.'}
                
        except Exception as e:
            _logger.error(f'[OTP Verify] Unexpected error: {str(e)}')
            return {
                'success': False, 
                'message': 'Đã xảy ra lỗi. Vui lòng thử lại sau.'
            }
