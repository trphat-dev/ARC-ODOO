import logging
import pytz
from odoo import models, fields, api
from odoo.http import request
from odoo.addons.custom_auth.constants import (
    PERMISSION_SYSTEM_ADMIN,
    PERMISSION_FUND_OPERATOR,
    PERMISSION_INVESTOR_USER,
    get_redirect_url
)

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    def _get_login_redirect_url(self):
        """Override để xác định URL điều hướng sau khi đăng nhập"""
        self.ensure_one()
        
        if self.has_group('base.group_portal'):
            return get_redirect_url(PERMISSION_INVESTOR_USER)
        elif self.has_group('base.group_user'):
            return get_redirect_url(PERMISSION_FUND_OPERATOR)
        else:
            return '/web'
    
    @api.model
    def _auth_redirect_after_login(self, user_id):
        """Xử lý điều hướng sau khi đăng nhập"""
        user = self.browse(user_id)
        return user._get_login_redirect_url()

    @api.model
    def _compute_tz_offset(self):
        """
        Override method _compute_tz_offset để xử lý timezone an toàn
        """
        for user in self:
            try:
                # Sửa timezone Asia/Saigon thành Asia/Ho_Chi_Minh
                user_tz = user.tz or 'GMT'
                if user_tz == 'Asia/Saigon':
                    user_tz = 'Asia/Ho_Chi_Minh'
                    # Cập nhật timezone trong database
                    user.write({'tz': 'Asia/Ho_Chi_Minh'})
                
                # Validate timezone
                try:
                    tz = pytz.timezone(user_tz)
                    user.tz_offset = pytz.datetime.datetime.now(tz).strftime('%z')
                except pytz.exceptions.UnknownTimeZoneError:
                    # Fallback về timezone mặc định
                    tz = pytz.timezone('Asia/Ho_Chi_Minh')
                    user.tz_offset = pytz.datetime.datetime.now(tz).strftime('%z')
                    # Cập nhật timezone trong database
                    user.write({'tz': 'Asia/Ho_Chi_Minh'})
                    
            except Exception as e:
                _logger.error(f"Lỗi khi tính toán timezone offset cho user {user.id}: {str(e)}")
                # Fallback về GMT
                user.tz_offset = '+0000'

    @api.model
    def fix_invalid_timezones(self):
        """
        Sửa các timezone không hợp lệ trong database
        Chuyển đổi Asia/Saigon thành Asia/Ho_Chi_Minh
        """
        try:
            # Tìm tất cả users có timezone Asia/Saigon
            users_with_saigon_tz = self.search([
                ('tz', '=', 'Asia/Saigon')
            ])
            
            if users_with_saigon_tz:
                # Cập nhật timezone thành Asia/Ho_Chi_Minh
                users_with_saigon_tz.write({'tz': 'Asia/Ho_Chi_Minh'})
                _logger.info(f"Đã sửa timezone cho {len(users_with_saigon_tz)} users từ Asia/Saigon thành Asia/Ho_Chi_Minh")
            
            # Kiểm tra và sửa các timezone không hợp lệ khác
            all_users = self.search([])
            invalid_tz_users = []
            
            for user in all_users:
                if user.tz:
                    try:
                        pytz.timezone(user.tz)
                    except pytz.exceptions.UnknownTimeZoneError:
                        invalid_tz_users.append(user)
            
            if invalid_tz_users:
                # Sửa tất cả timezone không hợp lệ thành Asia/Ho_Chi_Minh
                for user in invalid_tz_users:
                    user.write({'tz': 'Asia/Ho_Chi_Minh'})
                _logger.info(f"Đã sửa timezone cho {len(invalid_tz_users)} users có timezone không hợp lệ")
                
        except Exception as e:
            _logger.error(f"Lỗi khi sửa timezone: {str(e)}")
            raise 