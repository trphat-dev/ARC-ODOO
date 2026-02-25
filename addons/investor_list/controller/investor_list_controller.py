from odoo import http
from odoo.http import request
import json
import pytz
from markupsafe import Markup
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
        
        # Tính toán số lượng theo từng trạng thái mới
        draft_count = len([i for i in investor_data if i['status'] == 'draft'])
        pending_count = len([i for i in investor_data if i['status'] == 'pending'])
        active_count = len([i for i in investor_data if i['status'] == 'active'])
        vsd_count = len([i for i in investor_data if i['status'] == 'vsd'])
        rejected_count = len([i for i in investor_data if i['status'] == 'rejected'])
        
        # Tạo dữ liệu cho template
        all_dashboard_data = {
            'investors': investor_data,
            'total_count': len(investor_data),
            'draft_count': draft_count,
            'pending_count': pending_count,
            'active_count': active_count,
            'vsd_count': vsd_count,
            'rejected_count': rejected_count
        }

        return request.render('investor_list.investor_list_page', {
            'all_dashboard_data': Markup(json.dumps(all_dashboard_data))
        })

    @http.route('/api/investor_list/<int:investor_id>', type='http', auth='user', methods=['PUT'], csrf=False)
    def update_investor(self, investor_id, **kwargs):
        """Update investor details with manual override tracking"""
        try:
            # Đọc dữ liệu JSON từ request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return json.dumps({'error': 'Nhà đầu tư không tồn tại'})
            
            # Cập nhật các trường được phép chỉnh sửa
            vals = {}
            
            # Fields that can be manually edited
            editable_fields = ['partner_name', 'phone', 'email', 'id_number', 'province_city']
            
            for field in editable_fields:
                if field in data:
                    vals[field] = data[field]
                    vals[f'{field}_manual'] = True
            
            # Status fields
            if 'account_status' in data:
                vals['account_status'] = data['account_status']
            if 'profile_status' in data:
                vals['profile_status'] = data['profile_status']
            if 'status' in data:
                vals['status'] = data['status']
                vals['status_manual'] = True
            
            if vals:
                investor.write(vals)
            
            return json.dumps({'success': True})
            
        except Exception as e:
            return json.dumps({'error': str(e)})

    @http.route('/api/investor_list/<int:investor_id>/approve', type='json', auth='user', methods=['POST'])
    def approve_investor(self, investor_id):
        """Manually approve an investor"""
        try:
            # Check permission (simple check for now, can be enhanced)
            if not request.env.user.has_group('base.group_user'):
                 return {'error': 'Permission denied'}

            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return {'error': 'Investor not found'}
            
            # Update status manual flag
            investor.write({'status_manual': True, 'account_status': 'approved'})
            return {'success': True, 'status': 'approved', 'status_display': 'Approved'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/investor_list/<int:investor_id>/reject', type='json', auth='user', methods=['POST'])
    def reject_investor(self, investor_id):
        """Manually reject an investor"""
        try:
            if not request.env.user.has_group('base.group_user'):
                 return {'error': 'Permission denied'}

            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return {'error': 'Investor not found'}
            
            investor.write({'status_manual': True, 'account_status': 'rejected'})
            return {'success': True, 'status': 'rejected', 'status_display': 'Rejected'}
        except Exception as e:
            return {'error': str(e)}

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

    @http.route('/api/investor_list/<int:investor_id>/reset', type='json', auth='user', methods=['POST'])
    def reset_investor_fields(self, investor_id, **kwargs):
        try:
            investor = request.env['investor.list'].browse(investor_id)
            if not investor.exists():
                return {'error': 'Nhà đầu tư không tồn tại'}
            
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
                'province_city': investor.province_city or '',
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