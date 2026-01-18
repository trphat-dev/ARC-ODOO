# -*- coding: utf-8 -*-

import json
import logging
import random

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..utils import TokenConstants

_logger = logging.getLogger(__name__)


class TradingOrderModifyWizard(models.TransientModel):
    """Wizard để modify order"""
    _name = 'trading.order.modify.wizard'
    _description = 'Trading Order Modify Wizard'

    order_id = fields.Many2one(
        'trading.order',
        string='Order',
        required=True,
        readonly=True
    )
    
    quantity = fields.Integer(
        string='New Quantity',
        required=True,
        help='Khối lượng mới'
    )
    
    code = fields.Char(
        string='OTP Code',
        help='OTP code để verify và lấy write token (nếu chưa có write token)'
    )

    def action_modify_order(self):
        """Modify order via API"""
        self.ensure_one()
        order = self.order_id
        
        if not order.api_order_id:
            raise UserError(_('Không có Order ID để sửa'))
        
        try:
            client = order.config_id.get_api_client()
            
            # Đảm bảo có write token hiệu lực
            # Nếu token còn hiệu lực, sẽ tự động dùng lại (không cần verify OTP)
            try:
                client.ensure_write_token(code=self.code if self.code else None)
                # Xóa code sau khi verify thành công (nếu có)
                if self.code:
                    self.code = False
                    # Invalidate computed field để cập nhật UI
                    order.invalidate_recordset(['has_valid_write_token'])
                    order.config_id.invalidate_recordset(['write_access_token'])
            except UserError as ue:
                # Nếu không có code, hiển thị thông báo hướng dẫn
                if not self.code:
                    raise UserError(
                        _('Write token đã hết hạn hoặc chưa được verify.\n\n'
                          'Vui lòng:\n'
                          '1. Nhập OTP code vào trường "OTP Code"\n'
                          '2. Click "Modify Order"\n\n'
                          'Lưu ý: Write token có hiệu lực %s giờ, sau khi verify sẽ tự động dùng cho các giao dịch tiếp theo mà không cần nhập OTP code nữa.') %
                        TokenConstants.WRITE_TOKEN_LIFETIME_HOURS
                    )
                else:
                    # Re-raise nếu có code nhưng verify thất bại
                    raise
            
            # Generate deviceId và userAgent nếu chưa có
            device_id = order.device_id or client.get_deviceid()
            user_agent = order.user_agent or client.get_user_agent()
            if not order.device_id:
                order.device_id = device_id
            if not order.user_agent:
                order.user_agent = user_agent
            
            # Validate account
            if not order.account:
                raise UserError(_('Order không có Account'))
            
            account_clean = str(order.account).strip().upper()
            if not account_clean:
                raise UserError(_('Account không được để trống'))
            
            # Lấy giá đặt lệnh (luôn = 0 theo yêu cầu API)
            # Lấy giá đặt lệnh từ order gốc
            modify_price = order._get_order_price()
            
            # Prepare modify data theo chuẩn fc-trading
            # Format: account, requestID, orderID, marketID, instrumentID, price, quantity, buySell, orderType
            modify_data = {
                'account': account_clean,
                'requestID': str(random.randint(0, 99999999)),
                'orderID': str(order.api_order_id),
                'marketID': str(order.market).strip().upper(),
                'instrumentID': str(order.instrument_code).strip().upper(),
                'price': modify_price,
                'quantity': int(self.quantity),
                'buySell': str(order.buy_sell).strip().upper(),
                'orderType': str(order.order_type_detail).strip().upper(),
                'deviceId': str(device_id),
                'userAgent': str(user_agent),
            }
            
            if order.order_type == 'stock':
                result = client.modify_order(modify_data)
            else:
                result = client.der_modify_order(modify_data)
            
            # Update order
            order.write({
                'quantity': self.quantity,
                'request_id': modify_data['requestID'],
                'api_response': json.dumps(result, indent=2),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Đã sửa lệnh thành công'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f'Error modifying order: {e}')
            raise UserError(_('Không thể sửa lệnh: %s') % str(e))

