from odoo import http
from odoo.http import request, Response
import json
import requests
from odoo import http
from odoo.http import request
import base64
import os
from datetime import datetime
import re
from odoo.tools import config as odoo_config
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access


class PersonalProfileController(http.Controller):



    @http.route('/personal_profile', type='http', auth='user', website=True)
    @require_module_access('investor_profile_management')
    def personal_profile_page(self, **kwargs):
        """Route để hiển thị trang personal profile widget"""
        return request.render('investor_profile_management.personal_profile_page')

    @http.route('/bank_info', type='http', auth='user', website=True)
    @require_module_access('investor_profile_management')
    def bank_info_page(self, **kwargs):
        """Route to display the bank information widget page"""
        return request.render('investor_profile_management.bank_info_page')

    @http.route('/address_info', type='http', auth='user', website=True)
    @require_module_access('investor_profile_management')
    def address_info_page(self, **kwargs):
        """Route to display the address information widget page"""
        return request.render('investor_profile_management.address_info_page')

    @http.route('/verification', type='http', auth='user', website=True)
    @require_module_access('investor_profile_management')
    def verification_page(self, **kwargs):
        """Route to display the verification completion widget page"""
        return request.render('investor_profile_management.verification_page')

    @http.route('/get_countries', type='http', auth='user', methods=['GET'], csrf=False)
    def get_countries(self, **kwargs):
        """API endpoint để lấy danh sách quốc gia"""
        try:
            countries = request.env['res.country'].sudo().search([])
            data = []
            for country in countries:
                data.append({
                    'id': country.id,
                    'name': country.name
                })
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/get_currencies', type='http', auth='user', methods=['GET'], csrf=False)
    def get_currencies(self, **kwargs):
        """API endpoint để lấy danh sách tiền tệ"""
        try:
            currencies = request.env['res.currency'].sudo().search([])
            data = []
            for currency in currencies:
                data.append({
                    'id': currency.id,
                    'name': currency.name,
                    'symbol': currency.symbol
                })
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/get_status_info', type='http', auth='user', methods=['GET'], csrf=False)
    def get_status_info(self, **kwargs):
        """API endpoint để lấy dữ liệu status info của user hiện tại"""
        try:
            current_user = request.env.user
            status_infos = request.env['status.info'].sudo().search([
                ('partner_id', '=', current_user.partner_id.id)
            ])
            
            data = []
            for status_info in status_infos:
                # Lấy thông tin tài khoản chứng khoán
                trading_config = request.env['trading.config'].sudo().search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                securities_account = trading_config.account if trading_config else ''

                data.append({
                    'id': status_info.id,
                    'account_number': status_info.account_number or '',
                    'securities_account': securities_account, # Add securities account to response
                    'referral_code': status_info.referral_code or '',
                    'account_status': status_info.account_status or '',
                    'profile_status': status_info.profile_status or '',
                    'ekyc_verified': status_info.ekyc_verified or False,
                })
            
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/data_personal_profile', type='http', auth='user', methods=['GET'], csrf=False)
    def get_personal_profile_data(self, **kwargs):
        """API endpoint để lấy dữ liệu personal profile của user hiện tại"""
        try:
            # Lấy dữ liệu từ model investor.profile của user hiện tại
            current_user = request.env.user
            personal_profiles = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            
            data = []
            if personal_profiles:
                # Nếu có profile, trả về dữ liệu profile
                for profile in personal_profiles:
                    id_front_url = ''
                    id_back_url = ''
                    
                    if profile.id_front:
                        id_front_url = f"/web/image?model=investor.profile&field=id_front&id={profile.id}"

                    if profile.id_back:
                        id_back_url = f"/web/image?model=investor.profile&field=id_back&id={profile.id}"
                    data.append({
                        'id': profile.id,
                        'name': profile.name or '',
                        'email': profile.email or '',
                        'phone': profile.phone or '',
                        'birth_date': profile.birth_date.strftime('%Y-%m-%d') if profile.birth_date else '',
                        'gender': profile.gender or '',
                        'nationality': profile.nationality.id if profile.nationality else '',
                        'id_type': profile.id_type or '',
                        'id_number': profile.id_number or '',
                        'id_issue_date': profile.id_issue_date.strftime('%Y-%m-%d') if profile.id_issue_date else '',
                        'id_issue_place': profile.id_issue_place or '',
                        'id_front': id_front_url,
                        'id_back': id_back_url,
                    })
            else:
                # Nếu chưa có profile, trả về thông tin từ user hiện tại
                partner = current_user.partner_id
                data.append({
                    'id': None,
                    'name': partner.name or current_user.name or '',
                    'email': partner.email or current_user.email or '',
                    'phone': partner.phone or partner.mobile or '',
                    'birth_date': '',
                    'gender': '',
                    'nationality': '',
                    'id_type': '',
                    'id_number': '',
                    'id_issue_date': '',
                    'id_issue_place': '',
                    'id_front': '',
                    'id_back': '',
                })
            
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/save_personal_profile', type='http', auth='user', methods=['POST'], csrf=False)
    def save_personal_profile_data(self, **kwargs):
        """API endpoint để lưu dữ liệu personal profile"""
        try:
            current_user = request.env.user
            # Parse JSON data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            # Kiểm tra các trường bắt buộc
            required_fields = ['name', 'email', 'phone', 'gender', 'nationality', 'birth_date', 'id_type', 'id_number', 'id_issue_date', 'id_issue_place']
            missing_fields = [field for field in required_fields if not data.get(field)]
            # Kiểm tra nationality hợp lệ
            nationality_val = data.get('nationality')
            try:
                nationality_id = int(nationality_val) if nationality_val and str(nationality_val).isdigit() else None
            except Exception:
                nationality_id = None
            if not nationality_id:
                missing_fields.append('nationality')
            if missing_fields:
                return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin: {", ".join(set(missing_fields))}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            # Tìm profile hiện tại hoặc tạo mới
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            if not profile:
                # Tạo profile mới với đầy đủ trường required
                create_dict = {
                    'partner_id': current_user.partner_id.id,
                    'name': data['name'],
                    'gender': data['gender'],
                    'birth_date': data['birth_date'],
                    'nationality': nationality_id,
                    'id_type': data['id_type'],
                    'id_number': data['id_number'],
                    'id_issue_date': data['id_issue_date'],
                    'id_issue_place': data['id_issue_place'],
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                }
                
                # Thêm CCCD images nếu có từ eKYC
                if 'frontPreviewBase64' in data and data['frontPreviewBase64']:
                    try:
                        front_base64 = data['frontPreviewBase64']
                        if front_base64.startswith('data:'):
                            front_base64 = front_base64.split(',')[1]
                        import base64
                        front_binary = base64.b64decode(front_base64)
                        create_dict['id_front'] = front_binary
                        # Build filename using login username
                        login = (current_user.login or '').strip().lower()
                        uname = re.sub(r'[^a-z0-9_-]+', '', login.replace('@', '_').replace('.', '_').replace(' ', '_')) or 'user'
                        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                        filename = f"cccd_front_{uname}_{ts}.jpg"
                        create_dict['id_front_filename'] = filename
                        print(f"✅ Front CCCD image binary loaded for new profile ({len(front_binary)} bytes)")
                    except Exception as e:
                        print(f"❌ Error processing front CCCD image for new profile: {e}")
                
                if 'backPreviewBase64' in data and data['backPreviewBase64']:
                    try:
                        back_base64 = data['backPreviewBase64']
                        if back_base64.startswith('data:'):
                            back_base64 = back_base64.split(',')[1]
                        import base64
                        back_binary = base64.b64decode(back_base64)
                        create_dict['id_back'] = back_binary
                        # Build filename using login username
                        login = (current_user.login or '').strip().lower()
                        uname = re.sub(r'[^a-z0-9_-]+', '', login.replace('@', '_').replace('.', '_').replace(' ', '_')) or 'user'
                        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                        filename = f"cccd_back_{uname}_{ts}.jpg"
                        create_dict['id_back_filename'] = filename
                        print(f"✅ Back CCCD image binary loaded for new profile ({len(back_binary)} bytes)")
                    except Exception as e:
                        print(f"❌ Error processing back CCCD image for new profile: {e}")
                
                profile = request.env['investor.profile'].sudo().create(create_dict)
            # Cập nhật dữ liệu
            update_data = {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'gender': data['gender'],
                'nationality': nationality_id,
                'birth_date': data['birth_date'],
                'id_type': data['id_type'],
                'id_number': data['id_number'],
                'id_issue_date': data['id_issue_date'],
                'id_issue_place': data['id_issue_place'],
            }
            
            # Xử lý CCCD images từ base64 (từ eKYC hoặc upload). Ngoài việc lưu Binary,
            # ta còn lưu ra thư mục static để tạo URL tĩnh phục vụ frontend.
            if 'frontPreviewBase64' in data and data['frontPreviewBase64']:
                try:
                    # Decode base64 thành binary data
                    front_base64 = data['frontPreviewBase64']
                    if front_base64.startswith('data:'):
                        # Remove data URL prefix (data:image/jpeg;base64,)
                        front_base64 = front_base64.split(',')[1]
                    
                    import base64
                    front_binary = base64.b64decode(front_base64)
                    update_data['id_front'] = front_binary
                    # Build filename using login username
                    login = (current_user.login or '').strip().lower()
                    uname = re.sub(r'[^a-z0-9_-]+', '', login.replace('@', '_').replace('.', '_').replace(' ', '_')) or 'user'
                    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                    filename = f"cccd_front_{uname}_{ts}.jpg"
                    update_data['id_front_filename'] = filename
                    print(f"✅ Front CCCD image binary updated to database ({len(front_binary)} bytes)")
                except Exception as e:
                    print(f"❌ Error processing front CCCD image: {e}")
            
            if 'backPreviewBase64' in data and data['backPreviewBase64']:
                try:
                    # Decode base64 thành binary data
                    back_base64 = data['backPreviewBase64']
                    if back_base64.startswith('data:'):
                        # Remove data URL prefix (data:image/jpeg;base64,)
                        back_base64 = back_base64.split(',')[1]
                    
                    import base64
                    back_binary = base64.b64decode(back_base64)
                    update_data['id_back'] = back_binary
                    # Build filename using login username
                    login = (current_user.login or '').strip().lower()
                    uname = re.sub(r'[^a-z0-9_-]+', '', login.replace('@', '_').replace('.', '_').replace(' ', '_')) or 'user'
                    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                    filename = f"cccd_back_{uname}_{ts}.jpg"
                    update_data['id_back_filename'] = filename
                    print(f"✅ Back CCCD image binary updated to database ({len(back_binary)} bytes)")
                except Exception as e:
                    print(f"❌ Error processing back CCCD image: {e}")
            
            profile.sudo().write(update_data)
            # Đồng bộ lên contact/customer (res.partner)
            partner_update = {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
            }
            if partner_update:
                profile.partner_id.sudo().write(partner_update)
            return Response(json.dumps({'success': True, 'message': 'Profile updated successfully'}), 
                          content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/upload_id_image', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_id_image(self, **kwargs):
        try:
            current_user = request.env.user
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            if not profile:
                return Response(json.dumps({'error': 'Chưa có hồ sơ cá nhân'}), content_type='application/json', status=400)

            file = request.httprequest.files.get('file')
            side = request.httprequest.form.get('side')
            if not file or side not in ['front', 'back']:
                return Response(json.dumps({'error': 'Thiếu file hoặc side'}), content_type='application/json', status=400)

            file_data = file.read()
            # Build filename using login username
            login = (current_user.login or '').strip().lower()
            uname = re.sub(r'[^a-z0-9_-]+', '', login.replace('@', '_').replace('.', '_').replace(' ', '_')) or 'user'
            ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = f"cccd_{side}_{uname}_{ts}.jpg"
            # Directly save to fields
            if side == 'front':
                profile.sudo().write({'id_front': base64.b64encode(file_data), 'id_front_filename': filename})
            else:
                profile.sudo().write({'id_back': base64.b64encode(file_data), 'id_back_filename': filename})

            return Response(json.dumps({'success': True}), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/data_bank_info', type='http', auth='user', methods=['GET'], csrf=False)
    def get_bank_info_data(self, **kwargs):
        """API endpoint để lấy dữ liệu bank information của user hiện tại"""
        try:
            current_user = request.env.user
            
            # Tìm hoặc tạo investor profile trước
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            
            if not profile:
                # Tạo profile mới nếu chưa có
                profile = request.env['investor.profile'].sudo().create({
                    'partner_id': current_user.partner_id.id,
                })
            
            # Lấy dữ liệu từ model investor.bank.account của user hiện tại
            bank_accounts = request.env['investor.bank.account'].sudo().search([
                ('investor_id', '=', profile.id)
            ])

            data = []
            if bank_accounts:
                # Nếu có bank account, trả về dữ liệu
                for bank_account in bank_accounts:
                    data.append({
                        'id': bank_account.id,
                        'account_holder': bank_account.account_holder or '',
                        'account_number': bank_account.account_number or '',
                        'bank_name': bank_account.bank_name or '',
                        'branch': bank_account.branch or '',
                        'company_name': bank_account.company_name or '',
                        'company_address': bank_account.company_address or '',
                        'monthly_income': bank_account.monthly_income or '',
                        'occupation': bank_account.occupation or '',
                        'position': bank_account.position or ''
                    })
            else:
                # Nếu chưa có bank account, trả về thông tin mặc định
                partner = current_user.partner_id
                data.append({
                    'id': None,
                    'account_holder': partner.name or current_user.name or '',
                    'account_number': '',
                    'bank_name': '',
                    'branch': '',
                    'company_name': '',
                    'company_address': '',
                    'monthly_income': '',
                    'occupation': '',
                    'position': ''
                })

            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/save_bank_info', type='http', auth='user', methods=['POST'], csrf=False)
    def save_bank_info_data(self, **kwargs):
        """API endpoint để lưu dữ liệu bank information"""
        try:
            current_user = request.env.user
            data = json.loads(request.httprequest.data.decode('utf-8'))
            # Kiểm tra các trường bắt buộc
            required_fields = ['account_holder', 'account_number', 'bank_name', 'branch']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin: {", ".join(set(missing_fields))}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            # Tìm hoặc tạo investor profile trước
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            if not profile:
                profile = request.env['investor.profile'].sudo().create({
                    'partner_id': current_user.partner_id.id,
                })
            # Tìm bank account hiện tại hoặc tạo mới
            bank_account = request.env['investor.bank.account'].sudo().search([
                ('investor_id', '=', profile.id)
            ], limit=1)
            if not bank_account:
                # Tạo bank account mới với đầy đủ trường required
                create_dict = {
                    'investor_id': profile.id,
                    'bank_name': data['bank_name'],
                    'account_number': data['account_number'],
                    'account_holder': data['account_holder'],
                    'branch': data['branch'],
                    'company_name': data.get('company_name', ''),
                    'company_address': data.get('company_address', ''),
                    'monthly_income': data.get('monthly_income', 0),
                    'occupation': data.get('occupation', ''),
                    'position': data.get('position', ''),
                }
                bank_account = request.env['investor.bank.account'].sudo().create(create_dict)
            update_data = {
                'account_holder': data['account_holder'],
                'account_number': data['account_number'],
                'bank_name': data['bank_name'],
                'branch': data['branch'],
                'company_name': data.get('company_name', ''),
                'company_address': data.get('company_address', ''),
                'monthly_income': data.get('monthly_income', 0),
                'occupation': data.get('occupation', ''),
                'position': data.get('position', ''),
            }
            bank_account.sudo().write(update_data)
            return Response(json.dumps({'success': True, 'message': 'Bank info updated successfully'}),
                          content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/data_address_info', type='http', auth='user', methods=['GET'], csrf=False)
    def get_address_info_data(self, **kwargs):
        """API endpoint để lấy dữ liệu address information của user hiện tại"""
        try:
            current_user = request.env.user
            
            # Tìm hoặc tạo investor profile trước
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            
            if not profile:
                # Tạo profile mới nếu chưa có
                profile = request.env['investor.profile'].sudo().create({
                    'partner_id': current_user.partner_id.id,
                })
            
            # Lấy dữ liệu từ model investor.address của user hiện tại
            addresses = request.env['investor.address'].sudo().search([
                ('investor_id', '=', profile.id)
            ])

            data = []
            if addresses:
                # Nếu có address, trả về dữ liệu
                for address in addresses:
                    data.append({
                        'id': address.id,
                        'street': address.street or '',
                        'state': address.state_id.id if address.state_id else '',
                        'country_id': address.country_id.id if address.country_id else '',
                        'district': address.district or '',
                        'ward': address.ward or '',
                    })
            else:
                # Nếu chưa có address, trả về thông tin mặc định
                partner = current_user.partner_id
                data.append({
                    'id': None,
                    'street': partner.street or '',
                    'state': partner.state_id.id if partner.state_id else '',
                    'country_id': partner.country_id.id if partner.country_id else '',
                    'district': '',
                    'ward': '',
                })

            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/save_address_info', type='http', auth='user', methods=['POST'], csrf=False)
    def save_address_info_data(self, **kwargs):
        """API endpoint để lưu dữ liệu address information"""
        try:
            current_user = request.env.user
            data = json.loads(request.httprequest.data.decode('utf-8'))
            required_fields = ['street', 'district', 'ward', 'country_id', 'state']
            for field in required_fields:
                if not data.get(field):
                    return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin: {field}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            # Kiểm tra state_id hợp lệ
            state_val = data.get('state')
            try:
                state_id = int(state_val) if state_val and str(state_val).isdigit() else None
            except Exception:
                state_id = None
            if not state_id or state_id <= 0:
                return Response(json.dumps({'error': 'Thiếu hoặc sai thông tin: state. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            # Kiểm tra country_id hợp lệ
            country_val = data.get('country_id')
            try:
                country_id = int(country_val) if country_val and str(country_val).isdigit() else None
            except Exception:
                country_id = None
            if not country_id or country_id <= 0:
                return Response(json.dumps({'error': 'Thiếu hoặc sai thông tin: country_id. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            # Tìm hoặc tạo investor profile trước
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            if not profile:
                profile = request.env['investor.profile'].sudo().create({
                    'partner_id': current_user.partner_id.id,
                })
            # Tìm address hiện tại hoặc tạo mới
            address = request.env['investor.address'].sudo().search([
                ('investor_id', '=', profile.id)
            ], limit=1)
            address_vals = {
                'street': data['street'],
                'state_id': state_id,
                'district': data['district'],
                'ward': data['ward'],
                'country_id': country_id,
            }
            if not address:
                address_vals['investor_id'] = profile.id
                address_vals['address_type'] = 'current'
                address = request.env['investor.address'].sudo().create(address_vals)
            else:
                address.sudo().write(address_vals)
            return Response(json.dumps({'success': True, 'message': 'Address information updated successfully'}), 
                          content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/data_verification', type='http', auth='user', methods=['GET'], csrf=False)
    def get_verification_data(self, **kwargs):
        """API endpoint để lấy dữ liệu verification của user hiện tại"""
        try:
            current_user = request.env.user
            verification_profiles = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ])

            data = []
            if verification_profiles:
                # Nếu có profile, trả về dữ liệu
                for profile in verification_profiles:
                    data.append({
                        'id': profile.id,
                        'is_verified': getattr(profile, 'is_verified', False), # Assuming a boolean field for verification status
                        'contract_email': profile.partner_id.email, # Assuming email for contract delivery is partner's email
                        'company_address': "Your Company Address Here", # Placeholder, update as needed
                    })
            else:
                # Nếu chưa có profile, trả về thông tin mặc định
                partner = current_user.partner_id
                data.append({
                    'id': None,
                    'is_verified': False,
                    'contract_email': partner.email or current_user.email or '',
                    'company_address': "Your Company Address Here",
                })

            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/api/verification/complete', type='http', auth='user', methods=['POST'], csrf=False)
    def complete_verification_process(self, **kwargs):
        """
        API endpoint to complete the verification process.
        Auto-approves if eKYC is verified, otherwise sets to pending.
        """
        try:
            current_user = request.env.user
            status_info = request.env['status.info'].sudo().search([
                ('partner_id', '=', current_user.partner_id.id)
            ], limit=1)
            
            if not status_info:
                # Create if not exists (should not happen usually)
                status_info = request.env['status.info'].sudo().create({
                    'partner_id': current_user.partner_id.id
                })
            
            update_vals = {'profile_status': 'complete'}
            
            # ONLY auto-approve if eKYC is ALREADY verified through the proper process
            if status_info.ekyc_verified:
                update_vals['account_status'] = 'approved'
                message = 'Hồ sơ đã được phê duyệt tự động nhờ xác thực eKYC.'
            else:
                update_vals['account_status'] = 'pending'
                message = 'Hồ sơ đang chờ duyệt. Vui lòng thực hiện eKYC để được phê duyệt tự động.'
                
            status_info.sudo().write(update_vals)
            
            return Response(json.dumps({
                'success': True,
                'message': message,
                'status': update_vals['account_status']
            }), content_type='application/json')
            
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/save_all_profile_data', type='http', auth='user', methods=['POST'], csrf=False)
    def save_all_profile_data(self, **kwargs):
        """API endpoint to save all collected profile data"""
        try:
            current_user = request.env.user
            all_data = json.loads(request.httprequest.data.decode('utf-8'))
            # --- 1. Personal Profile Data ---
            personal_data = all_data.get('personalProfileData', {})
            required_fields = ['name', 'email', 'phone', 'gender', 'nationality', 'birth_date', 'id_type', 'id_number', 'id_issue_date', 'id_issue_place']
            missing_fields = [field for field in required_fields if not personal_data.get(field)]
            nationality_val = personal_data.get('nationality')
            try:
                nationality_id = int(nationality_val) if nationality_val and str(nationality_val).isdigit() else None
            except Exception:
                nationality_id = None
            if not nationality_id:
                missing_fields.append('nationality')
            if missing_fields:
                return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin cá nhân: {", ".join(set(missing_fields))}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
            profile = request.env['investor.profile'].sudo().search([
                ('user_id', '=', current_user.id)
            ], limit=1)
            if not profile:
                create_dict = {
                    'partner_id': current_user.partner_id.id,
                    'name': personal_data['name'],
                    'gender': personal_data['gender'],
                    'id_type': personal_data['id_type'],
                    'id_number': personal_data['id_number'],
                    'id_issue_place': personal_data['id_issue_place'],
                    'birth_date': personal_data['birth_date'],
                    'id_issue_date': personal_data['id_issue_date'],
                    'email': personal_data['email'],
                    'phone': personal_data['phone'],
                    'nationality': nationality_id,
                }
                profile = request.env['investor.profile'].sudo().create(create_dict)
            personal_update_data = {
                'name': personal_data['name'],
                'email': personal_data['email'],
                'phone': personal_data['phone'],
                'gender': personal_data['gender'],
                'nationality': nationality_id,
                'birth_date': personal_data['birth_date'],
                'id_type': personal_data['id_type'],
                'id_number': personal_data['id_number'],
                'id_issue_date': personal_data['id_issue_date'],
                'id_issue_place': personal_data['id_issue_place'],
            }
            # Xử lý lưu ảnh CCCD và video eKYC (nếu có)
            if 'id_front' in personal_data and personal_data['id_front']:
                try:
                    personal_update_data['id_front'] = base64.b64decode(personal_data['id_front'].split(',')[-1])
                    personal_update_data['id_front_filename'] = 'cccd_front.jpg'
                    print(f"✅ Front CCCD image saved to database ({len(personal_update_data['id_front'])} bytes)")
                except Exception as e:
                    print(f"❌ Error processing front CCCD image: {e}")
            if 'id_back' in personal_data and personal_data['id_back']:
                try:
                    personal_update_data['id_back'] = base64.b64decode(personal_data['id_back'].split(',')[-1])
                    personal_update_data['id_back_filename'] = 'cccd_back.jpg'
                    print(f"✅ Back CCCD image saved to database ({len(personal_update_data['id_back'])} bytes)")
                except Exception as e:
                    print(f"❌ Error processing back CCCD image: {e}")
            # Video eKYC không được lưu vào profile vì field không tồn tại
            # Video chỉ dùng cho quá trình verification
            profile.sudo().write(personal_update_data)
            partner_update = {
                'name': personal_data['name'],
                'email': personal_data['email'],
                'phone': personal_data['phone'],
            }
            if partner_update:
                profile.partner_id.sudo().write(partner_update)
            # --- 2. Bank Account Data ---
            bank_data = all_data.get('bankInfoData', {})
            if bank_data:
                required_fields = ['bank_name', 'bank_account_number', 'account_holder_name', 'bank_branch']
                missing_fields = [field for field in required_fields if not bank_data.get(field)]
                if missing_fields:
                    return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin ngân hàng: {", ".join(set(missing_fields))}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
                bank_account_vals = {
                    'bank_name': bank_data['bank_name'],
                    'account_number': bank_data['bank_account_number'],
                    'account_holder': bank_data['account_holder_name'],
                    'branch': bank_data['bank_branch'],
                    'company_name': bank_data.get('company_name', ''),
                    'company_address': bank_data.get('company_address', ''),
                    'occupation': bank_data.get('occupation', ''),
                    'monthly_income': bank_data.get('monthly_income', 0),
                    'position': bank_data.get('position', ''),
                }
                if profile.bank_account_ids:
                    profile.bank_account_ids[0].sudo().write(bank_account_vals)
                else:
                    bank_account_vals['investor_id'] = profile.id
                    request.env['investor.bank.account'].sudo().create(bank_account_vals)
            # --- 3. Address Information Data ---
            address_data = all_data.get('addressInfoData', {})
            if address_data:
                # Kiểm tra từng trường required, trả về lỗi rõ ràng từng trường
                required_fields = ['street', 'district', 'ward', 'country_id', 'state']
                for field in required_fields:
                    if not address_data.get(field):
                        return Response(json.dumps({'error': f'Thiếu hoặc sai thông tin địa chỉ: {field}. Vui lòng nhập lại.'}), content_type='application/json', status=400)
                state_val = address_data.get('state')
                try:
                    state_id = int(state_val) if state_val and str(state_val).isdigit() else None
                except Exception:
                    state_id = None
                if not state_id or state_id <= 0:
                    return Response(json.dumps({'error': 'Thiếu hoặc sai thông tin địa chỉ: state. Vui lòng nhập lại.'}), content_type='application/json', status=400)
                country_val = address_data.get('country_id')
                try:
                    country_id = int(country_val) if country_val and str(country_val).isdigit() else None
                except Exception:
                    country_id = None
                if not country_id or country_id <= 0:
                    return Response(json.dumps({'error': 'Thiếu hoặc sai thông tin địa chỉ: country_id. Vui lòng nhập lại.'}), content_type='application/json', status=400)
                address_vals = {
                    'street': address_data['street'],
                    'district': address_data['district'],
                    'ward': address_data['ward'],
                    'state_id': state_id,
                    'country_id': country_id,
                }
                if profile.address_ids:
                    profile.address_ids[0].sudo().write(address_vals)
                else:
                    address_vals['investor_id'] = profile.id
                    request.env['investor.address'].sudo().create(address_vals)
            # Sau khi lưu xong toàn bộ, cập nhật trạng thái TK đầu tư và hồ sơ gốc
            status_info = request.env['status.info'].sudo().search([
                ('partner_id', '=', current_user.partner_id.id)
            ], limit=1)
            if status_info:
                status_info.set_approved()
            return Response(json.dumps({'success': True, 'message': 'All profile data saved successfully'}), 
                          content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500) 

    @http.route('/get_states', type='http', auth='user', methods=['GET'], csrf=False)
    def get_states(self, **kwargs):
        country_id = kwargs.get('country_id')
        try:
            domain = []
            if country_id:
                domain.append(('country_id', '=', int(country_id)))
            states = request.env['res.country.state'].sudo().search(domain)
            data = [{'id': s.id, 'name': s.name} for s in states]
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500) 