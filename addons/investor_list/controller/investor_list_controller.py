from odoo import http
from odoo.http import request
import json
import pytz
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access


class InvestorListController(http.Controller):
    @http.route('/investor_list', type='http', auth='user', website=True)
    @require_module_access('investor_list')
    def investor_list_page(self, **kwargs):
        # Tự động đồng bộ portal users vào danh sách (idempotent)
        try:
            request.env['investor.list'].sudo().sync_portal_users()
        except Exception:
            # Không chặn hiển thị trang nếu đồng bộ lỗi
            pass
        
        # Lấy dữ liệu từ model investor.list
        investor_records = request.env['investor.list'].search([])
        investor_data = []
        
        for record in investor_records:
            investor_data.append({
                'id': record.id,
                'open_date': record.open_date.strftime('%Y-%m-%d %H:%M:%S') if record.open_date else '',
                'account_number': record.account_number or '',
                'partner_name': record.partner_name or '',
                'id_number': record.id_number or '',
                'phone': record.phone or '',
                'email': record.email or '',
                'province_city': record.province_city or '',
                'source': record.source or '',
                'bda_user': record.bda_user.name if record.bda_user else '',
                'status': record.status or '',
                'account_status': record.account_status or '',
                'profile_status': record.profile_status or '',
                'status_manual': record.status_manual,
                'partner_name_manual': record.partner_name_manual,
                'phone_manual': record.phone_manual,
                'email_manual': record.email_manual,
                'id_number_manual': record.id_number_manual,
                'province_city_manual': record.province_city_manual
            })
        
        # Tính toán số lượng theo từng trạng thái
        pending_count = len([i for i in investor_data if i['status'] == 'pending'])
        kyc_count = len([i for i in investor_data if i['status'] == 'kyc'])
        vsd_count = len([i for i in investor_data if i['status'] == 'vsd'])
        incomplete_count = len([i for i in investor_data if i['status'] == 'incomplete'])
        
        # Tạo dữ liệu cho template
        all_dashboard_data = {
            'investors': investor_data,
            'total_count': len(investor_data),
            'pending_count': pending_count,
            'kyc_count': kyc_count,
            'vsd_count': vsd_count,
            'incomplete_count': incomplete_count
        }

        return request.render('investor_list.investor_list_page', {
            'all_dashboard_data': json.dumps(all_dashboard_data)
        })

    @http.route('/api/investor_list/<int:investor_id>', type='http', auth='user', methods=['PUT'], csrf=False)
    def update_investor(self, investor_id, **kwargs):
        try:
            # Đọc dữ liệu JSON từ request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return json.dumps({'error': 'Nhà đầu tư không tồn tại'})
            
            # Cập nhật các trường được phép chỉnh sửa
            update_data = {}
            
            # Xử lý trường source
            if 'source' in data:
                update_data['source'] = data['source']
            
            # Xử lý trường bda_user - có thể là ID hoặc tên
            if 'bda_user' in data and data['bda_user']:
                bda_value = data['bda_user']
                if isinstance(bda_value, int):
                    # Nếu là ID
                    update_data['bda_user'] = bda_value
                else:
                    # Nếu là tên, tìm user theo tên
                    user = request.env['res.users'].search([('name', '=', bda_value)], limit=1)
                    if user:
                        update_data['bda_user'] = user.id
                    else:
                        # Nếu không tìm thấy, tạo mới hoặc để trống
                        update_data['bda_user'] = False
            elif 'bda_user' in data and not data['bda_user']:
                # Nếu bda_user rỗng, set về False
                update_data['bda_user'] = False
            
            # Xử lý các trường thông tin cá nhân
            if 'partner_name' in data:
                update_data['partner_name'] = data['partner_name']
            if 'phone' in data:
                update_data['phone'] = data['phone']
            if 'email' in data:
                update_data['email'] = data['email']
            if 'id_number' in data:
                update_data['id_number'] = data['id_number']
            if 'province_city' in data:
                update_data['province_city'] = data['province_city']
            
            # Xử lý các trường khác
            if 'account_status' in data:
                update_data['account_status'] = data['account_status']
            if 'profile_status' in data:
                update_data['profile_status'] = data['profile_status']
            if 'status' in data:
                update_data['status'] = data['status']
            
            # Ghi dữ liệu vào database
            investor.write(update_data)
            
            # Refresh record để lấy dữ liệu mới nhất
            investor.refresh()
            
            # Trả về dữ liệu đã cập nhật
            response_data = {
                'id': investor.id,
                'open_date': investor.open_date.strftime('%Y-%m-%d %H:%M:%S') if investor.open_date else '',
                'account_number': investor.account_number or '',
                'partner_name': investor.partner_name or '',
                'id_number': investor.id_number or '',
                'phone': investor.phone or '',
                'email': investor.email or '',
                'province_city': investor.province_city or '',
                'source': investor.source or '',
                'bda_user': investor.bda_user.name if investor.bda_user else '',
                'status': investor.status or '',
                'account_status': investor.account_status or '',
                'profile_status': investor.profile_status or '',
                'status_manual': investor.status_manual,
                'partner_name_manual': investor.partner_name_manual,
                'phone_manual': investor.phone_manual,
                'email_manual': investor.email_manual,
                'id_number_manual': investor.id_number_manual,
                'province_city_manual': investor.province_city_manual
            }
            
            return json.dumps(response_data)
        except Exception as e:
            return json.dumps({'error': str(e)})


    @http.route('/api/users', type='http', auth='user', methods=['GET'], csrf=False)
    def get_users(self, **kwargs):
        try:
            # Lấy danh sách users active
            users = request.env['res.users'].search([('active', '=', True)])
            users_data = []
            
            for user in users:
                users_data.append({
                    'id': user.id,
                    'name': user.name
                })
            
            return json.dumps(users_data)
        except Exception as e:
            return json.dumps({'error': str(e)})

    @http.route('/api/investor_list/<int:investor_id>/reset', type='http', auth='user', methods=['POST'], csrf=False)
    def reset_investor_fields(self, investor_id, **kwargs):
        try:
            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return json.dumps({'error': 'Nhà đầu tư không tồn tại'})
            
            # Reset tất cả trường về tự động
            investor.reset_manual_fields()
            
            # Trả về dữ liệu đã cập nhật
            response_data = {
                'id': investor.id,
                'open_date': investor.open_date.strftime('%Y-%m-%d %H:%M:%S') if investor.open_date else '',
                'account_number': investor.account_number or '',
                'partner_name': investor.partner_name or '',
                'id_number': investor.id_number or '',
                'phone': investor.phone or '',
                'email': investor.email or '',
                'province_city': investor.province_city or '',
                'source': investor.source or '',
                'bda_user': investor.bda_user.name if investor.bda_user else '',
                'status': investor.status or '',
                'account_status': investor.account_status or '',
                'profile_status': investor.profile_status or '',
                'status_manual': investor.status_manual,
                'partner_name_manual': investor.partner_name_manual,
                'phone_manual': investor.phone_manual,
                'email_manual': investor.email_manual,
                'id_number_manual': investor.id_number_manual,
                'province_city_manual': investor.province_city_manual
            }
            
            return json.dumps(response_data)
        except Exception as e:
            return json.dumps({'error': str(e)})