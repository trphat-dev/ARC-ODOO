# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from ..utils import (
    TokenConstants,
    get_token_expires_in,
)

_logger = logging.getLogger(__name__)


class TradingConfig(models.Model):
    """Cấu hình kết nối FastConnect Trading API"""
    _name = 'trading.config'
    _description = 'Trading API Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help='Tên cấu hình để dễ quản lý'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Chỉ cấu hình active mới được sử dụng'
    )
    
    # API Credentials
    api_url = fields.Char(
        string='API URL',
        required=True,
        default='https://fc-tradeapi.ssi.com.vn/',
        help='URL của FastConnect Trading API'
    )
    
    stream_url = fields.Char(
        string='Stream URL',
        required=True,
        default='https://fc-tradehub.ssi.com.vn/',
        help='URL của FastConnect Trading Stream (SignalR)'
    )
    
    consumer_id = fields.Char(
        string='Consumer ID',
        required=True,
        help='Consumer ID từ SSI'
    )
    
    consumer_secret = fields.Char(
        string='Consumer Secret',
        required=True,
        help='Consumer Secret từ SSI'
    )
    
    private_key = fields.Text(
        string='Private Key (Base64)',
        required=True,
        help='Private Key dạng Base64 để ký requests'
    )
    
    two_fa_type = fields.Selection([
        ('1', 'OTP (SMS/Email)'),
    ], string='Two Factor Type', default='1', required=True, readonly=True,
       help='Loại xác thực 2 yếu tố: OTP được gửi qua SMS/Email (chỉ hỗ trợ OTP)')
    
    otp_type = fields.Selection([
        ('sms_email', 'SMS/Email OTP'),
        ('smart', 'Smart OTP'),
    ], string='OTP Type', default='smart', required=True,
       help='Loại OTP: SMS/Email OTP (cần gọi Get OTP) hoặc Smart OTP (từ ứng dụng SSI Iboard Pro)')
    
    account = fields.Char(
        string='Default Account',
        help='Tài khoản mặc định (sẽ tự động điền vào order khi chọn config này)'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        help='User liên kết với config này (dùng để tìm config từ investor)'
    )
    
    # Token Management
    read_access_token = fields.Char(
        string='Read Access Token',
        readonly=True,
        help='Access token cho đọc dữ liệu (tự động refresh)'
    )
    
    read_token_expire_at = fields.Datetime(
        string='Read Token Expires At',
        readonly=True,
        help='Thời gian hết hạn read token'
    )
    
    write_access_token = fields.Char(
        string='Write Access Token',
        readonly=True,
        help='Access token cho ghi dữ liệu (cần verify code)'
    )
    
    write_token_expire_at = fields.Datetime(
        string='Write Token Expires At',
        readonly=True,
        help='Thời gian hết hạn write token'
    )
    
    write_token_expires_in = fields.Char(
        string='Write Token Expires In',
        compute='_compute_write_token_expires_in',
        store=False,
        readonly=True,
        help='Thời gian còn lại của write token (cooldown)'
    )
    
    @api.depends('write_access_token')
    def _compute_write_token_expires_in(self):
        """Tính thời gian còn lại của write token (cooldown)"""
        for record in self:
            if not record.write_access_token:
                record.write_token_expires_in = ''
                continue
            
            try:
                # Sử dụng utility function để tính và format thời gian còn lại
                record.write_token_expires_in = get_token_expires_in(record.write_access_token)
            except Exception:
                record.write_token_expires_in = ''
    
    last_notify_id = fields.Char(
        string='Last Notify ID',
        default='-1',
        help='ID của notification cuối cùng để tiếp tục streaming'
    )
    
    # Status
    is_connected = fields.Boolean(
        string='Is Connected',
        compute='_compute_is_connected',
        help='Trạng thái kết nối API'
    )
    
    # Notes
    notes = fields.Text(string='Notes')

    @api.depends('read_access_token', 'read_token_expire_at')
    def _compute_is_connected(self):
        """Kiểm tra xem đã kết nối được API chưa"""
        for record in self:
            record.is_connected = bool(record.read_access_token)

    @api.constrains('api_url', 'stream_url')
    def _check_urls(self):
        """Validate URL format"""
        for record in self:
            if record.api_url and not record.api_url.startswith(('http://', 'https://')):
                raise ValidationError(_('API URL phải bắt đầu bằng http:// hoặc https://'))
            if record.stream_url and not record.stream_url.startswith(('http://', 'https://')):
                raise ValidationError(_('Stream URL phải bắt đầu bằng http:// hoặc https://'))

    def get_api_client(self):
        """Lấy API client instance để sử dụng"""
        self.ensure_one()
        from ...models.trading_api_client import TradingAPIClient
        
        return TradingAPIClient(self)
    
    def action_test_connection(self):
        """Test kết nối API"""
        self.ensure_one()
        try:
            client = self.get_api_client()
            client.get_access_token()  # Test lấy access token
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Kết nối API thành công!'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error(f'Error testing connection: {e}')
            raise UserError(_('Không thể kết nối API: %s') % str(e))
    
    def action_get_otp(self):
        """
        Lấy OTP từ SSI (chỉ khi dùng OTP authentication)
        
        OTP sẽ được gửi qua SMS hoặc Email theo cấu hình SSI.
        Sau khi nhận được OTP, user cần:
        1. Nhập OTP vào field "OTP Code"
        2. Click "Verify Code" để lấy write token
        """
        self.ensure_one()
        
        # Kiểm tra two_fa_type (luôn phải là OTP)
        if self.two_fa_type != '1':
            raise UserError(_('Two Factor Type phải là OTP (SMS/Email).'))
        
        try:
            client = self.get_api_client()
            result = client.get_otp()
            
            # Kiểm tra response
            if isinstance(result, dict):
                status = result.get('status', 0)
                message = result.get('message', '')
                
                if status == 200:
                    # OTP đã được gửi thành công
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('OTP đã được gửi'),
                            'message': _('OTP đã được gửi thành công qua SMS/Email.\n\nVui lòng:\n1. Kiểm tra SMS hoặc Email để lấy OTP code\n2. Nhập OTP vào field "OTP Code"\n3. Click "Verify Code" để lấy write token\n\nLưu ý: OTP có thời hạn (thường 5-10 phút) và chỉ dùng được 1 lần.'),
                            'type': 'success',
                            'sticky': True,  # Sticky để user có thời gian đọc
                        }
                    }
                else:
                    # Lỗi từ API
                    error_msg = message or f'API returned status {status}'
                    raise UserError(_('Không thể lấy OTP: %s') % error_msg)
            else:
                # Response không đúng format, nhưng vẫn thông báo thành công (có thể API đã gửi OTP)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('OTP Request Sent'),
                        'message': _('Yêu cầu lấy OTP đã được gửi. Vui lòng kiểm tra SMS/Email.'),
                        'type': 'success',
                        'sticky': True,
                    }
                }
        except UserError:
            # Re-raise UserError để giữ nguyên thông báo
            raise
        except Exception as e:
            _logger.error(f'Error getting OTP: {e}')
            raise UserError(_('Không thể lấy OTP: %s') % str(e))

