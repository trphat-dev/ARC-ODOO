from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import logging

from ..services import PayOSService

_logger = logging.getLogger(__name__)


class PayOSConfig(models.Model):
    """Configuration for PayOS Gateway"""
    _name = 'payos.config'
    _description = 'PayOS Configuration'
    _rec_name = 'name'
    _order = 'is_active desc, name'

    name = fields.Char('Tên cấu hình', required=True, default='Cấu hình mặc định')
    
    # PayOS Credentials
    client_id = fields.Char('Client ID', required=True)
    api_key = fields.Char('API Key', required=True)
    checksum_key = fields.Char('Checksum Key', required=True)
    
    # Base URL
    base_url = fields.Char('Base URL', default='https://api-merchant.payos.vn')

    # Demo Mode (for thesis demo: display full amount but charge reduced amount)
    demo_mode = fields.Boolean(
        'Demo Mode',
        default=False,
        help='When enabled, the actual payment amount sent to PayOS is divided by the demo divisor. '
             'Useful for thesis demos where you want to show large amounts but pay small amounts.'
    )
    demo_divisor = fields.Integer(
        'Demo Divisor',
        default=1000,
        help='Divisor applied to the payment amount in demo mode. '
             'Example: divisor=1000 means 3,000,000 VND displays but only 3,000 VND is charged.'
    )

    # Merchant Bank Account (overrides PayOS virtual account number)
    merchant_bank_name = fields.Char('Bank Name')
    merchant_account_number = fields.Char('Account Number')
    merchant_account_holder = fields.Char('Account Holder')

    # Status
    is_active = fields.Boolean('Đang hoạt động', default=True)
    last_connection_date = fields.Datetime('Ngày kết nối lần cuối', readonly=True)
    last_connection_status = fields.Selection([
        ('success', 'Thành công'),
        ('failed', 'Thất bại'),
        ('not_tested', 'Chưa kiểm tra')
    ], string='Trạng thái kết nối lần cuối', default='not_tested', readonly=True)
    connection_message = fields.Text('Thông báo kết nối', readonly=True)

    @api.model
    def get_active_config(self):
        """Lấy cấu hình đang hoạt động"""
        config = self.search([('is_active', '=', True)], limit=1)
        return config

    @api.model
    def get_or_create_config(self):
        """Lấy hoặc tạo cấu hình mặc định (singleton pattern)"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'Cấu hình mặc định',
                'is_active': True,
                'client_id': '',
                'api_key': '',
                'checksum_key': '',
            })
        return config

    def action_test_connection(self):
        """Test kết nối tới PayOS API"""
        for record in self:
            if not record.client_id or not record.api_key or not record.checksum_key:
                raise UserError(_('Vui lòng nhập đầy đủ Client ID, API Key và Checksum Key'))
            
            try:
                # Tạo PayOS service với credentials từ record
                service = PayOSService(
                    client_id=record.client_id,
                    api_key=record.api_key,
                    checksum_key=record.checksum_key,
                    base_url=record.base_url or 'https://api-merchant.payos.vn'
                )
                
                # Test kết nối bằng cách gọi API get payment link info hoặc confirm webhook
                # Hoặc đơn giản chỉ cần verify signature
                # Ở đây tôi sẽ test bằng cách tạo một payment link test nhỏ
                test_order_code = int(datetime.now().timestamp() * 1000)
                # PayOS yêu cầu description tối đa 25 ký tự
                test_data = {
                    'orderCode': test_order_code,
                    'amount': 1000,  # 1000 VND test
                    'description': 'Test connection',  # 14 ký tự - OK
                    'returnUrl': 'https://localhost/test',
                    'cancelUrl': 'https://localhost/test'
                }
                
                # Thử tạo payment link để test
                resp = service.create_payment_link(test_data)
                
                # Nếu thành công, cập nhật trạng thái
                record.write({
                    'last_connection_date': fields.Datetime.now(),
                    'last_connection_status': 'success',
                    'connection_message': f'Kết nối thành công! Order Code: {test_order_code}'
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Thành công'),
                        'message': _('Bạn đã kết nối thành công tới PayOS API!'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                error_msg = str(e)
                record.write({
                    'last_connection_date': fields.Datetime.now(),
                    'last_connection_status': 'failed',
                    'connection_message': f'Lỗi: {error_msg}'
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Thất bại'),
                        'message': _('Không thể kết nối tới PayOS API: %s') % error_msg,
                        'type': 'danger',
                        'sticky': True,
                    }
                }

