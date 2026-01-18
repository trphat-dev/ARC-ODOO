# -*- coding: utf-8 -*-

"""
Wrapper class cho ssi-fctrading library
Giúp quản lý kết nối và các API calls
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .utils import TokenConstants

_logger = logging.getLogger(__name__)


class TradingAPIClient:
    """
    Wrapper class cho FCTradingClient và FCTradingStream
    Quản lý connection, token refresh, error handling
    """
    
    def __init__(self, config):
        """
        Khởi tạo API client từ config
        
        Args:
            config: trading.config record
        """
        self.config = config
        self._client = None
        self._stream = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Khởi tạo FCTradingClient"""
        try:
            from ssi_fctrading import FCTradingClient
            from ssi_fctrading.models import AccessTokenModel, fcmodel_responses
            
            self._client = FCTradingClient(
                url=self.config.api_url,
                consumer_id=self.config.consumer_id,
                consumer_secret=self.config.consumer_secret,
                private_key=self.config.private_key,
                twoFAType=int(self.config.two_fa_type)
            )
            
            # Lưu read token vào config
            self.config.write({
                'read_access_token': self._client.get_access_token(),
            })
            
            # Restore write_access_token nếu có trong config và còn hiệu lực
            if self.config.write_access_token:
                try:
                    from ssi_fctrading.models import AccessTokenModel, fcmodel_responses
                    # Tạo AccessToken object từ token string
                    access_token_obj = fcmodel_responses.AccessToken(accessToken=self.config.write_access_token)
                    # Tạo AccessTokenModel từ AccessToken object
                    token_model = AccessTokenModel(access_token_obj)
                    # Chỉ restore nếu token còn hiệu lực (chưa hết hạn)
                    if not token_model.is_expired():
                        self._client._write_access_token = token_model
                        _logger.info(f'Restored write_access_token from config for: {self.config.name} (token còn hiệu lực)')
                    else:
                        _logger.info(f'Write token trong config đã hết hạn cho: {self.config.name}, cần verify lại OTP')
                        # Clear write token trong config vì đã hết hạn
                        self.config.write({'write_access_token': False})
                except Exception as e:
                    _logger.warning(f'Could not restore write_access_token from config: {e}')
                    # Nếu không restore được, user sẽ phải verify code lại
            
            _logger.info(f'Trading API client initialized for config: {self.config.name}')
        except Exception as e:
            _logger.error(f'Error initializing trading client: {e}')
            raise UserError(_('Không thể khởi tạo API client: %s') % str(e))
    
    def get_access_token(self):
        """Lấy read access token (tự động refresh nếu hết hạn)"""
        try:
            token = self._client.get_access_token()
            self.config.write({'read_access_token': token})
            return token
        except Exception as e:
            _logger.error(f'Error getting access token: {e}')
            raise UserError(_('Không thể lấy access token: %s') % str(e))
    
    def verify_code(self, code):
        """
        Verify OTP code để lấy write token
        
        Args:
            code: OTP code
            
        Returns:
            Write access token
        """
        try:
            # Log twoFAType đang sử dụng (luôn là OTP)
            two_fa_type = int(self.config.two_fa_type)
            _logger.info(f'Verifying code with twoFAType: {two_fa_type} (OTP) for config: {self.config.name}')
            
            # Verify code và lưu vào FCTradingClient internal state
            # FCTradingClient sẽ dùng twoFAType đã được set trong __init__
            token = self._client.verifyCode(code)
            
            # Lưu write token vào config để lưu trữ và tái sử dụng
            # Token sẽ được restore và kiểm tra hết hạn khi khởi tạo client
            # Note: AccessTokenModel không expose expire_at, nên ta lưu token thôi
            # Nhưng quan trọng là _client._write_access_token đã được set bởi verifyCode()
            # Token này có thể dùng cho nhiều giao dịch trong thời gian còn hiệu lực (thường 8 giờ)
            self.config.write({
                'write_access_token': token,
            })
            
            _logger.info(f'Successfully verified code and obtained write token for config: {self.config.name}')
            return token
        except NameError as e:
            # NameError từ FCTradingClient khi verifyCode() thất bại
            error_msg = str(e)
            _logger.error(f'Error verifying code (NameError): {error_msg}')
            
            # Kiểm tra nếu lỗi liên quan đến twoFAType không match
            if 'TwoFactorType' in error_msg or 'twoFAType' in error_msg or 'not matched' in error_msg.lower():
                # Re-raise với thông báo chi tiết hơn
                raise
            elif 'Out of synchronization' in error_msg or 'synchronization' in error_msg.lower():
                raise UserError(_('Mã OTP đã hết hạn hoặc không còn hợp lệ. Vui lòng kiểm tra mã Smart OTP mới trên ứng dụng SSI Iboard Pro và thử lại.'))
            else:
                raise UserError(_('Không thể verify code: %s') % error_msg)
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error verifying code: {error_msg}')
            
            # Kiểm tra nếu lỗi liên quan đến twoFAType không match
            if 'TwoFactorType' in error_msg or 'twoFAType' in error_msg or 'not matched' in error_msg.lower():
                # Re-raise để xử lý ở layer trên với thông báo chi tiết
                raise
            elif 'Out of synchronization' in error_msg or 'synchronization' in error_msg.lower():
                raise UserError(_('Mã OTP đã hết hạn hoặc không còn hợp lệ. Vui lòng kiểm tra mã Smart OTP mới trên ứng dụng SSI Iboard Pro và thử lại.'))
            else:
                raise UserError(_('Không thể verify code: %s') % error_msg)
    
    def ensure_write_token(self, code=None):
        """
        Đảm bảo có write token hiệu lực. Nếu chưa có hoặc đã hết hạn, yêu cầu verify OTP.
        
        Args:
            code: OTP code để verify (nếu cần)
            
        Returns:
            bool: True nếu có token hiệu lực, False nếu cần verify OTP
            
        Raises:
            UserError: Nếu cần verify nhưng không có code
        """
        # Kiểm tra write token có tồn tại và còn hiệu lực không
        if not hasattr(self._client, '_write_access_token') or self._client._write_access_token is None:
            if not code:
                raise UserError(_('Write token chưa được verify. Vui lòng nhập OTP code để verify.'))
            # Verify code để lấy write token
            self.verify_code(code)
            return True
        
        # Kiểm tra token có hết hạn không
        if self._client._write_access_token.is_expired():
            _logger.info(f'Write token đã hết hạn cho config {self.config.name}, cần verify OTP lại')
            # Clear token đã hết hạn
            self._client._write_access_token = None
            self.config.write({'write_access_token': False})
            
            if not code:
                raise UserError(
                    _('Write token đã hết hạn. Vui lòng nhập OTP code để verify lại.\n\n'
                      'Lưu ý: Write token có hiệu lực %s giờ, sau khi verify sẽ tự động dùng cho các giao dịch tiếp theo.') %
                    TokenConstants.WRITE_TOKEN_LIFETIME_HOURS
                )
            # Verify code để lấy write token mới
            self.verify_code(code)
            return True
        
        # Token còn hiệu lực
        _logger.info(f'Write token còn hiệu lực cho config {self.config.name}')
        return True
    
    def get_otp(self):
        """
        Lấy OTP từ SSI (chỉ khi two_fa_type = '1')
        
        API GetOTP là public endpoint, không cần access token.
        OTP sẽ được gửi qua SMS/Email theo cấu hình SSI.
        OTP không có trong response, chỉ có status và message.
        
        Returns:
            dict: Response từ API với format {status, message, data}
        """
        try:
            # Kiểm tra two_fa_type (luôn phải là OTP)
            if self.config.two_fa_type != '1':
                raise UserError(_('Two Factor Type phải là OTP (SMS/Email).'))
            
            # Validate consumer_id và consumer_secret
            if not self.config.consumer_id or not self.config.consumer_secret:
                raise UserError(_('Consumer ID và Consumer Secret không được để trống'))
            
            from ssi_fctrading.models import fcmodel_requests
            
            # Tạo request với consumerID và consumerSecret
            req = fcmodel_requests.GetOTP(
                consumerID=str(self.config.consumer_id).strip(),
                consumerSecret=str(self.config.consumer_secret).strip()
            )
            
            # Gọi API GetOTP (public endpoint, không cần access token)
            result = self._client.get_otp(req)
            
            # Log response để debug
            _logger.info(f'GetOTP response for config {self.config.name}: {result}')
            
            # Kiểm tra response
            if isinstance(result, dict):
                status = result.get('status', 0)
                message = result.get('message', '')
                
                # Kiểm tra status
                if status == 200:
                    _logger.info(f'OTP sent successfully for config: {self.config.name}')
                    # OTP đã được gửi qua SMS/Email, không có trong response
                    return result
                else:
                    # Lỗi từ API
                    error_msg = message or f'API returned status {status}'
                    _logger.error(f'GetOTP failed: status={status}, message={message}')
                    raise UserError(_('Không thể lấy OTP: %s\n\nVui lòng kiểm tra:\n1. Consumer ID và Consumer Secret có đúng không\n2. Tài khoản đã được đăng ký với SSI FastConnect chưa\n3. Two Factor Type đã được cấu hình đúng với SSI chưa') % error_msg)
            else:
                # Response không phải dict
                _logger.warning(f'GetOTP returned unexpected format: {type(result)}')
                return result
            
        except UserError:
            # Re-raise UserError để giữ nguyên thông báo
            raise
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error getting OTP: {error_msg}')
            raise UserError(_('Không thể lấy OTP: %s\n\nVui lòng kiểm tra:\n1. Consumer ID và Consumer Secret có đúng không\n2. Tài khoản đã được đăng ký với SSI FastConnect chưa\n3. Kết nối mạng có ổn định không') % error_msg)
    
    def get_deviceid(self):
        """
        Lấy deviceId từ FCTradingClient và format đúng theo yêu cầu API
        FCTradingClient.get_deviceid() trả về: "interface1:MAC1|interface2:MAC2"
        Format yêu cầu API: XX:XX:XX:XX:XX:XX, XX-XX-XX-XX-XX-XX, hoặc XXXXXXXXXXXX
        """
        try:
            from ssi_fctrading import FCTradingClient
            import re
            
            device_id_raw = FCTradingClient.get_deviceid()
            
            # Nếu deviceId rỗng, trả về giá trị mặc định
            if not device_id_raw or device_id_raw.strip() == '':
                _logger.warning('Device ID is empty, using default')
                return '00:00:00:00:00:00'
            
            # FCTradingClient.get_deviceid() trả về: "interface:MAC" hoặc "interface1:MAC1|interface2:MAC2"
            # Cần extract MAC address từ format này
            
            # Nếu có nhiều interface (có dấu |), lấy MAC đầu tiên
            if '|' in device_id_raw:
                device_id_raw = device_id_raw.split('|')[0]
            
            # Extract MAC address (phần sau dấu :)
            # Format: "interface:MAC" -> cần lấy phần MAC
            # Có thể là "eth0:AA:BB:CC:DD:EE:FF" hoặc "Wi-Fi:AA-BB-CC-DD-EE-FF"
            if ':' in device_id_raw:
                parts = device_id_raw.split(':')
                # Nếu có nhiều dấu :, format là "interface:AA:BB:CC:DD:EE:FF"
                if len(parts) >= 7:
                    # Lấy 6 phần cuối là MAC address
                    mac_address = ':'.join(parts[-6:])
                elif len(parts) >= 2:
                    # Format: "interface:MAC" -> lấy phần MAC
                    mac_address = parts[-1]
                else:
                    _logger.warning(f'Invalid device ID format: {device_id_raw}, using default')
                    return '00:00:00:00:00:00'
            else:
                # Không có dấu :, có thể là MAC address thuần
                mac_address = device_id_raw
            
            # Clean MAC address: loại bỏ tất cả ký tự không phải hex
            mac_clean = re.sub(r'[^0-9A-Fa-f]', '', mac_address.upper())
            
            # Validate: MAC address phải có 12 ký tự hex
            if len(mac_clean) != 12:
                _logger.warning(f'Invalid MAC address length: {len(mac_clean)} (expected 12), using default')
                return '00:00:00:00:00:00'
            
            # Format thành XX:XX:XX:XX:XX:XX (chuẩn API yêu cầu)
            device_id = ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
            
            _logger.info(f'Formatted device ID: {device_id} (from raw: {device_id_raw})')
            return device_id
        except Exception as e:
            _logger.error(f'Error getting deviceId: {e}')
            # Fallback: trả về giá trị mặc định đúng format
            return '00:00:00:00:00:00'
    
    def get_user_agent(self):
        """Lấy user agent từ FCTradingClient"""
        try:
            from ssi_fctrading import FCTradingClient
            return FCTradingClient.get_user_agent()
        except Exception as e:
            _logger.error(f'Error getting user agent: {e}')
            # Fallback: trả về giá trị mặc định
            return 'Odoo/18.0'
    
    # ========== ORDER MANAGEMENT ==========
    
    def new_order(self, order_data):
        """Đặt lệnh mới (Stock)"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.NewOrder(**order_data)
            result = self._client.new_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error placing new order: {e}')
            raise UserError(_('Không thể đặt lệnh: %s') % str(e))
    
    def modify_order(self, order_data):
        """Sửa lệnh (Stock)"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.ModifyOrder(**order_data)
            result = self._client.modify_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error modifying order: {e}')
            raise UserError(_('Không thể sửa lệnh: %s') % str(e))
    
    def cancel_order(self, order_data):
        """Hủy lệnh (Stock)"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.CancelOrder(**order_data)
            result = self._client.cancle_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error canceling order: {e}')
            raise UserError(_('Không thể hủy lệnh: %s') % str(e))
    
    def der_new_order(self, order_data):
        """Đặt lệnh phái sinh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.NewOrder(**order_data)
            result = self._client.der_new_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error placing derivative order: {e}')
            raise UserError(_('Không thể đặt lệnh phái sinh: %s') % str(e))
    
    def der_modify_order(self, order_data):
        """Sửa lệnh phái sinh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.ModifyOrder(**order_data)
            result = self._client.der_modify_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error modifying derivative order: {e}')
            raise UserError(_('Không thể sửa lệnh phái sinh: %s') % str(e))
    
    def der_cancel_order(self, order_data):
        """Hủy lệnh phái sinh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.CancelOrder(**order_data)
            result = self._client.der_cancle_order(req)
            return result
        except Exception as e:
            _logger.error(f'Error canceling derivative order: {e}')
            raise UserError(_('Không thể hủy lệnh phái sinh: %s') % str(e))
    
    # ========== ACCOUNT & POSITION ==========
    
    def get_stock_account_balance(self, account):
        """
        Lấy số dư tài khoản chứng khoán
        
        Args:
            account: Account number (đã được clean và format)
        """
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            # Validate account
            if not account:
                raise UserError(_('Account không được để trống'))
            
            # Format account (loại bỏ khoảng trắng, uppercase) để đảm bảo consistency
            account_clean = str(account).strip().upper()
            
            _logger.info(f'Getting stock account balance for account: {account_clean}')
            
            req = fcmodel_requests.StockAccountBalance(account=account_clean)
            result = self._client.get_stock_account_balance(req)
            
            # Kiểm tra response
            if isinstance(result, dict):
                status = result.get('status', 0)
                message = result.get('message', '')
                
                if status == 400 and 'not exist' in message.lower():
                    raise UserError(_('Account không tồn tại trên hệ thống SSI.\n\nVui lòng kiểm tra:\n1. Account number có đúng không\n2. Account có được đăng ký với SSI FastConnect không\n3. Config API có đúng với tài khoản này không'))
                elif status != 200:
                    _logger.warning(f'API returned non-200 status: {status}, message: {message}')
            
            return result
        except UserError:
            # Re-raise UserError để giữ nguyên thông báo
            raise
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error getting stock account balance: {error_msg}')
            
            # Kiểm tra nếu lỗi liên quan đến account không tồn tại
            if 'not exist' in error_msg.lower() or 'not found' in error_msg.lower():
                raise UserError(_('Account không tồn tại trên hệ thống SSI.\n\nVui lòng kiểm tra:\n1. Account number có đúng không\n2. Account có được đăng ký với SSI FastConnect không\n3. Config API có đúng với tài khoản này không'))
            else:
                raise UserError(_('Không thể lấy số dư tài khoản: %s') % error_msg)
    
    def get_derivative_account_balance(self, account):
        """Lấy số dư tài khoản phái sinh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            # Chuẩn hoá account
            if not account:
                raise UserError(_('Account không được để trống'))
            account_clean = str(account).strip().upper()
            
            req = fcmodel_requests.DerivativeAccountBalance(account=account_clean)
            result = self._client.get_derivative_account_balance(req)
            
            # Kiểm tra response tương tự stock
            if isinstance(result, dict):
                status = result.get('status', 0)
                message = result.get('message', '')
                if status == 400 and 'not exist' in message.lower():
                    raise UserError(_('Account không tồn tại trên hệ thống SSI.'))
                elif status != 200 and status != 0:
                    _logger.warning(f'Derivative balance non-200: {status}, message: {message}')
            return result
        except Exception as e:
            _logger.error(f'Error getting derivative account balance: {e}')
            raise UserError(_('Không thể lấy số dư phái sinh: %s') % str(e))
    
    def get_stock_position(self, account):
        """Lấy vị thế chứng khoán"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.StockPosition(account=account)
            result = self._client.get_stock_position(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting stock position: {e}')
            raise UserError(_('Không thể lấy vị thế chứng khoán: %s') % str(e))
    
    def get_derivative_position(self, account, query_summary=True):
        """Lấy vị thế phái sinh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.DerivativePosition(account=account, querySummary=query_summary)
            result = self._client.get_derivative_position(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting derivative position: {e}')
            raise UserError(_('Không thể lấy vị thế phái sinh: %s') % str(e))
    
    def get_max_buy_qty(self, account, instrument_id, price):
        """Lấy khối lượng mua tối đa"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.MaxBuyQty(account=account, instrumentID=instrument_id, price=price)
            result = self._client.get_max_buy_qty(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting max buy qty: {e}')
            raise UserError(_('Không thể lấy khối lượng mua tối đa: %s') % str(e))
    
    def get_max_sell_qty(self, account, instrument_id, price='0'):
        """Lấy khối lượng bán tối đa"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.MaxSellQty(account=account, instrumentID=instrument_id, price=price)
            result = self._client.get_max_sell_qty(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting max sell qty: {e}')
            raise UserError(_('Không thể lấy khối lượng bán tối đa: %s') % str(e))
    
    # ========== ORDER INFO ==========
    
    def get_order_history(self, account, start_date, end_date):
        """Lấy lịch sử lệnh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.OrderHistory(account=account, startDate=start_date, endDate=end_date)
            result = self._client.get_order_history(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting order history: {e}')
            raise UserError(_('Không thể lấy lịch sử lệnh: %s') % str(e))
    
    def get_order_book(self, account):
        """Lấy sổ lệnh"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.OrderBook(account=account)
            result = self._client.get_order_book(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting order book: {e}')
            raise UserError(_('Không thể lấy sổ lệnh: %s') % str(e))
    
    def get_audit_order_book(self, account):
        """Lấy sổ lệnh kèm lỗi"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.AuditOrderBook(account=account)
            result = self._client.get_audit_order_book(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting audit order book: {e}')
            raise UserError(_('Không thể lấy audit order book: %s') % str(e))
    
    def get_rate_limit(self):
        """Lấy rate limit"""
        try:
            result = self._client.get_ratelimit()
            return result
        except Exception as e:
            _logger.error(f'Error getting rate limit: {e}')
            raise UserError(_('Không thể lấy rate limit: %s') % str(e))
    
    # ========== CASH MANAGEMENT ==========
    
    def get_cash_cia_amount(self, account):
        """Lấy số tiền ứng trước"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.CashInAdvanceAmount(account=account)
            result = self._client.get_cash_cia_amount(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting cash CIA amount: {e}')
            raise UserError(_('Không thể lấy số tiền ứng trước: %s') % str(e))
    
    def get_cash_transfer_history(self, account, from_date, to_date):
        """Lấy lịch sử chuyển tiền"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.CashTransferHistory(account=account, fromDate=from_date, toDate=to_date)
            result = self._client.get_cash_transfer_history(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting cash transfer history: {e}')
            raise UserError(_('Không thể lấy lịch sử chuyển tiền: %s') % str(e))
    
    def create_cash_transfer(self, transfer_data):
        """Tạo chuyển tiền nội bộ"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.CashTransfer(**transfer_data)
            result = self._client.create_cash_transfer(req)
            return result
        except Exception as e:
            _logger.error(f'Error creating cash transfer: {e}')
            raise UserError(_('Không thể tạo chuyển tiền: %s') % str(e))
    
    # ========== ONLINE RIGHT SUBSCRIPTION ==========
    
    def get_ors_dividend(self, account):
        """Lấy cổ tức ORS"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.OrsDividend(account=account)
            result = self._client.get_ors_dividend(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting ORS dividend: {e}')
            raise UserError(_('Không thể lấy cổ tức ORS: %s') % str(e))
    
    def create_ors(self, ors_data):
        """Tạo đăng ký quyền mua"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.Ors(**ors_data)
            result = self._client.create_ors(req)
            return result
        except Exception as e:
            _logger.error(f'Error creating ORS: {e}')
            raise UserError(_('Không thể tạo đăng ký quyền mua: %s') % str(e))
    
    # ========== STOCK TRANSFER ==========
    
    def get_stock_transferable(self, account):
        """Lấy cổ phiếu có thể chuyển"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.StockTransferable(account=account)
            result = self._client.get_stock_transferable(req)
            return result
        except Exception as e:
            _logger.error(f'Error getting stock transferable: {e}')
            raise UserError(_('Không thể lấy cổ phiếu có thể chuyển: %s') % str(e))
    
    def create_stock_transfer(self, transfer_data):
        """Tạo chuyển khoản cổ phiếu"""
        try:
            from ssi_fctrading.models import fcmodel_requests
            
            req = fcmodel_requests.StockTransfer(**transfer_data)
            result = self._client.create_stock_transfer(req)
            return result
        except Exception as e:
            _logger.error(f'Error creating stock transfer: {e}')
            raise UserError(_('Không thể tạo chuyển khoản cổ phiếu: %s') % str(e))

