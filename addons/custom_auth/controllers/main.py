import json
import random
import string
import logging
import re

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.addons.custom_auth.constants import PERMISSION_INVESTOR_USER
from odoo.addons.arc_core.utils.rate_limiter import rate_limit_strict
import werkzeug

_logger = logging.getLogger(__name__)


class CustomAuthController(AuthSignupHome):
    
    def _validate_password(self, password):
        """
        Validate password requirements:
        - Tối thiểu 8 ký tự
        - Ít nhất 1 chữ hoa
        - Ít nhất 1 chữ số
        - Ít nhất 1 ký tự đặc biệt
        """
        if not password or len(password) < 8:
            return False, 'Mật khẩu phải có ít nhất 8 ký tự.'
        if not re.search(r'[A-Z]', password):
            return False, 'Mật khẩu phải có ít nhất 1 chữ in hoa.'
        if not re.search(r'[0-9]', password):
            return False, 'Mật khẩu phải có ít nhất 1 chữ số.'
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
            return False, 'Mật khẩu phải có ít nhất 1 ký tự đặc biệt (!@#$%^&*...).'
        return True, ''
    
    @http.route('/web/signup/otp', type='json', auth='public', methods=['POST'])
    @rate_limit_strict(max_calls=5, period=60)
    def send_otp(self, **post):
        """Gửi mã OTP qua SMS"""
        try:
            phone = post.get('phone', '').strip()
            email = post.get('email', '').strip()
            password = post.get('password', '')
            
            # 1. Validate Phone: đúng 10 số
            if not phone:
                return {'success': False, 'message': 'Vui lòng nhập số điện thoại.'}
            phone_digits = re.sub(r'[^0-9]', '', phone)
            if len(phone_digits) != 10:
                return {'success': False, 'message': 'Số điện thoại phải có đúng 10 chữ số.'}
            
            # 2. Check phone trùng trong res.partner
            existing_phone = request.env['res.partner'].sudo().search_count([
                ('phone', '=', phone)
            ])
            if existing_phone:
                return {'success': False, 'message': 'Số điện thoại này đã được sử dụng bởi tài khoản khác.'}
            
            # 3. Validate Email format
            if not email:
                return {'success': False, 'message': 'Vui lòng nhập email.'}
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return {'success': False, 'message': 'Email không hợp lệ. Vui lòng nhập đúng định dạng email.'}
            
            # 4. Check email trùng trong res.users
            existing_email = request.env['res.users'].sudo().search_count([
                ('login', '=', email)
            ])
            if existing_email:
                return {'success': False, 'message': 'Email này đã được sử dụng bởi tài khoản khác.'}
            
            # 5. Validate Password
            is_valid_password, password_error = self._validate_password(password)
            if not is_valid_password:
                return {'success': False, 'message': password_error}
            
            # Tạo mã OTP 6 số
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Lưu OTP vào session
            request.session['signup_otp'] = otp
            request.session['signup_phone'] = phone
            request.session['signup_data'] = post
            
            _logger.info("Generated OTP for phone %s", phone)
            
            return {
                'success': True, 
                'message': 'Mã OTP đã được gửi đến số điện thoại của bạn',
                'phone': phone
            }
            
        except Exception as e:
            _logger.error("Error sending OTP: %s", str(e), exc_info=True)
            return {'success': False, 'message': 'Có lỗi xảy ra khi gửi OTP.'}

    @http.route('/web/signup/direct', type='json', auth='public', methods=['POST'])
    @rate_limit_strict(max_calls=5, period=60)
    def signup_direct(self, **post):
        """Create account directly without OTP verification"""
        try:
            phone = post.get('phone', '').strip()
            email = post.get('email', '').strip()
            password = post.get('password', '')
            name = post.get('name', '').strip()

            # 1. Validate Name
            if not name or len(name) < 2:
                return {'success': False, 'message': 'Vui lòng nhập họ và tên (ít nhất 2 ký tự).'}

            # 2. Validate Phone
            if not phone:
                return {'success': False, 'message': 'Vui lòng nhập số điện thoại.'}
            phone_digits = re.sub(r'[^0-9]', '', phone)
            if len(phone_digits) != 10:
                return {'success': False, 'message': 'Số điện thoại phải có đúng 10 chữ số.'}

            # 3. Check phone duplicate
            existing_phone = request.env['res.partner'].sudo().search_count([
                ('phone', '=', phone)
            ])
            if existing_phone:
                return {'success': False, 'message': 'Số điện thoại này đã được sử dụng bởi tài khoản khác.'}

            # 4. Validate Email
            if not email:
                return {'success': False, 'message': 'Vui lòng nhập email.'}
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return {'success': False, 'message': 'Email không hợp lệ.'}

            # 5. Check email duplicate
            existing_email = request.env['res.users'].sudo().search_count([
                ('login', '=', email)
            ])
            if existing_email:
                return {'success': False, 'message': 'Email này đã được sử dụng bởi tài khoản khác.'}

            # 6. Validate Password
            is_valid_password, password_error = self._validate_password(password)
            if not is_valid_password:
                return {'success': False, 'message': password_error}

            # 7. Create user directly
            user = self._create_user_from_data(post)

            return {
                'success': True,
                'message': 'Đăng ký thành công! Bạn sẽ được chuyển hướng đến trang đăng nhập.',
                'redirect_url': '/web/login'
            }

        except UserError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            _logger.error("Error during direct signup: %s", str(e), exc_info=True)
            return {'success': False, 'message': 'Đã xảy ra lỗi. Vui lòng thử lại.'}

    
    @http.route('/web/signup/verify-otp', type='json', auth='public', methods=['POST'])
    @rate_limit_strict(max_calls=10, period=60)
    def verify_otp(self, **post):
        """Xác thực mã OTP và tạo tài khoản"""
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return {'success': False, 'message': _('Không có dữ liệu đăng ký trong phiên. Vui lòng thử lại.')}

        try:
            otp = post.get('otp')
            
            if not otp or len(otp) != 6:
                return {'success': False, 'message': 'Vui lòng nhập đủ 6 số OTP'}
            
            # Verify OTP against stored value
            stored_otp = request.session.get('signup_otp')
            if not stored_otp or otp != stored_otp:
                return {'success': False, 'message': _('Mã OTP không đúng hoặc đã hết hạn.')}
            
            # Create user
            user = self._create_user_from_data(signup_data)
            
            # Clean session
            request.session.pop('signup_otp', None)
            request.session.pop('signup_phone', None)
            request.session.pop('signup_data', None)
            
            return {
                'success': True, 
                'message': 'Đăng ký thành công! Bạn sẽ được chuyển hướng đến trang đăng nhập.',
                'redirect_url': '/web/login'
            }
            
        except UserError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            _logger.error("Error during OTP verification/signup: %s", str(e), exc_info=True)
            return {'success': False, 'message': _('Đã xảy ra lỗi không mong muốn. Vui lòng liên hệ quản trị viên.')}

    def _create_user_from_data(self, data):
        """Tạo người dùng từ dữ liệu đăng ký. Raises UserError on failure."""
        if not all(data.get(key) for key in ['email', 'password', 'name', 'phone']):
             raise UserError(_("Vui lòng điền đầy đủ thông tin: Tên, Email, Điện thoại và Mật khẩu."))

        if request.env['res.users'].sudo().search_count([('login', '=', data.get('email'))]):
            raise UserError(_("Một người dùng khác đã được đăng ký với địa chỉ email này."))

        user_values = {
            'name': data.get('name'),
            'login': data.get('email'),
            'email': data.get('email'),
            'password': data.get('password'),
            'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
        }
        
        try:
            user = request.env['res.users'].with_context(no_reset_password=True).sudo().create(user_values)
            user.partner_id.sudo().write({'phone': data.get('phone')})
            
            # Create user.permission.management record for proper permission tracking
            self._create_permission_management(user, data)
            
            _logger.info("Successfully created new portal user: %s (ID: %s)", user.login, user.id)
            return user
        except Exception as e:
            _logger.error("Failed to create user for login %s: %s", data.get('email'), str(e), exc_info=True)
            raise UserError(_("Không thể tạo người dùng mới. Vui lòng liên hệ quản trị viên."))
    
    def _create_permission_management(self, user, data):
        """
        Tạo record user.permission.management cho user mới đăng ký.
        Mặc định là investor_user cho users đăng ký qua signup form.
        """
        try:
            permission_mgmt = request.env['user.permission.management'].sudo().create({
                'user_id': user.id,
                'login': user.login,
                'email': user.email,
                'phone': data.get('phone', ''),
                'permission_type': PERMISSION_INVESTOR_USER,
                'is_market_maker': False,
                'active': True,
            })
            _logger.info("Created permission management record for user %s: %s", 
                        user.login, permission_mgmt.id)
        except Exception as e:
            _logger.warning("Failed to create permission management for user %s: %s", 
                          user.login, str(e))
    
    def _send_sms_otp(self, phone, otp):
        """Gửi SMS OTP (cần implement)"""
        # Implement gửi SMS OTP ở đây
        # Có thể sử dụng các dịch vụ SMS như Twilio, Nexmo, etc.
        pass
    
    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        """
        Override password reset to redirect to login page with success message
        after password is successfully changed (instead of auto-login).
        """
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    # Validate password match
                    if qcontext.get('password') != qcontext.get('confirm_password'):
                        qcontext['error'] = _("Mật khẩu không khớp. Vui lòng nhập lại.")
                    else:
                        # Change the password using signup mechanism
                        self.do_signup(qcontext)
                        # Logout user if they were auto-logged in by do_signup
                        request.session.logout(keep_db=True)
                        # Redirect to login with success message
                        return request.redirect('/web/login?message=password_reset_success')
                else:
                    # Request password reset email
                    login = qcontext.get('login')
                    if not login:
                        qcontext['error'] = _("Vui lòng nhập email.")
                    else:
                        _logger.info(
                            "Password reset attempt for <%s> by user <%s> from %s",
                            login, request.env.user.login, request.httprequest.remote_addr)
                        request.env['res.users'].sudo().reset_password(login)
                        qcontext['message'] = _("Hướng dẫn đặt lại mật khẩu đã được gửi đến email của bạn")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except Exception as e:
                qcontext['error'] = _('An unexpected error occurred. Please try again.')
                _logger.exception('error when resetting password')

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response