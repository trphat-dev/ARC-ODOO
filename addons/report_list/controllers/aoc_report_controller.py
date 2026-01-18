from odoo import http
from odoo.http import request
import json
from datetime import datetime
import openpyxl
import csv
import io
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access

class AOCReportController(http.Controller):
    @http.route('/aoc_report', type='http', auth='user', website=True)
    @require_module_access('report_list')
    def aoc_report_page(self, **kwargs):
        """Render the AOC Report page."""
        return request.render('report_list.aoc_report_page_template', {})

    @http.route('/aoc_report/get_data', type='json', auth='user', methods=['POST'])
    def get_aoc_report_data(self, filters, page, limit, search_values=None, **kws):
        """API endpoint to fetch paginated report data based on filters."""
        try:
            # Lấy dữ liệu từ investor.list model
            domain = []
            
            # Filter theo ngày
            if filters.get('dateFrom'):
                domain.append(('open_date', '>=', filters['dateFrom']))
            if filters.get('dateTo'):
                domain.append(('open_date', '<=', filters['dateTo']))
            
            # Filter theo trạng thái
            if filters.get('status'):
                if filters['status'] == 'active':
                    # Tài khoản hoạt động - status KYC hoặc VSD
                    domain.append(('status', 'in', ['kyc', 'vsd']))
                elif filters['status'] == 'inactive':
                    # Tài khoản đã đóng - status pending hoặc incomplete
                    domain.append(('status', 'in', ['pending', 'incomplete']))
            
            # Search values
            if search_values:
                if search_values.get('account_number'):
                    domain.append(('account_number', 'ilike', search_values['account_number']))
                if search_values.get('customer_name'):
                    domain.append(('partner_name', 'ilike', search_values['customer_name']))
                if search_values.get('account_manager'):
                    domain.append(('bda_user.name', 'ilike', search_values['account_manager']))
            
            # Lấy records với pagination
            offset = (int(page) - 1) * int(limit)
            records = request.env['investor.list'].search(domain, limit=int(limit), offset=offset)
            total_records = request.env['investor.list'].search_count(domain)
            
            # Chuẩn hóa dữ liệu
            data = []
            for i, record in enumerate(records):
                # Lấy thông tin từ partner
                partner = record.partner_id
                
                # Lấy thông tin từ investor.profile nếu có
                investor_profile = None
                if partner:
                    investor_profile = request.env['investor.profile'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin từ status.info
                status_info = None
                if partner:
                    status_info = request.env['status.info'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin địa chỉ
                permanent_address = ''
                contact_address = ''
                if partner:
                    address = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'permanent')
                    ], limit=1)
                    if address:
                        permanent_address = f"{address.street}, {address.ward}, {address.district}, {address.state_id.name if address.state_id else ''}"
                    
                    # Lấy địa chỉ liên hệ
                    contact_address_obj = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'current')
                    ], limit=1)
                    if contact_address_obj:
                        contact_address = f"{contact_address_obj.street}, {contact_address_obj.ward}, {contact_address_obj.district}, {contact_address_obj.state_id.name if contact_address_obj.state_id else ''}"
                
                # Xác định trạng thái tài khoản
                account_status = 'active' if record.status in ['kyc', 'vsd'] else 'inactive'
                
                # Lấy ngày đóng tài khoản (nếu có)
                close_date = ''
                if account_status == 'inactive' and record.write_date:
                    close_date = record.write_date.strftime('%d/%m/%Y')
                
                # Xác định loại khách hàng
                customer_type = 'CN' if record.status in ['kyc', 'vsd'] else 'TC'
                
                # Lấy account manager từ status_info
                account_manager = ''
                if status_info and status_info.rm_id:
                    account_manager = status_info.rm_id.name
                elif status_info and status_info.bda_id:
                    account_manager = status_info.bda_id.name
                elif record.bda_user:
                    account_manager = record.bda_user.name
                
                data.append({
                    'id': record.id,
                    'stt': offset + i + 1,
                    'account_number': record.account_number or '',
                    'trading_account': '',  # Không có trong investor.list
                    'customer_name': record.partner_name or '',
                    'id_number': record.id_number or '',
                    'id_issue_date': investor_profile.id_issue_date.strftime('%d/%m/%Y') if investor_profile and investor_profile.id_issue_date else '',
                    'id_issue_place': investor_profile.id_issue_place if investor_profile else '',
                    'permanent_address': permanent_address,
                    'contact_address': contact_address,
                    'phone_number': record.phone or '',
                    'email': record.email or '',
                    'open_date': record.open_date.strftime('%d/%m/%Y') if record.open_date else '',
                    'close_date': close_date,
                    'status': account_status,
                    'customer_type': customer_type,
                    'nationality_type': investor_profile.nationality.name if investor_profile and investor_profile.nationality else '',
                    'account_manager': account_manager,
                    'unit': record.source or ''
                })
            
            return {
                'data': data,
                'total': total_records,
                'page': int(page),
                'limit': int(limit)
            }
            
        except Exception as e:
            print(f"Error in get_aoc_report_data: {e}")
            return {
                'data': [],
                'total': 0,
                'page': int(page),
                'limit': int(limit),
                'error': str(e)
            }
    
    @http.route('/aoc_report/export_pdf', type='http', auth='user', website=True, csrf=False)
    def export_pdf(self, **kw):
        """Export report data as a PDF file."""
        try:
            # Lấy dữ liệu thật từ investor.list
            domain = []
            
            # Filter theo ngày
            if kw.get('dateFrom'):
                domain.append(('open_date', '>=', kw['dateFrom']))
            if kw.get('dateTo'):
                domain.append(('open_date', '<=', kw['dateTo']))
            
            # Filter theo trạng thái
            if kw.get('status'):
                if kw['status'] == 'active':
                    domain.append(('status', 'in', ['kyc', 'vsd']))
                elif kw['status'] == 'inactive':
                    domain.append(('status', 'in', ['pending', 'incomplete']))
            
            # Search values
            if kw.get('account_number'):
                domain.append(('account_number', 'ilike', kw['account_number']))
            if kw.get('customer_name'):
                domain.append(('partner_name', 'ilike', kw['customer_name']))
            if kw.get('account_manager'):
                domain.append(('bda_user.name', 'ilike', kw['account_manager']))
            
            records = request.env['investor.list'].search(domain)
            
            # Chuẩn hóa dữ liệu cho export
            export_data = []
            for i, record in enumerate(records):
                # Lấy thông tin từ partner
                partner = record.partner_id
                
                # Lấy thông tin từ investor.profile nếu có
                investor_profile = None
                if partner:
                    investor_profile = request.env['investor.profile'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin từ status.info
                status_info = None
                if partner:
                    status_info = request.env['status.info'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin địa chỉ
                permanent_address = ''
                contact_address = ''
                if partner:
                    address = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'permanent')
                    ], limit=1)
                    if address:
                        permanent_address = f"{address.street}, {address.ward}, {address.district}, {address.state_id.name if address.state_id else ''}"
                    
                    # Lấy địa chỉ liên hệ
                    contact_address_obj = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'current')
                    ], limit=1)
                    if contact_address_obj:
                        contact_address = f"{contact_address_obj.street}, {contact_address_obj.ward}, {contact_address_obj.district}, {contact_address_obj.state_id.name if contact_address_obj.state_id else ''}"
                
                # Xác định trạng thái tài khoản
                account_status = 'active' if record.status in ['kyc', 'vsd'] else 'inactive'
                
                # Lấy ngày đóng tài khoản (nếu có)
                close_date = ''
                if account_status == 'inactive' and record.write_date:
                    close_date = record.write_date.strftime('%d/%m/%Y')
                
                # Xác định loại khách hàng
                customer_type = 'CN' if record.status in ['kyc', 'vsd'] else 'TC'
                
                # Lấy account manager từ status_info
                account_manager = ''
                if status_info and status_info.rm_id:
                    account_manager = status_info.rm_id.name
                elif status_info and status_info.bda_id:
                    account_manager = status_info.bda_id.name
                elif record.bda_user:
                    account_manager = record.bda_user.name
                
                export_data.append({
                    'stt': i + 1,
                    'account_number': record.account_number or '',
                    'trading_account': '',
                    'customer_name': record.partner_name or '',
                    'id_number': record.id_number or '',
                    'id_issue_date': investor_profile.id_issue_date.strftime('%d/%m/%Y') if investor_profile and investor_profile.id_issue_date else '',
                    'id_issue_place': investor_profile.id_issue_place if investor_profile else '',
                    'permanent_address': permanent_address,
                    'contact_address': contact_address,
                    'phone_number': record.phone or '',
                    'email': record.email or '',
                    'open_date': record.open_date.strftime('%d/%m/%Y') if record.open_date else '',
                    'close_date': close_date,
                    'status': account_status,
                    'customer_type': customer_type,
                    'nationality_type': investor_profile.nationality.name if investor_profile and investor_profile.nationality else '',
                    'account_manager': account_manager,
                    'unit': record.source or ''
                })
            
            records = export_data
            
        except Exception as e:
            print(f"Error in export_pdf: {e}")
            records = []
        
        report_date_range = "Từ ngày ... đến ngày ..."
        date_from = kw.get('date_from')
        date_to = kw.get('date_to')
        if date_from and date_to:
            date_from_str = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
            date_to_str = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
            report_date_range = f"Từ ngày {date_from_str} đến ngày {date_to_str}"

        return request.render('report_list.aoc_report_pdf_template', {
            'records': records,
            'report_date_range': report_date_range,
            'total_count': len(records)
        })

    @http.route('/aoc_report/export_xlsx', type='http', auth='user', website=True, csrf=False)
    def export_xlsx(self, **kw):
        """Export report data as an XLSX file."""
        if not openpyxl:
            return request.make_response(
                "Thư viện 'openpyxl' chưa được cài đặt. Vui lòng cài đặt bằng lệnh 'pip install openpyxl'.",
                headers=[('Content-Type', 'text/plain')]
            )

        try:
            # Lấy dữ liệu thật từ investor.list
            domain = []
            
            # Filter theo ngày
            if kw.get('dateFrom'):
                domain.append(('open_date', '>=', kw['dateFrom']))
            if kw.get('dateTo'):
                domain.append(('open_date', '<=', kw['dateTo']))
            
            # Filter theo trạng thái
            if kw.get('status'):
                if kw['status'] == 'active':
                    domain.append(('status', 'in', ['kyc', 'vsd']))
                elif kw['status'] == 'inactive':
                    domain.append(('status', 'in', ['pending', 'incomplete']))
            
            # Search values
            if kw.get('account_number'):
                domain.append(('account_number', 'ilike', kw['account_number']))
            if kw.get('customer_name'):
                domain.append(('partner_name', 'ilike', kw['customer_name']))
            if kw.get('account_manager'):
                domain.append(('bda_user.name', 'ilike', kw['account_manager']))
            
            records = request.env['investor.list'].search(domain)
            
            # Chuẩn hóa dữ liệu cho export
            export_data = []
            for i, record in enumerate(records):
                # Lấy thông tin từ partner
                partner = record.partner_id
                
                # Lấy thông tin từ investor.profile nếu có
                investor_profile = None
                if partner:
                    investor_profile = request.env['investor.profile'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin từ status.info
                status_info = None
                if partner:
                    status_info = request.env['status.info'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin địa chỉ
                permanent_address = ''
                contact_address = ''
                if partner:
                    address = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'permanent')
                    ], limit=1)
                    if address:
                        permanent_address = f"{address.street}, {address.ward}, {address.district}, {address.state_id.name if address.state_id else ''}"
                    
                    # Lấy địa chỉ liên hệ
                    contact_address_obj = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'current')
                    ], limit=1)
                    if contact_address_obj:
                        contact_address = f"{contact_address_obj.street}, {contact_address_obj.ward}, {contact_address_obj.district}, {contact_address_obj.state_id.name if contact_address_obj.state_id else ''}"
                
                # Xác định trạng thái tài khoản
                account_status = 'active' if record.status in ['kyc', 'vsd'] else 'inactive'
                
                # Lấy ngày đóng tài khoản (nếu có)
                close_date = ''
                if account_status == 'inactive' and record.write_date:
                    close_date = record.write_date.strftime('%d/%m/%Y')
                
                # Xác định loại khách hàng
                customer_type = 'CN' if record.status in ['kyc', 'vsd'] else 'TC'
                
                # Lấy account manager từ status_info
                account_manager = ''
                if status_info and status_info.rm_id:
                    account_manager = status_info.rm_id.name
                elif status_info and status_info.bda_id:
                    account_manager = status_info.bda_id.name
                elif record.bda_user:
                    account_manager = record.bda_user.name
                
                export_data.append({
                    'stt': i + 1,
                    'account_number': record.account_number or '',
                    'trading_account': '',
                    'customer_name': record.partner_name or '',
                    'id_number': record.id_number or '',
                    'id_issue_date': investor_profile.id_issue_date.strftime('%d/%m/%Y') if investor_profile and investor_profile.id_issue_date else '',
                    'id_issue_place': investor_profile.id_issue_place if investor_profile else '',
                    'permanent_address': permanent_address,
                    'contact_address': contact_address,
                    'phone_number': record.phone or '',
                    'email': record.email or '',
                    'open_date': record.open_date.strftime('%d/%m/%Y') if record.open_date else '',
                    'close_date': close_date,
                    'status': account_status,
                    'customer_type': customer_type,
                    'nationality_type': investor_profile.nationality.name if investor_profile and investor_profile.nationality else '',
                    'account_manager': account_manager,
                    'unit': record.source or ''
                })
            
            records = export_data
            
        except Exception as e:
            print(f"Error in export_xlsx: {e}")
            records = []

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "AOC Report"

        # Headers
        headers = [
            'STT', 'Số TK', 'Số TK GDCK', 'Khách hàng', 'ĐKSH', 'Ngày cấp', 'Nơi cấp',
            'Địa chỉ thường trú', 'Địa chỉ liên hệ', 'Số điện thoại', 'Email', 
            'Ngày mở TK', 'Ngày đóng TK', 'Trạng thái', 'Loại khách hàng',
            'Loại quốc tịch', 'NVCS', 'Đơn vị'
        ]
        
        for col, header in enumerate(headers, 1):
            sheet.cell(row=1, column=col, value=header)

        # Body
        for rec in records:
            row = [
                rec.get('stt', ''), 
                rec.get('account_number', ''), 
                rec.get('trading_account', ''), 
                rec.get('customer_name', ''), 
                rec.get('id_number', ''), 
                rec.get('id_issue_date', ''), 
                rec.get('id_issue_place', ''), 
                rec.get('permanent_address', ''), 
                rec.get('contact_address', ''), 
                rec.get('phone_number', ''), 
                rec.get('email', ''), 
                rec.get('open_date', ''), 
                rec.get('close_date', ''), 
                rec.get('status', ''), 
                rec.get('customer_type', ''), 
                rec.get('nationality_type', ''), 
                rec.get('account_manager', ''), 
                rec.get('unit', '')
            ]
            sheet.append(row)

        # Save to BytesIO
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = request.make_response(
            output.getvalue(),
            headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="aoc_report.xlsx"')
            ]
        )
        return response

    @http.route('/aoc_report/export_csv', type='http', auth='user', website=True, csrf=False)
    def export_csv(self, **kw):
        """Export report data as a CSV file."""
        try:
            # Lấy dữ liệu thật từ investor.list
            domain = []
            
            # Filter theo ngày
            if kw.get('dateFrom'):
                domain.append(('open_date', '>=', kw['dateFrom']))
            if kw.get('dateTo'):
                domain.append(('open_date', '<=', kw['dateTo']))
            
            # Filter theo trạng thái
            if kw.get('status'):
                if kw['status'] == 'active':
                    domain.append(('status', 'in', ['kyc', 'vsd']))
                elif kw['status'] == 'inactive':
                    domain.append(('status', 'in', ['pending', 'incomplete']))
            
            # Search values
            if kw.get('account_number'):
                domain.append(('account_number', 'ilike', kw['account_number']))
            if kw.get('customer_name'):
                domain.append(('partner_name', 'ilike', kw['customer_name']))
            if kw.get('account_manager'):
                domain.append(('bda_user.name', 'ilike', kw['account_manager']))
            
            records = request.env['investor.list'].search(domain)
            
            # Chuẩn hóa dữ liệu cho export
            export_data = []
            for i, record in enumerate(records):
                # Lấy thông tin từ partner
                partner = record.partner_id
                
                # Lấy thông tin từ investor.profile nếu có
                investor_profile = None
                if partner:
                    investor_profile = request.env['investor.profile'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin từ status.info
                status_info = None
                if partner:
                    status_info = request.env['status.info'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                
                # Lấy thông tin địa chỉ
                permanent_address = ''
                contact_address = ''
                if partner:
                    address = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'permanent')
                    ], limit=1)
                    if address:
                        permanent_address = f"{address.street}, {address.ward}, {address.district}, {address.state_id.name if address.state_id else ''}"
                    
                    # Lấy địa chỉ liên hệ
                    contact_address_obj = request.env['investor.address'].search([
                        ('partner_id', '=', partner.id),
                        ('address_type', '=', 'current')
                    ], limit=1)
                    if contact_address_obj:
                        contact_address = f"{contact_address_obj.street}, {contact_address_obj.ward}, {contact_address_obj.district}, {contact_address_obj.state_id.name if contact_address_obj.state_id else ''}"
                
                # Xác định trạng thái tài khoản
                account_status = 'active' if record.status in ['kyc', 'vsd'] else 'inactive'
                
                # Lấy ngày đóng tài khoản (nếu có)
                close_date = ''
                if account_status == 'inactive' and record.write_date:
                    close_date = record.write_date.strftime('%d/%m/%Y')
                
                # Xác định loại khách hàng
                customer_type = 'CN' if record.status in ['kyc', 'vsd'] else 'TC'
                
                # Lấy account manager từ status_info
                account_manager = ''
                if status_info and status_info.rm_id:
                    account_manager = status_info.rm_id.name
                elif status_info and status_info.bda_id:
                    account_manager = status_info.bda_id.name
                elif record.bda_user:
                    account_manager = record.bda_user.name
                
                export_data.append({
                    'stt': i + 1,
                    'account_number': record.account_number or '',
                    'trading_account': '',
                    'customer_name': record.partner_name or '',
                    'id_number': record.id_number or '',
                    'id_issue_date': investor_profile.id_issue_date.strftime('%d/%m/%Y') if investor_profile and investor_profile.id_issue_date else '',
                    'id_issue_place': investor_profile.id_issue_place if investor_profile else '',
                    'permanent_address': permanent_address,
                    'contact_address': contact_address,
                    'phone_number': record.phone or '',
                    'email': record.email or '',
                    'open_date': record.open_date.strftime('%d/%m/%Y') if record.open_date else '',
                    'close_date': close_date,
                    'status': account_status,
                    'customer_type': customer_type,
                    'nationality_type': investor_profile.nationality.name if investor_profile and investor_profile.nationality else '',
                    'account_manager': account_manager,
                    'unit': record.source or ''
                })
            
            records = export_data
            
        except Exception as e:
            print(f"Error in export_csv: {e}")
            records = []

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'STT', 'Số TK', 'Số TK GDCK', 'Khách hàng', 'ĐKSH', 'Ngày cấp', 'Nơi cấp',
            'Địa chỉ thường trú', 'Địa chỉ liên hệ', 'Số điện thoại', 'Email',
            'Ngày mở TK', 'Ngày đóng TK', 'Trạng thái', 'Loại khách hàng',
            'Loại quốc tịch', 'NVCS', 'Đơn vị'
        ]
        writer.writerow(headers)
        
        # Data rows
        for rec in records:
            row = [
                rec.get('stt', ''), 
                rec.get('account_number', ''), 
                rec.get('trading_account', ''), 
                rec.get('customer_name', ''), 
                rec.get('id_number', ''), 
                rec.get('id_issue_date', ''), 
                rec.get('id_issue_place', ''), 
                rec.get('permanent_address', ''), 
                rec.get('contact_address', ''), 
                rec.get('phone_number', ''), 
                rec.get('email', ''), 
                rec.get('open_date', ''), 
                rec.get('close_date', ''), 
                rec.get('status', ''), 
                rec.get('customer_type', ''), 
                rec.get('nationality_type', ''), 
                rec.get('account_manager', ''), 
                rec.get('unit', '')
            ]
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        response = request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', 'attachment; filename="aoc_report.csv"')
            ]
        )
        return response